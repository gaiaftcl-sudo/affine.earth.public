/**
 * UUM8D manifold staging for Affine.Earth OpenUSD.
 * Observer zoom is a fiber projection on S⁴ staging bands — not CSS bitmap scale.
 * Band transitions swap map skin + traffic LOD + label density (lossless feel).
 */
(function (global) {
  "use strict";

  /**
   * Discrete staging bands (observer fiber stages).
   * zoomLevel is the continuous orthographic zoom (smooth lerp).
   * Thresholds are inclusive on the high side of the previous band.
   *
   *   HEMISPHERE   zoom ∈ [ZOOM_MIN, 0.42)   — world / hemisphere
   *   REGIONAL     zoom ∈ [0.42, 1.15)        — continent / FIR corridor
   *   METRO        zoom ∈ [1.15, 3.60)        — TMA / metro airspace
   *   AIRPORT_WALK zoom ∈ [3.60, ZOOM_MAX]    — runway / taxi / gate walk
   */
  var BANDS = [
    {
      id: "HEMISPHERE",
      label: "Hemisphere / planetary",
      zoomMin: 0,
      zoomMax: 0.42,
      skin: "map-hemisphere",
      spanMul: 14.0,
      fetchDistNm: 900,
      maxTracks: 48,
      maxDistNm: 1800,
      minAltFt: 18000,
      thinStride: 4,
      labelDensity: 0.25,
      spriteScale: 1.55,
      panSense: 1.0,
      walkMode: false,
    },
    {
      id: "REGIONAL",
      label: "Regional / corridor",
      zoomMin: 0.42,
      zoomMax: 1.15,
      skin: "map-regional",
      spanMul: 5.5,
      fetchDistNm: 350,
      maxTracks: 120,
      maxDistNm: 420,
      minAltFt: 8000,
      thinStride: 2,
      labelDensity: 0.55,
      spriteScale: 1.25,
      panSense: 1.05,
      walkMode: false,
    },
    {
      id: "METRO",
      label: "Metro / TMA",
      zoomMin: 1.15,
      zoomMax: 3.6,
      skin: "map-metro",
      spanMul: 1.6,
      fetchDistNm: 120,
      maxTracks: 220,
      maxDistNm: 140,
      minAltFt: 0,
      thinStride: 1,
      labelDensity: 0.85,
      spriteScale: 1.05,
      panSense: 1.15,
      walkMode: false,
    },
    {
      id: "AIRPORT_WALK",
      label: "Airport walk",
      zoomMin: 3.6,
      zoomMax: 99,
      skin: "map-airport",
      spanMul: 0.55,
      fetchDistNm: 45,
      maxTracks: 160,
      maxDistNm: 55,
      minAltFt: 0,
      thinStride: 1,
      labelDensity: 1.0,
      spriteScale: 0.92,
      panSense: 1.85,
      walkMode: true,
      preferGround: true,
    },
  ];

  var ZOOM_MIN = 0.08;
  var ZOOM_MAX = 14;
  /** Boot staging band — hemisphere start (UUM8D observer fiber). */
  var BOOT_ZOOM = 0.22;

  function bandForZoom(zoom) {
    var z = Number(zoom) || 0;
    for (var i = 0; i < BANDS.length; i++) {
      var b = BANDS[i];
      if (z < b.zoomMax) return b;
    }
    return BANDS[BANDS.length - 1];
  }

  function bandIndex(id) {
    for (var i = 0; i < BANDS.length; i++) {
      if (BANDS[i].id === id) return i;
    }
    return 0;
  }

  /** Haversine nm between two lat/lon. */
  function distNm(lat1, lon1, lat2, lon2) {
    var R = 3440.065; // Earth radius nm
    var toR = Math.PI / 180;
    var dLat = (lat2 - lat1) * toR;
    var dLon = (lon2 - lon1) * toR;
    var a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * toR) * Math.cos(lat2 * toR) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  /**
   * LOD filter: peg traffic to zoom band + distance-to-focus.
   * Live rows only — no authored loops. Returns filtered array.
   */
  function filterTracksForBand(rows, band, focusLat, focusLon) {
    var list = rows || [];
    var out = [];
    var stride = Math.max(1, band.thinStride | 0);
    var i = 0;
    for (var n = 0; n < list.length; n++) {
      var a = list[n];
      if (!a || a.lat == null || a.lon == null) continue;
      var d = distNm(focusLat, focusLon, Number(a.lat), Number(a.lon));
      if (d > band.maxDistNm) continue;
      var alt = Number(a.alt_baro_ft);
      if (isNaN(alt)) alt = 0;
      if (band.minAltFt > 0 && alt > 0 && alt < band.minAltFt) continue;
      if (band.preferGround) {
        // Airport walk: prefer arrivals/departures/ground-relevant (low alt or near field)
        var gs = Number(a.gs_kt) || 0;
        var groundish = alt < 12000 || d < 18 || gs < 250;
        if (!groundish && (n % 3) !== 0) continue;
      }
      if (i % stride !== 0) {
        i += 1;
        continue;
      }
      i += 1;
      out.push(a);
      if (out.length >= band.maxTracks) break;
    }
    return out;
  }

  function applySkin(skinId) {
    var link = document.getElementById("mapSkin");
    if (link) link.href = "assets/skins/" + skinId + ".css";
    var body = document.body;
    if (body) {
      body.className = body.className
        .split(/\s+/)
        .filter(function (c) {
          return c && c.indexOf("skin-") !== 0 && c.indexOf("band-") !== 0;
        })
        .concat(["skin-" + skinId])
        .join(" ");
    }
    var band = null;
    for (var i = 0; i < BANDS.length; i++) {
      if (BANDS[i].skin === skinId) {
        band = BANDS[i];
        break;
      }
    }
    if (band && body) body.classList.add("band-" + band.id.toLowerCase());
  }

  function zoomRational(zoom) {
    // Approximate rational for HUD (num/den) — display only
    var z = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, Number(zoom) || 1));
    var den = 100;
    var num = Math.round(z * den);
    return { num: num, den: den, text: num + "/" + den };
  }

  global.ManifoldStage = {
    BANDS: BANDS,
    ZOOM_MIN: ZOOM_MIN,
    ZOOM_MAX: ZOOM_MAX,
    BOOT_ZOOM: BOOT_ZOOM,
    bandForZoom: bandForZoom,
    bandIndex: bandIndex,
    distNm: distNm,
    filterTracksForBand: filterTracksForBand,
    applySkin: applySkin,
    zoomRational: zoomRational,
  };
})(typeof window !== "undefined" ? window : globalThis);
