/**
 * Affine.Earth OpenUSD — live traffic separation + anomaly warnings.
 * Computed from each ADS-B snapshot. Minima pegged to UUM8D manifold band.
 *
 * Rule thresholds (documented; ICAO-inspired simplified for map surface):
 *
 * | Band           | Lateral min | Vertical min | Closing alert      |
 * |----------------|-------------|--------------|--------------------|
 * | HEMISPHERE     | 5.0 nm      | 1000 ft      | range_nm < 1.5× lat |
 * | REGIONAL       | 5.0 nm      | 1000 ft      | range_nm < 1.5× lat |
 * | METRO (TMA)    | 3.0 nm      | 1000 ft      | range_nm < 1.5× lat |
 * | AIRPORT_WALK   | 1.0 nm      |  500 ft      | range_nm < 1.5× lat |
 *
 * Severity: CRITICAL (both axes breached + closing), HIGH (both breached),
 * MEDIUM (one axis + closing or near), LOW (anomaly only).
 */
(function (global) {
  "use strict";

  var MINIMA = {
    HEMISPHERE: { lateralNm: 5.0, verticalFt: 1000, label: "enroute" },
    REGIONAL: { lateralNm: 5.0, verticalFt: 1000, label: "corridor" },
    METRO: { lateralNm: 3.0, verticalFt: 1000, label: "terminal" },
    AIRPORT_WALK: { lateralNm: 1.0, verticalFt: 500, label: "airport" },
  };

  function minimaForBand(bandId) {
    return MINIMA[(bandId || "METRO").toUpperCase()] || MINIMA.METRO;
  }

  function distNm(lat1, lon1, lat2, lon2) {
    var R = 3440.065;
    var toR = Math.PI / 180;
    var dLat = (lat2 - lat1) * toR;
    var dLon = (lon2 - lon1) * toR;
    var a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * toR) * Math.cos(lat2 * toR) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(a)));
  }

  function trackVector(a) {
    var gs = Number(a.gs_kt) || 0;
    var trk = ((Number(a.track_deg) || 0) * Math.PI) / 180;
    // North/east components in nm/hr
    return { n: gs * Math.cos(trk), e: gs * Math.sin(trk), gs: gs };
  }

  /** Closing speed (kt): positive = approaching. */
  function closingSpeedKt(a, b) {
    var va = trackVector(a);
    var vb = trackVector(b);
    var toR = Math.PI / 180;
    var latm = (((Number(a.lat) + Number(b.lat)) / 2) * Math.PI) / 180;
    var dN = (Number(b.lat) - Number(a.lat)) * 60; // nm approx
    var dE = (Number(b.lon) - Number(a.lon)) * 60 * Math.cos(latm);
    var r = Math.sqrt(dN * dN + dE * dE) || 1;
    var rHatN = dN / r;
    var rHatE = dE / r;
    var vRelN = vb.n - va.n;
    var vRelE = vb.e - va.e;
    // Component of relative velocity along line of sight from a→b
    var vAlong = vRelN * rHatN + vRelE * rHatE;
    return -vAlong; // positive when approaching
  }

  function callsign(a) {
    return (a.callsign || a.icao || "?").toString().trim() || "?";
  }

  /**
   * Evaluate separation conflicts + flight anomalies on a live-shaped track list.
   * @returns {{ warnings: Array, minima: object, pairCount: number }}
   */
  function evaluate(rows, bandId, opts) {
    opts = opts || {};
    var minima = minimaForBand(bandId);
    var list = (rows || []).filter(function (a) {
      return a && a.lat != null && a.lon != null;
    });
    var warnings = [];
    var maxPairs = opts.maxPairs != null ? opts.maxPairs : 800;
    var pairs = 0;

    for (var i = 0; i < list.length; i++) {
      for (var j = i + 1; j < list.length; j++) {
        if (pairs++ > maxPairs) break;
        var a = list[i];
        var b = list[j];
        var latNm = distNm(Number(a.lat), Number(a.lon), Number(b.lat), Number(b.lon));
        var altA = Number(a.alt_baro_ft);
        var altB = Number(b.alt_baro_ft);
        if (isNaN(altA)) altA = 0;
        if (isNaN(altB)) altB = 0;
        var dAlt = Math.abs(altA - altB);
        var latBreach = latNm < minima.lateralNm;
        var vertBreach = dAlt < minima.verticalFt;
        if (!latBreach && latNm > minima.lateralNm * 2) continue;
        var closing = closingSpeedKt(a, b);
        var nearLat = latNm < minima.lateralNm * 1.5;
        if (!(latBreach && vertBreach) && !(nearLat && vertBreach && closing > 80)) continue;

        var severity = "MEDIUM";
        if (latBreach && vertBreach && closing > 120) severity = "CRITICAL";
        else if (latBreach && vertBreach) severity = "HIGH";
        else if (nearLat && vertBreach && closing > 80) severity = "MEDIUM";

        warnings.push({
          kind: "SEPARATION",
          severity: severity,
          a: callsign(a),
          b: callsign(b),
          icaoA: String(a.icao || "").toLowerCase(),
          icaoB: String(b.icao || "").toLowerCase(),
          latA: Number(a.lat),
          lonA: Number(a.lon),
          latB: Number(b.lat),
          lonB: Number(b.lon),
          lateralNm: Math.round(latNm * 100) / 100,
          verticalFt: Math.round(dAlt),
          closingKt: Math.round(closing),
          minima: minima,
          message:
            callsign(a) +
            " ↔ " +
            callsign(b) +
            " lat=" +
            latNm.toFixed(2) +
            "nm (<" +
            minima.lateralNm +
            ") Δalt=" +
            Math.round(dAlt) +
            "ft (<" +
            minima.verticalFt +
            ") close=" +
            Math.round(closing) +
            "kt [" +
            minima.label +
            "]",
        });
      }
      if (pairs > maxPairs) break;
    }

    // Speed / altitude anomalies (phase-of-flight heuristics)
    list.forEach(function (a) {
      var alt = Number(a.alt_baro_ft);
      var gs = Number(a.gs_kt);
      if (isNaN(alt) || isNaN(gs)) return;
      var msg = null;
      var sev = "LOW";
      if (alt < 800 && gs > 280) {
        msg = callsign(a) + " high speed " + Math.round(gs) + "kt at " + Math.round(alt) + "ft (pattern/ground)";
        sev = "MEDIUM";
      } else if (alt > 28000 && gs < 220 && gs > 40) {
        msg = callsign(a) + " low speed " + Math.round(gs) + "kt at FL" + Math.round(alt / 100);
        sev = "LOW";
      } else if (alt > 12000 && gs < 60) {
        msg = callsign(a) + " near-hover " + Math.round(gs) + "kt at " + Math.round(alt) + "ft";
        sev = "MEDIUM";
      } else if (
        (bandId || "").toUpperCase() === "AIRPORT_WALK" &&
        alt < 3000 &&
        gs > 220
      ) {
        msg = callsign(a) + " " + Math.round(gs) + "kt in airport walk band @ " + Math.round(alt) + "ft";
        sev = "MEDIUM";
      }
      if (!msg) return;
      warnings.push({
        kind: "ANOMALY",
        severity: sev,
        a: callsign(a),
        b: "",
        icaoA: String(a.icao || "").toLowerCase(),
        icaoB: "",
        latA: Number(a.lat),
        lonA: Number(a.lon),
        latB: null,
        lonB: null,
        lateralNm: null,
        verticalFt: null,
        closingKt: null,
        minima: minima,
        message: msg,
      });
    });

    // Weather hazard intersection — only when overlay reports active hazard zones
    var hazards = opts.weatherHazards || [];
    if (hazards.length) {
      list.forEach(function (a) {
        for (var h = 0; h < hazards.length; h++) {
          var z = hazards[h];
          var d = distNm(Number(a.lat), Number(a.lon), z.lat, z.lon);
          if (d < (z.radiusNm || 15)) {
            warnings.push({
              kind: "WEATHER",
              severity: z.severity || "MEDIUM",
              a: callsign(a),
              b: z.label || "WX",
              icaoA: String(a.icao || "").toLowerCase(),
              icaoB: "",
              latA: Number(a.lat),
              lonA: Number(a.lon),
              latB: z.lat,
              lonB: z.lon,
              lateralNm: Math.round(d * 100) / 100,
              verticalFt: null,
              closingKt: null,
              minima: minima,
              message: callsign(a) + " in " + (z.label || "weather zone") + " (" + d.toFixed(1) + "nm)",
            });
          }
        }
      });
    }

    var rank = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    warnings.sort(function (x, y) {
      return (rank[x.severity] || 9) - (rank[y.severity] || 9);
    });

    return {
      warnings: warnings.slice(0, opts.maxWarnings != null ? opts.maxWarnings : 40),
      minima: minima,
      pairCount: pairs,
      trackCount: list.length,
      bandId: (bandId || "METRO").toUpperCase(),
    };
  }

  global.TrafficWarnings = {
    MINIMA: MINIMA,
    minimaForBand: minimaForBand,
    distNm: distNm,
    closingSpeedKt: closingSpeedKt,
    evaluate: evaluate,
  };

  // Node / pytest bridge
  if (typeof module !== "undefined" && module.exports) {
    module.exports = global.TrafficWarnings;
  }
})(typeof window !== "undefined" ? window : globalThis);
