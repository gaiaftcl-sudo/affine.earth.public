/**
 * Affine.Earth OpenUSD — solar terminator + weather overlay (UUM8D band LOD).
 *
 * Solar: computed from UTC time + lat/lon (always live math — not a feed).
 * Weather radar/METAR: membrane may report BLOCKED_NOAA_* — render honest status
 * + Affine-branded synoptic stylization. Never fake radar loops as live NOAA.
 */
(function (global) {
  "use strict";

  var FEED_STATUS = {
    noaa: "UNKNOWN",
    note: "",
    checkedAt: 0,
  };

  /** Live METAR from Swift uum8d-zoom weather JSON (not stylized placeholder). */
  var METAR_LIVE = {
    icao: "",
    raw: "",
    status: "",
    source: "",
    shearRisk: "",
    windDirDeg: null,
    windKt: null,
    goesStatus: "",
  };

  function parseMetarWind(raw) {
    var m = /\b(\d{3}|VRB)(\d{2,3})(G\d{2,3})?KT\b/.exec(raw || "");
    if (!m) return { windDirDeg: null, windKt: null };
    return {
      windDirDeg: m[1] === "VRB" ? null : parseInt(m[1], 10),
      windKt: parseInt(m[2], 10),
    };
  }

  /** Stamp METAR from Swift zoom packet; GOES may still be FOLLOW_ON. */
  function setMetarFromPacket(wx, goesHint) {
    wx = wx || {};
    var wind = parseMetarWind(wx.raw || "");
    METAR_LIVE.icao = wx.icao || "";
    METAR_LIVE.raw = wx.raw || "";
    METAR_LIVE.status = wx.status || "";
    METAR_LIVE.source = wx.source || "";
    METAR_LIVE.shearRisk = wx.shear_risk || wx.shearRisk || "";
    METAR_LIVE.windDirDeg = wind.windDirDeg;
    METAR_LIVE.windKt = wind.windKt;
    if (goesHint) METAR_LIVE.goesStatus = String(goesHint);
    if (METAR_LIVE.status) {
      // Prefer live METAR status for HUD; keep GOES honesty separate.
      FEED_STATUS.noaa = METAR_LIVE.status;
      FEED_STATUS.note = "swift_uum8d_zoom.weather";
      FEED_STATUS.checkedAt = Date.now();
    }
    return METAR_LIVE;
  }

  function metarLive() {
    return METAR_LIVE;
  }

  /** Approximate solar elevation (deg) + terminator longitude for UTC date. */
  function solarState(date, latDeg, lonDeg) {
    var d = date instanceof Date ? date : new Date();
    var start = Date.UTC(d.getUTCFullYear(), 0, 0);
    var dayOfYear = Math.floor((d.getTime() - start) / 86400000);
    var hourUTC = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
    // Declination (Cooper approx)
    var decl = 23.45 * Math.sin(((360 / 365) * (dayOfYear - 81) * Math.PI) / 180);
    // Equation of time skipped — sufficient for terminator cue
    var lat = (latDeg * Math.PI) / 180;
    var declR = (decl * Math.PI) / 180;
    var lstHour = hourUTC + lonDeg / 15;
    var ha = ((lstHour - 12) * 15 * Math.PI) / 180;
    var sinEl =
      Math.sin(lat) * Math.sin(declR) + Math.cos(lat) * Math.cos(declR) * Math.cos(ha);
    var elev = (Math.asin(Math.max(-1, Math.min(1, sinEl))) * 180) / Math.PI;
    // Subsolar longitude ≈ 15° * (12 - hourUTC)
    var subsolarLon = 15 * (12 - hourUTC);
    while (subsolarLon > 180) subsolarLon -= 360;
    while (subsolarLon < -180) subsolarLon += 360;
    var subsolarLat = decl;
    return {
      elevationDeg: elev,
      declinationDeg: decl,
      subsolarLat: subsolarLat,
      subsolarLon: subsolarLon,
      hourUTC: hourUTC,
      dayOfYear: dayOfYear,
      isDay: elev > 0,
      twilight: elev > -6 && elev <= 0,
    };
  }

  /**
   * Probe membrane for NOAA feed status (economics-config live_feeds).
   * Falls back to BLOCKED_FOLLOW_ON if unreachable.
   */
  async function refreshFeedStatus() {
    var apex =
      (global.UUM8DShell && global.UUM8DShell.apexBase && global.UUM8DShell.apexBase()) ||
      "https://affine.earth";
    try {
      var r = await fetch(apex + "/language-invariant/economics-config", {
        credentials: "omit",
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      var body = await r.json();
      var feeds = body.live_feeds || {};
      var goes = feeds.noaa_goes_r || feeds.goes_r || "";
      METAR_LIVE.goesStatus = goes || METAR_LIVE.goesStatus || "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH";
      // Do not overwrite CALORIE_METAR with GOES follow-on — radar lane is separate.
      if (!METAR_LIVE.status || !/^CALORIE/i.test(METAR_LIVE.status)) {
        FEED_STATUS.noaa =
          feeds.noaa_weather || goes || "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH";
      }
      FEED_STATUS.note = "membrane live_feeds + metar lane";
      FEED_STATUS.checkedAt = Date.now();
      FEED_STATUS.raw = feeds;
      FEED_STATUS.goes = METAR_LIVE.goesStatus;
    } catch (e) {
      if (!METAR_LIVE.status) {
        FEED_STATUS.noaa = "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH";
      }
      FEED_STATUS.note = String(e).slice(0, 80);
      FEED_STATUS.checkedAt = Date.now();
      METAR_LIVE.goesStatus = METAR_LIVE.goesStatus || "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH";
    }
    return FEED_STATUS;
  }

  function feedStatus() {
    return FEED_STATUS;
  }

  function bandWeatherLod(bandId) {
    var id = (bandId || "METRO").toUpperCase();
    if (id === "HEMISPHERE")
      return {
        showTerminator: true,
        showSynoptic: true,
        showLocalMetar: false,
        showWindBarb: false,
        cloudAlpha: 0.35,
        nightAlpha: 0.45,
        precipBlobs: 5,
      };
    if (id === "REGIONAL")
      return {
        showTerminator: true,
        showSynoptic: true,
        showLocalMetar: false,
        showWindBarb: false,
        cloudAlpha: 0.4,
        nightAlpha: 0.32,
        precipBlobs: 7,
      };
    if (id === "METRO")
      return {
        showTerminator: false,
        showSynoptic: true,
        showLocalMetar: true,
        showWindBarb: true,
        cloudAlpha: 0.28,
        nightAlpha: 0.18,
        precipBlobs: 4,
      };
    // AIRPORT_WALK
    return {
      showTerminator: false,
      showSynoptic: false,
      showLocalMetar: true,
      showWindBarb: true,
      cloudAlpha: 0.15,
      nightAlpha: 0.08,
      precipBlobs: 2,
    };
  }

  /**
   * Draw solar + weather overlay onto canvas (Affine palette).
   * Synoptic clouds are stylized placeholders labeled via status — not NOAA radar.
   */
  function paintOverlay(g, W, H, opts) {
    opts = opts || {};
    var centerLat = opts.centerLat;
    var centerLon = opts.centerLon;
    var spanDeg = opts.spanDeg;
    var bandId = opts.bandId || "METRO";
    var lod = bandWeatherLod(bandId);
    var solar = solarState(opts.date || new Date(), centerLat, centerLon);
    var status = METAR_LIVE.status || FEED_STATUS.noaa || "UNKNOWN";
    var goes = METAR_LIVE.goesStatus || FEED_STATUS.goes || "";
    var blocked = /BLOCKED|FOLLOW_ON|REFUSED|UNKNOWN/i.test(status) && !METAR_LIVE.raw;
    var radarFollowOn = /FOLLOW_ON|BLOCKED|GOES/i.test(goes || status);

    function project(lat, lon) {
      var x = ((lon - (centerLon - spanDeg / 2)) / spanDeg) * W;
      var y = ((centerLat + spanDeg / 2 - lat) / spanDeg) * H;
      return { x: x, y: y };
    }

    g.clearRect(0, 0, W, H);

    // Night side / terminator (computed solar — always available)
    // Fast path: night hemisphere is ~90° from subsolar longitude (no per-pixel scans).
    if (lod.showTerminator || lod.nightAlpha > 0.05) {
      var nightAlpha = lod.nightAlpha * (solar.isDay ? 0.55 : 1);
      var termA = solar.subsolarLon - 90;
      var termB = solar.subsolarLon + 90;
      function normLon(L) {
        while (L > 180) L -= 360;
        while (L < -180) L += 360;
        return L;
      }
      termA = normLon(termA);
      termB = normLon(termB);
      // Shade columns west of morning terminator (approx night)
      for (var xi = 0; xi < W; xi += 4) {
        var lon = centerLon - spanDeg / 2 + (xi / W) * spanDeg;
        var dSub = Math.abs(normLon(lon - solar.subsolarLon));
        var a = 0;
        if (dSub > 95) a = nightAlpha;
        else if (dSub > 85) a = nightAlpha * 0.55;
        else if (dSub > 75) a = nightAlpha * 0.18;
        if (a <= 0.01) continue;
        g.fillStyle = "rgba(4, 10, 22," + a + ")";
        g.fillRect(xi, 0, 4, H);
      }
      if (lod.showTerminator) {
        g.strokeStyle = "rgba(245, 197, 24, 0.55)";
        g.lineWidth = 1.5;
        g.beginPath();
        var first = true;
        for (var yi = 0; yi <= H; yi += 16) {
          var lat = centerLat + spanDeg / 2 - (yi / H) * spanDeg;
          // Approximate terminator longitude for this latitude (great-circle cue)
          var bestLon = normLon(solar.subsolarLon + 90);
          var p = project(lat, bestLon);
          if (first) {
            g.moveTo(p.x, p.y);
            first = false;
          } else g.lineTo(p.x, p.y);
        }
        g.stroke();
        // Second limb
        g.beginPath();
        first = true;
        for (yi = 0; yi <= H; yi += 16) {
          lat = centerLat + spanDeg / 2 - (yi / H) * spanDeg;
          bestLon = normLon(solar.subsolarLon - 90);
          p = project(lat, bestLon);
          if (first) {
            g.moveTo(p.x, p.y);
            first = false;
          } else g.lineTo(p.x, p.y);
        }
        g.stroke();
      }
    }

    // Synoptic stylized clouds (NOT live radar) — only when LOD asks
    if (lod.showSynoptic) {
      var seed = Math.floor((opts.date || new Date()).getUTCHours() / 3);
      g.globalAlpha = lod.cloudAlpha;
      for (var i = 0; i < lod.precipBlobs; i++) {
        var t = (i * 37 + seed * 13) % 97;
        var cx = ((t * 17) % W) + ((i * 41) % 40);
        var cy = ((t * 29) % H) + ((i * 19) % 30);
        var rx = 40 + (t % 50);
        var ry = 18 + (t % 28);
        var grd = g.createRadialGradient(cx, cy, 4, cx, cy, rx);
        grd.addColorStop(0, "rgba(180, 200, 220, 0.55)");
        grd.addColorStop(0.55, "rgba(100, 130, 160, 0.28)");
        grd.addColorStop(1, "rgba(60, 90, 120, 0)");
        g.fillStyle = grd;
        g.beginPath();
        if (typeof g.ellipse === "function") {
          g.ellipse(cx, cy, rx, ry, (i * 0.4) % 1.2, 0, Math.PI * 2);
        } else {
          g.save();
          g.translate(cx, cy);
          g.scale(1, Math.max(0.2, ry / Math.max(1, rx)));
          g.arc(0, 0, rx, 0, Math.PI * 2);
          g.restore();
        }
        g.fill();
        // Light precip hatch under denser blobs
        if (i % 2 === 0 && lod.cloudAlpha > 0.25) {
          g.strokeStyle = "rgba(120, 170, 220, 0.25)";
          g.lineWidth = 1;
          for (var h = -ry; h < ry; h += 6) {
            g.beginPath();
            g.moveTo(cx - rx * 0.4, cy + h);
            g.lineTo(cx + rx * 0.4, cy + h + 4);
            g.stroke();
          }
        }
      }
      g.globalAlpha = 1;
    }

    // Local METAR / wind barb — always when METAR raw present; else LOD gates
    if (lod.showLocalMetar || lod.showWindBarb || METAR_LIVE.raw) {
      var px = W * 0.5;
      var py = H * 0.5;
      g.fillStyle = "rgba(14, 20, 28, 0.78)";
      g.strokeStyle = METAR_LIVE.raw
        ? "rgba(62, 207, 142, 0.95)"
        : blocked
          ? "rgba(224, 163, 92, 0.9)"
          : "rgba(62, 207, 142, 0.9)";
      g.lineWidth = 1.2;
      var boxY = py + H * 0.26;
      var boxH = METAR_LIVE.raw ? 52 : blocked ? 44 : 36;
      g.fillRect(px - 120, boxY, 240, boxH);
      g.strokeRect(px - 120, boxY, 240, boxH);
      g.fillStyle = "#c8d0d6";
      g.font = "600 11px ui-monospace, monospace";
      var metarLine = METAR_LIVE.raw
        ? (METAR_LIVE.icao || "") + " " + METAR_LIVE.raw.slice(0, 42)
        : blocked
          ? "METAR: " + status.slice(0, 28)
          : "METAR: membrane live";
      g.fillText(metarLine, px - 112, boxY + 16);
      g.font = "10px ui-monospace, monospace";
      g.fillStyle = "#8aa0ad";
      var windLine =
        METAR_LIVE.windKt != null
          ? "wind " +
            (METAR_LIVE.windDirDeg != null ? METAR_LIVE.windDirDeg + "°/" : "VRB/") +
            METAR_LIVE.windKt +
            "kt shear=" +
            (METAR_LIVE.shearRisk || "?")
          : "solar elev " + solar.elevationDeg.toFixed(1) + "°";
      g.fillText(windLine, px - 112, boxY + 30);
      if (radarFollowOn) {
        g.fillStyle = "#e0a35c";
        g.fillText(
          "radar " + (goes || "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH").slice(0, 36),
          px - 112,
          boxY + 44
        );
      }

      if (lod.showWindBarb || METAR_LIVE.windKt != null) {
        var az =
          METAR_LIVE.windDirDeg != null
            ? (METAR_LIVE.windDirDeg * Math.PI) / 180
            : ((solar.subsolarLon - centerLon) * Math.PI) / 180;
        var barbLen = 18 + Math.min(24, (METAR_LIVE.windKt || 8) * 0.9);
        g.save();
        g.translate(px + 90, py - 50);
        g.rotate(az);
        g.strokeStyle = "#f5c518";
        g.lineWidth = 2.2;
        g.beginPath();
        g.moveTo(0, barbLen * 0.55);
        g.lineTo(0, -barbLen * 0.7);
        g.stroke();
        g.beginPath();
        g.moveTo(0, -barbLen * 0.7);
        g.lineTo(9, -barbLen * 0.35);
        g.stroke();
        if ((METAR_LIVE.windKt || 0) >= 10) {
          g.beginPath();
          g.moveTo(0, -barbLen * 0.45);
          g.lineTo(11, -barbLen * 0.45);
          g.stroke();
        }
        g.restore();
        g.fillStyle = "#a8b8c4";
        g.font = "9px ui-monospace, monospace";
        g.fillText(
          METAR_LIVE.windKt != null ? "METAR wind" : "wind cue (computed)",
          px + 58,
          py - 72
        );
      }
    }

    // Corner status chip
    g.fillStyle = "rgba(10, 16, 24, 0.78)";
    g.fillRect(8, 8, 300, 48);
    g.fillStyle = METAR_LIVE.raw ? "#3ecf8e" : blocked ? "#e0a35c" : "#3ecf8e";
    g.font = "600 10px ui-monospace, monospace";
    g.fillText("WX " + status.slice(0, 34), 14, 22);
    g.fillStyle = "#9ab0bc";
    g.font = "10px ui-monospace, monospace";
    g.fillText(
      "solar " +
        (solar.isDay ? "DAY" : solar.twilight ? "TWILIGHT" : "NIGHT") +
        " elev=" +
        solar.elevationDeg.toFixed(1) +
        "° band=" +
        bandId,
      14,
      36
    );
    if (radarFollowOn) {
      g.fillStyle = "#e0a35c";
      g.fillText(
        "GOES " + (goes || "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH").slice(0, 40),
        14,
        48
      );
    }

    return {
      solar: solar,
      weatherStatus: status,
      goesStatus: goes || "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH",
      metar: METAR_LIVE.raw || "",
      windKt: METAR_LIVE.windKt,
      windDirDeg: METAR_LIVE.windDirDeg,
      lod: lod,
      blocked: blocked,
      radarFollowOn: radarFollowOn,
    };
  }

  /** Build THREE texture from overlay paint. */
  function makeOverlayTexture(THREE, centerLat, centerLon, spanDeg, bandId, date) {
    var W = 1024;
    var H = 1024;
    var c = document.createElement("canvas");
    c.width = W;
    c.height = H;
    var g = c.getContext("2d");
    var meta = paintOverlay(g, W, H, {
      centerLat: centerLat,
      centerLon: centerLon,
      spanDeg: spanDeg,
      bandId: bandId,
      date: date || new Date(),
    });
    var tex = new THREE.CanvasTexture(c);
    tex.needsUpdate = true;
    return { texture: tex, meta: meta };
  }

  global.SolarWeather = {
    solarState: solarState,
    refreshFeedStatus: refreshFeedStatus,
    feedStatus: feedStatus,
    setMetarFromPacket: setMetarFromPacket,
    metarLive: metarLive,
    parseMetarWind: parseMetarWind,
    bandWeatherLod: bandWeatherLod,
    paintOverlay: paintOverlay,
    makeOverlayTexture: makeOverlayTexture,
  };
})(typeof window !== "undefined" ? window : globalThis);
