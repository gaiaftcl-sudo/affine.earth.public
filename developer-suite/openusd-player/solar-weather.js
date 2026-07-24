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
      FEED_STATUS.noaa = feeds.noaa_weather || feeds.noaa_goes_r || "BLOCKED_NOAA_WEATHER_FEED";
      FEED_STATUS.note = "membrane live_feeds";
      FEED_STATUS.checkedAt = Date.now();
      FEED_STATUS.raw = feeds;
    } catch (e) {
      FEED_STATUS.noaa = "BLOCKED_FOLLOW_ON";
      FEED_STATUS.note = String(e).slice(0, 80);
      FEED_STATUS.checkedAt = Date.now();
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
    var status = FEED_STATUS.noaa || "UNKNOWN";
    var blocked = /BLOCKED/i.test(status);

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

    // Local METAR / wind barb cue (airport & metro) — honest when NOAA blocked
    if (lod.showLocalMetar || lod.showWindBarb) {
      var px = W * 0.5;
      var py = H * 0.5;
      g.fillStyle = "rgba(14, 20, 28, 0.72)";
      g.strokeStyle = blocked ? "rgba(224, 163, 92, 0.9)" : "rgba(62, 207, 142, 0.9)";
      g.lineWidth = 1.2;
      var boxY = py + H * 0.28;
      var boxH = blocked ? 44 : 36;
      g.fillRect(px - 92, boxY, 184, boxH);
      g.strokeRect(px - 92, boxY, 184, boxH);
      g.fillStyle = "#c8d0d6";
      g.font = "600 11px ui-monospace, monospace";
      g.fillText(
        blocked ? "METAR: " + status.slice(0, 28) : "METAR: membrane live",
        px - 84,
        py + H * 0.28 + 16
      );
      g.font = "10px ui-monospace, monospace";
      g.fillStyle = "#8aa0ad";
      g.fillText(
        "solar elev " + solar.elevationDeg.toFixed(1) + "° · Affine stylized wx",
        px - 84,
        py + H * 0.28 + 30
      );

      if (lod.showWindBarb) {
        // Stylized wind barb from solar azimuth proxy when METAR blocked
        // (honest cue — labeled "computed cue", not METAR wind)
        var az = ((solar.subsolarLon - centerLon) * Math.PI) / 180;
        g.save();
        g.translate(px + 70, py - 40);
        g.rotate(az);
        g.strokeStyle = "#f5c518";
        g.lineWidth = 2;
        g.beginPath();
        g.moveTo(0, 18);
        g.lineTo(0, -22);
        g.stroke();
        g.beginPath();
        g.moveTo(0, -22);
        g.lineTo(8, -12);
        g.stroke();
        g.beginPath();
        g.moveTo(0, -14);
        g.lineTo(10, -14);
        g.stroke();
        g.restore();
        g.fillStyle = "#a8b8c4";
        g.font = "9px ui-monospace, monospace";
        g.fillText(blocked ? "wind cue (computed)" : "wind", px + 48, py - 58);
      }
    }

    // Corner status chip
    g.fillStyle = "rgba(10, 16, 24, 0.78)";
    g.fillRect(8, 8, 280, 34);
    g.fillStyle = blocked ? "#e0a35c" : "#3ecf8e";
    g.font = "600 10px ui-monospace, monospace";
    g.fillText("WX " + status, 14, 22);
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

    return { solar: solar, weatherStatus: status, lod: lod, blocked: blocked };
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
    bandWeatherLod: bandWeatherLod,
    paintOverlay: paintOverlay,
    makeOverlayTexture: makeOverlayTexture,
  };
})(typeof window !== "undefined" ? window : globalThis);
