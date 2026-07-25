/**
 * Affine.Earth OpenUSD — UUM8D manifold ATC viewer (FR24-class map + yellow sprites).
 * Three.js CDN only; no Pixar libusd. No RealityPro naming.
 *
 * ATC map contract:
 * - Geographic basemap PRIMARY (land/ocean/airport diagram); c₄ grid secondary overlay
 * - Yellow heading-rotated aircraft sprites sized to view (readable at every band)
 * - Stream c₄ / uum8d-zoom / tracks — NOT video rasters
 * - Observer zoom = UUM8D manifold staging; JS is thin viewport
 * - Prefer GET /language-invariant/airspace/uum8d-zoom → c4-constraints → tracks fallback
 */
(function (global) {
  "use strict";

  var AIRPORTS = {
    KJFK: { lat: 40.6413, lon: -73.7781, name: "New York JFK", zoom: 7.2 },
    KEWR: { lat: 40.6895, lon: -74.1745, name: "Newark", zoom: 7.0 },
    KLAX: { lat: 33.9425, lon: -118.4081, name: "Los Angeles", zoom: 7.0 },
    EGLL: { lat: 51.47, lon: -0.4543, name: "London Heathrow", zoom: 6.8 },
    EHAM: { lat: 52.3105, lon: 4.7683, name: "Amsterdam Schiphol", zoom: 6.8 },
    LFPG: { lat: 49.0097, lon: 2.5479, name: "Paris CDG", zoom: 6.8 },
    EDDF: { lat: 50.0379, lon: 8.5622, name: "Frankfurt", zoom: 6.6 },
    RJTT: { lat: 35.5494, lon: 139.7798, name: "Tokyo Haneda", zoom: 6.8 },
    YSSY: { lat: -33.9399, lon: 151.1753, name: "Sydney", zoom: 6.8 },
    OMDB: { lat: 25.2532, lon: 55.3657, name: "Dubai", zoom: 6.6 },
  };

  var ICAO_ORDER = ["KJFK", "EGLL", "EHAM", "LFPG", "EDDF", "KLAX", "RJTT", "OMDB"];

  /**
   * UUM-8D surface twin stubs (coast / FIR / airport / runway) when membrane
   * globe-constraints empty for focus ICAO. Encoded as milli-deg c₄ curves —
   * not subterranean, not orbital/satellite chrome.
   */
  function surfaceTwinStub(icao) {
    var ap = AIRPORTS[icao];
    if (!ap) return null;
    var latM = Math.round(ap.lat * 1000);
    var lonM = Math.round(ap.lon * 1000);
    var dAp = 40;
    var dFir = 2500;
    var dCoast = 180;
    return {
      focus_icao: icao,
      boundary_count: 4,
      proven: "UUM8D_SURFACE_TWIN_STUB",
      schema: "affine.earth.uum8d.globe_constraints.v1",
      elevation_query_ft: 20,
      terrain_hit_count: 0,
      no_google_maps: true,
      structural_skins: true,
      boundaries: [
        {
          id: 1,
          kind: "airport",
          name: ap.name,
          icao: icao,
          elev_floor_ft: 20,
          min_lat_milli: latM - dAp,
          max_lat_milli: latM + dAp,
          min_lon_milli: lonM - dAp,
          max_lon_milli: lonM + dAp,
          curve_milli: [
            [latM - dAp, lonM - dAp],
            [latM - dAp, lonM + dAp],
            [latM + dAp, lonM + dAp],
            [latM + dAp, lonM - dAp],
            [latM - dAp, lonM - dAp],
          ],
        },
        {
          id: 2,
          kind: "runway",
          name: icao + " RWY",
          icao: icao,
          elev_floor_ft: 20,
          min_lat_milli: latM - 20,
          max_lat_milli: latM + 20,
          min_lon_milli: lonM - 35,
          max_lon_milli: lonM + 35,
          curve_milli: [
            [latM - 12, lonM - 30],
            [latM + 12, lonM + 30],
          ],
        },
        {
          id: 3,
          kind: "fir",
          name: icao + " FIR/ARTCC stub",
          min_lat_milli: latM - dFir,
          max_lat_milli: latM + dFir,
          min_lon_milli: lonM - dFir,
          max_lon_milli: lonM + dFir,
          curve_milli: [
            [latM - dFir, lonM - dFir],
            [latM + dFir, lonM - dFir],
            [latM + dFir, lonM + dFir],
            [latM - dFir, lonM + dFir],
            [latM - dFir, lonM - dFir],
          ],
        },
        {
          id: 4,
          kind: "coastline",
          name: icao + " coast floor cue",
          elev_floor_ft: 0,
          min_lat_milli: latM - dCoast,
          max_lat_milli: latM + dCoast,
          min_lon_milli: lonM - dCoast * 2,
          max_lon_milli: lonM + dCoast * 2,
          curve_milli: [
            [latM - dCoast, lonM - dCoast * 2],
            [latM - dCoast * 0.3, lonM - dCoast],
            [latM + dCoast * 0.2, lonM],
            [latM - dCoast * 0.4, lonM + dCoast],
            [latM - dCoast, lonM + dCoast * 2],
          ],
        },
      ],
    };
  }

  function parseUsdHints(usda) {
    var names = [];
    var re = /\bdef\s+(\w+)\s+"([^"]+)"/g;
    var m;
    while ((m = re.exec(usda || ""))) names.push({ type: m[1], name: m[2] });
    return names;
  }

  function schemaOf(usda) {
    var m = /gaia:schema\s*=\s*"([^"]+)"/.exec(usda || "");
    return m ? m[1] : "";
  }

  function customString(usda, key) {
    var re = new RegExp(
      "gaia:" + key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + '\\s*=\\s*"([^"]+)"'
    );
    var m = re.exec(usda || "");
    return m ? m[1] : "";
  }

  function parseSampleBody(body) {
    var samples = [];
    var sampleRe =
      /(\d+(?:\.\d+)?)\s*:\s*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)/g;
    var s;
    while ((s = sampleRe.exec(body || ""))) {
      samples.push({
        t: parseFloat(s[1]),
        x: parseFloat(s[2]),
        y: parseFloat(s[3]),
        z: parseFloat(s[4]),
      });
    }
    samples.sort(function (a, b) {
      return a.t - b.t;
    });
    return samples;
  }

  function parseTranslateTimeSamples(usda) {
    var text = usda || "";
    var blockRe = /xformOp:translate\.timeSamples\s*=\s*\{([^}]*)\}/gi;
    var samples = [];
    var block;
    while ((block = blockRe.exec(text))) {
      Array.prototype.push.apply(samples, parseSampleBody(block[1]));
    }
    samples.sort(function (a, b) {
      return a.t - b.t;
    });
    return samples;
  }

  function lerpSamples(samples, tNorm) {
    if (!samples || !samples.length) return null;
    if (samples.length === 1) return samples[0];
    var t0 = samples[0].t;
    var t1 = samples[samples.length - 1].t;
    var span = t1 > t0 ? t1 - t0 : 1;
    var t = t0 + (tNorm % 1) * span;
    var i = 0;
    while (i < samples.length - 1 && samples[i + 1].t < t) i += 1;
    var a = samples[i];
    var b = samples[Math.min(i + 1, samples.length - 1)];
    var den = b.t - a.t;
    var u = den > 0 ? (t - a.t) / den : 0;
    return {
      t: t,
      x: a.x + (b.x - a.x) * u,
      y: a.y + (b.y - a.y) * u,
      z: a.z + (b.z - a.z) * u,
    };
  }

  function makeHud(container) {
    var hud = document.createElement("div");
    hud.id = "openusd-live-hud";
    hud.setAttribute("data-openusd-live", "1");
    hud.setAttribute("data-strobe-tick", "0");
    hud.setAttribute("data-clock-ms", "0");
    hud.setAttribute("data-membrane-ticks", "0");
    hud.style.cssText =
      "position:absolute;left:8px;bottom:8px;z-index:5;font:11px/1.35 ui-monospace,monospace;" +
      "color:#9ab0bc;background:rgba(10,16,24,0.82);padding:6px 8px;border:1px solid #2a3a44;border-radius:4px;" +
      "max-width:94%;white-space:pre-wrap;";
    hud.textContent = "strobe=0";
    container.style.position = container.style.position || "relative";
    container.appendChild(hud);
    return hud;
  }

  function assetUrl(rel) {
    // Resolve relative to player directory (/language-game/openusd/)
    try {
      return new URL(rel, window.location.href).href;
    } catch (_) {
      return rel;
    }
  }

  /** Load Affine.Earth SVG sprite → Three texture (yellow jet / heavy / light). */
  function loadSpriteTexture(THREE, relPath, fallbackDraw) {
    return new Promise(function (resolve) {
      var loader = new THREE.TextureLoader();
      loader.load(
        assetUrl(relPath),
        function (tex) {
          tex.needsUpdate = true;
          resolve(tex);
        },
        undefined,
        function () {
          resolve(fallbackDraw(THREE));
        }
      );
    });
  }

  /** Canvas fallback if SVG fetch fails. */
  function makePlaneTextureFallback(THREE) {
    var c = document.createElement("canvas");
    c.width = 64;
    c.height = 64;
    var g = c.getContext("2d");
    g.clearRect(0, 0, 64, 64);
    g.translate(32, 32);
    g.fillStyle = "#f5c518";
    g.beginPath();
    g.moveTo(0, -22);
    g.lineTo(3.5, 10);
    g.lineTo(2, 18);
    g.lineTo(-2, 18);
    g.lineTo(-3.5, 10);
    g.closePath();
    g.fill();
    g.beginPath();
    g.moveTo(-22, 2);
    g.lineTo(22, 2);
    g.lineTo(18, 7);
    g.lineTo(-18, 7);
    g.closePath();
    g.fill();
    var tex = new THREE.CanvasTexture(c);
    tex.needsUpdate = true;
    return tex;
  }

  function skinPalette() {
    var root = getComputedStyle(document.body);
    var ocean = (root.getPropertyValue("--ae-ocean") || "").trim() || "#0a1628";
    // Land must read against ocean at HEMISPHERE (FR24-class geographic context).
    var land = (root.getPropertyValue("--ae-land") || "").trim() || "#2a3a30";
    var label = (root.getPropertyValue("--ae-label") || "").trim() || "#d0d8de";
    var accent = (root.getPropertyValue("--ae-accent") || "").trim() || "#f5c518";
    return { ocean: ocean, land: land, label: label, accent: accent };
  }

  /**
   * ATC basemap — geographic land / ocean / airport diagram (CanvasTexture).
   * Product path: this texture is PRIMARY. Procedural c₄ grid is a secondary overlay.
   */
  function makeBasemapTexture(THREE, centerLat, centerLon, spanDeg, bandId) {
    var pal = skinPalette();
    var band = (bandId || "METRO").toUpperCase();
    var W = 1024;
    var H = 1024;
    var c = document.createElement("canvas");
    c.width = W;
    c.height = H;
    var g = c.getContext("2d");
    g.fillStyle = pal.ocean;
    g.fillRect(0, 0, W, H);
    var grd = g.createRadialGradient(W * 0.5, H * 0.45, 40, W * 0.5, H * 0.5, W * 0.75);
    grd.addColorStop(0, pal.ocean);
    grd.addColorStop(1, band === "HEMISPHERE" ? "#03080e" : "#071018");
    g.fillStyle = grd;
    g.fillRect(0, 0, W, H);

    function project(lat, lon) {
      var x = ((lon - (centerLon - spanDeg / 2)) / spanDeg) * W;
      var y = ((centerLat + spanDeg / 2 - lat) / spanDeg) * H;
      return { x: x, y: y };
    }

    function fillPoly(poly, fill, stroke) {
      g.beginPath();
      poly.forEach(function (ll, i) {
        var p = project(ll[0], ll[1]);
        if (i === 0) g.moveTo(p.x, p.y);
        else g.lineTo(p.x, p.y);
      });
      g.closePath();
      g.fillStyle = fill;
      g.fill();
      if (stroke) {
        g.strokeStyle = stroke;
        g.lineWidth = band === "HEMISPHERE" ? 1.6 : 1.1;
        g.stroke();
      }
    }

    // World-scale land (always drawn; clipped by span) — surface twin, not orbital
    var lands = [
      [[72, -170], [70, -50], [55, -65], [30, -80], [25, -97], [15, -90], [8, -78], [50, -55], [72, -50], [72, -170]],
      [[55, -10], [71, -10], [70, 40], [55, 40], [36, 28], [36, -9], [55, -10]],
      [[60, -8], [59, 2], [50, 2], [50, -6], [55, -8], [60, -8]],
      [[36, -10], [36, 35], [5, 40], [-5, 10], [5, -17], [36, -10]],
      [[55, 60], [70, 180], [45, 145], [20, 120], [10, 100], [25, 60], [55, 60]],
      [[-10, 110], [-45, 145], [-35, 175], [-15, 150], [-10, 110]],
      [[12, -80], [-55, -70], [-55, -40], [5, -35], [12, -80]],
    ];
    var landFill = band === "HEMISPHERE" ? "#334840" : pal.land;
    var landStroke = band === "HEMISPHERE" ? "#6a9a78" : "#3a5548";
    lands.forEach(function (poly) {
      fillPoly(poly, landFill, landStroke);
    });
    // Coast emphasis stroke (surface floor cue — distinct from abstract fill)
    g.lineWidth = band === "HEMISPHERE" ? 2.2 : 1.6;
    g.strokeStyle = "rgba(90, 160, 140, 0.75)";
    lands.forEach(function (poly) {
      g.beginPath();
      poly.forEach(function (ll, i) {
        var p = project(ll[0], ll[1]);
        if (i === 0) g.moveTo(p.x, p.y);
        else g.lineTo(p.x, p.y);
      });
      g.closePath();
      g.stroke();
    });
    // Doctrine chip on basemap (dead-cat refuse)
    g.fillStyle = "rgba(10,16,24,0.72)";
    g.fillRect(8, H - 36, 420, 28);
    g.fillStyle = "#e0a35c";
    g.font = "600 10px ui-monospace, monospace";
    g.fillText(
      "UUM-8D surface twin · DEAD_CAT_REFUSED: subterranean · orbital/satellite-about",
      14,
      H - 18
    );

    // Regional denser blobs near focus
    if (band === "REGIONAL" || band === "METRO" || band === "AIRPORT_WALK") {
      fillPoly(
        [
          [centerLat + 8, centerLon - 10],
          [centerLat + 6, centerLon + 8],
          [centerLat - 4, centerLon + 6],
          [centerLat - 6, centerLon - 8],
          [centerLat + 8, centerLon - 10],
        ],
        pal.land,
        "#2e4438"
      );
    }

    // Grid density by band
    var gridAlpha = band === "HEMISPHERE" ? 0.14 : band === "REGIONAL" ? 0.22 : band === "METRO" ? 0.3 : 0.38;
    g.strokeStyle = "rgba(70,100,120," + gridAlpha + ")";
    g.lineWidth = 1;
    var step = spanDeg > 60 ? 15 : spanDeg > 25 ? 5 : spanDeg > 10 ? 2 : spanDeg > 4 ? 1 : 0.5;
    for (var lat = Math.floor((centerLat - spanDeg / 2) / step) * step; lat <= centerLat + spanDeg / 2; lat += step) {
      var a = project(lat, centerLon - spanDeg / 2);
      var b = project(lat, centerLon + spanDeg / 2);
      g.beginPath();
      g.moveTo(a.x, a.y);
      g.lineTo(b.x, b.y);
      g.stroke();
    }
    for (var lon = Math.floor((centerLon - spanDeg / 2) / step) * step; lon <= centerLon + spanDeg / 2; lon += step) {
      var c1 = project(centerLat + spanDeg / 2, lon);
      var c2 = project(centerLat - spanDeg / 2, lon);
      g.beginPath();
      g.moveTo(c1.x, c1.y);
      g.lineTo(c2.x, c2.y);
      g.stroke();
    }

    // Airport diagram overlay (runway/taxi feel) — AIRPORT_WALK band
    if (band === "AIRPORT_WALK" || band === "METRO") {
      var cx = W * 0.5;
      var cy = H * 0.5;
      var rw = band === "AIRPORT_WALK" ? W * 0.42 : W * 0.18;
      var rh = band === "AIRPORT_WALK" ? 14 : 6;
      g.save();
      g.translate(cx, cy);
      g.rotate((-32 * Math.PI) / 180);
      g.fillStyle = band === "AIRPORT_WALK" ? "#3a4048" : "rgba(58,64,72,0.55)";
      g.fillRect(-rw / 2, -rh / 2, rw, rh);
      g.fillRect(-rw * 0.35, -rh * 2.2, rw * 0.7, rh * 0.7);
      if (band === "AIRPORT_WALK") {
        g.strokeStyle = "#f5c518";
        g.lineWidth = 1.5;
        g.setLineDash([8, 10]);
        g.beginPath();
        g.moveTo(-rw / 2 + 4, 0);
        g.lineTo(rw / 2 - 4, 0);
        g.stroke();
        g.setLineDash([]);
        // Taxi / apron blocks
        g.fillStyle = "#2a3238";
        g.fillRect(-rw * 0.2, rh * 1.2, rw * 0.45, rh * 3.5);
        g.fillRect(rw * 0.15, -rh * 4.5, rw * 0.22, rh * 3);
        g.fillStyle = pal.accent;
        g.font = "600 13px sans-serif";
        g.fillText("RWY", -18, -rh - 6);
      }
      g.restore();
    }

    // Labels — density follows band
    var labelEvery = band === "HEMISPHERE" ? 2 : 1;
    var li = 0;
    g.font = band === "HEMISPHERE" ? "600 12px sans-serif" : "600 14px sans-serif";
    Object.keys(AIRPORTS).forEach(function (icao) {
      var ap = AIRPORTS[icao];
      if (Math.abs(ap.lat - centerLat) > spanDeg * 0.55) return;
      if (Math.abs(ap.lon - centerLon) > spanDeg * 0.55) return;
      if (band === "HEMISPHERE" && (li++ % labelEvery) !== 0 && icao !== Object.keys(AIRPORTS)[0]) {
        // still mark major hubs
        if (["KJFK", "EGLL", "RJTT", "OMDB", "YSSY"].indexOf(icao) < 0) return;
      }
      var p = project(ap.lat, ap.lon);
      g.beginPath();
      g.fillStyle = pal.accent;
      g.arc(p.x, p.y, band === "AIRPORT_WALK" ? 5 : 3.5, 0, Math.PI * 2);
      g.fill();
      g.fillStyle = pal.label;
      var label =
        band === "HEMISPHERE"
          ? icao
          : band === "AIRPORT_WALK"
            ? ap.name
            : ap.name.split(" ")[0];
      g.fillText(label, p.x + 6, p.y - 4);
    });

    var tex = new THREE.CanvasTexture(c);
    tex.needsUpdate = true;
    return tex;
  }

  function lonLatToWorld(lat, lon, centerLat, centerLon, scale) {
    // equirectangular local km-ish units
    var x = (lon - centerLon) * Math.cos((centerLat * Math.PI) / 180) * scale;
    var z = -(lat - centerLat) * scale;
    return { x: x, z: z };
  }

  /**
   * Procedural manifold grid from band + zoom_depth — scale-invariant lines.
   * No CanvasTexture stretch; LOD via line density (constraint depth), not mipmaps.
   */
  function makeProceduralManifoldGrid(THREE, spanWorld, bandId, zoomDepth) {
    var pal = skinPalette();
    var band = (bandId || "METRO").toUpperCase();
    var depth = Math.max(0, zoomDepth | 0);
    var divisions =
      band === "HEMISPHERE"
        ? 8 + depth
        : band === "REGIONAL"
          ? 16 + depth * 2
          : band === "METRO"
            ? 28 + depth * 3
            : 40 + depth * 4;
    var half = spanWorld / 2;
    var step = spanWorld / Math.max(2, divisions);
    var positions = [];
    for (var i = 0; i <= divisions; i++) {
      var t = -half + i * step;
      positions.push(-half, 0, t, half, 0, t);
      positions.push(t, 0, -half, t, 0, half);
    }
    // Crosshair at camera origin (Euclidean re-root stay near 0,0,0)
    var cross = half * 0.08;
    positions.push(-cross, 0.01, 0, cross, 0.01, 0);
    positions.push(0, 0.01, -cross, 0, 0.01, cross);
    var geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    var color =
      band === "AIRPORT_WALK"
        ? 0xf5c518
        : band === "METRO"
          ? 0x6a8a9a
          : band === "REGIONAL"
            ? 0x4a6a7a
            : 0x2a4a5a;
    var mat = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: band === "AIRPORT_WALK" ? 0.85 : 0.65,
    });
    var lines = new THREE.LineSegments(geo, mat);
    lines.userData.bandId = band;
    lines.userData.procedural = true;
    lines.userData.zoomDepth = depth;
    // Flat ocean plane (solid color — not a video/radar texture)
    var ocean = new THREE.Mesh(
      new THREE.PlaneGeometry(spanWorld, spanWorld),
      new THREE.MeshBasicMaterial({ color: pal.ocean || 0x0a1628 })
    );
    ocean.rotation.x = -Math.PI / 2;
    ocean.position.y = -0.12;
    var group = new THREE.Group();
    group.add(ocean);
    group.add(lines);
    // Origin crosshair (Euclidean re-root stay) — bright yellow
    var originGeo = new THREE.BufferGeometry();
    var oc = spanWorld * 0.04;
    originGeo.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(
        [-oc, 0.02, 0, oc, 0.02, 0, 0, 0.02, -oc, 0, 0.02, oc],
        3
      )
    );
    group.add(
      new THREE.LineSegments(
        originGeo,
        new THREE.LineBasicMaterial({ color: 0xf5c518, opacity: 0.95, transparent: true })
      )
    );
    group.userData.bandId = band;
    group.userData.procedural = true;
    group.userData.dispose = function () {
      geo.dispose();
      mat.dispose();
      ocean.geometry.dispose();
      ocean.material.dispose();
    };
    return group;
  }

  function buildLatticeScene(THREE, container, hints, usdaText) {
    var w = container.clientWidth || 640;
    var h = container.clientHeight || 420;
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 200);
    camera.position.set(4.5, 3.2, 5.5);
    camera.lookAt(0, 0, 0);
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    var hud = makeHud(container);
    scene.add(new THREE.AmbientLight(0x668888, 0.7));
    var dir = new THREE.DirectionalLight(0xffffff, 0.85);
    dir.position.set(3, 6, 2);
    scene.add(dir);
    scene.add(new THREE.GridHelper(10, 20, 0x3ecf8e, 0x24343c));
    var group = new THREE.Group();
    scene.add(group);
    var timeSamples = parseTranslateTimeSamples(usdaText);
    var n = Math.max(hints.length, 8);
    var basePositions = [];
    for (var i = 0; i < n; i++) {
      var geo = new THREE.SphereGeometry(0.18, 16, 16);
      var mat = new THREE.MeshStandardMaterial({ color: 0x3ecf8e });
      var mesh = new THREE.Mesh(geo, mat);
      var angle = (i / n) * Math.PI * 2;
      var r = 1.6 + (i % 3) * 0.35;
      var pos = { x: Math.cos(angle) * r, y: (i % 5) * 0.25 - 0.5, z: Math.sin(angle) * r };
      basePositions.push(pos);
      mesh.position.set(pos.x, pos.y, pos.z);
      group.add(mesh);
    }
    var raf = 0;
    var strobeTick = 0;
    var membraneTicks = 0;
    var membranePulse = 0;
    var t0 = performance.now();
    function tick() {
      strobeTick += 1;
      var elapsedMs = performance.now() - t0;
      var sample = lerpSamples(timeSamples, (elapsedMs / 8000) % 1);
      group.rotation.y = elapsedMs * 0.00035;
      group.children.forEach(function (mesh, idx) {
        var b = basePositions[idx];
        var breath = 1 + 0.1 * Math.sin(elapsedMs * 0.004 + idx);
        mesh.position.set(
          b.x * breath + (sample ? sample.x * 0.2 : 0),
          b.y + (sample ? sample.y * 0.2 : 0),
          b.z * breath + (sample ? sample.z * 0.2 : 0)
        );
      });
      if (membranePulse > 0) membranePulse *= 0.92;
      hud.setAttribute("data-strobe-tick", String(strobeTick));
      hud.setAttribute("data-clock-ms", String(Math.floor(elapsedMs)));
      hud.setAttribute("data-membrane-ticks", String(membraneTicks));
      hud.setAttribute("data-scene-mode", "lattice");
      hud.textContent =
        "mode=lattice strobe=" + strobeTick + " clock=" + Math.floor(elapsedMs) + "ms";
      container.setAttribute("data-strobe-tick", String(strobeTick));
      container.setAttribute("data-clock-ms", String(Math.floor(elapsedMs)));
      container.setAttribute("data-openusd-animating", "1");
      renderer.render(scene, camera);
      raf = requestAnimationFrame(tick);
    }
    tick();
    function onResize() {
      var nw = container.clientWidth || 640;
      var nh = container.clientHeight || 420;
      camera.aspect = nw / nh;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, nh);
    }
    window.addEventListener("resize", onResize);
    return {
      dispose: function () {
        cancelAnimationFrame(raf);
        window.removeEventListener("resize", onResize);
        renderer.dispose();
        if (hud.parentNode) hud.parentNode.removeChild(hud);
      },
      hintCount: hints.length,
      timeSampleCount: timeSamples.length,
      sceneMode: "lattice",
      applyMembraneTick: function () {
        membraneTicks += 1;
        membranePulse = 1;
      },
      getLiveState: function () {
        return {
          strobeTick: strobeTick,
          clockMs: Math.floor(performance.now() - t0),
          membraneTicks: membraneTicks,
          sceneMode: "lattice",
        };
      },
    };
  }

  function buildAtcScene(THREE, container, hints, usdaText, opts) {
    opts = opts || {};
    var w = container.clientWidth || 640;
    var h = container.clientHeight || 420;
    var focusIcao = (opts.icao || customString(usdaText, "focus_icao") || "KJFK").toUpperCase();
    if (!AIRPORTS[focusIcao]) focusIcao = "KJFK";
    var ap = AIRPORTS[focusIcao];
    var centerLat = ap.lat;
    var centerLon = ap.lon;
    var mapScale = 48; // deg → world units
    var viewSpanDeg = ap.zoom; // geographic span of basemap
    var orthoHalf = (viewSpanDeg * mapScale) / 2.4;

    var scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a1628);
    var camera = new THREE.OrthographicCamera(
      -orthoHalf * (w / h),
      orthoHalf * (w / h),
      orthoHalf,
      -orthoHalf,
      0.1,
      2000
    );
    camera.position.set(0, 80, 0);
    camera.up.set(0, 0, -1);
    camera.lookAt(0, 0, 0);
    // UUM8D manifold zoom — continuous lerp; discrete band LOD at thresholds
    var MS = global.ManifoldStage || null;
    var ZOOM_MIN = MS ? MS.ZOOM_MIN : 0.08;
    var ZOOM_MAX = MS ? MS.ZOOM_MAX : 14;
    var zoomLevel = MS ? MS.BOOT_ZOOM : 0.22;
    var targetZoom = zoomLevel;
    var panX = 0;
    var panZ = 0;
    var targetPanX = 0;
    var targetPanZ = 0;
    var currentBand = MS ? MS.bandForZoom(zoomLevel) : { id: "HEMISPHERE", label: "Hemisphere / planetary", skin: "map-hemisphere", fetchDistNm: 900, panSense: 1, walkMode: false, spriteScale: 1.5 };
    var manifoldStageId = currentBand.id;
    var skinCrossfade = 1;
    var pendingSkin = null;
    var dragging = false;
    var spaceDown = false;
    var lastPtr = null;
    var lastTapMs = 0;
    var lastTapX = 0;
    var lastTapY = 0;
    var lodTrackCount = 0;
    var lastFetchDist = currentBand.fetchDistNm || 100;
    var rawTrackCache = [];

    var renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      preserveDrawingBuffer: true, // evidence / screenshot path
    });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    renderer.domElement.style.cursor = "grab";
    renderer.domElement.style.touchAction = "none";
    container.setAttribute("data-manifold-band", manifoldStageId);
    container.setAttribute("data-walk-mode", currentBand.walkMode ? "1" : "0");

    var hud = makeHud(container);
    hud.setAttribute("data-scene-mode", "atc-map");
    hud.setAttribute("data-focus-icao", focusIcao);
    hud.setAttribute("data-track-source", "adsb.lol_https_v2");
    hud.setAttribute("data-manifold-band", manifoldStageId);

    // Title chrome
    var chrome = document.createElement("div");
    chrome.className = "map-chrome top-left";
    chrome.innerHTML =
      '<div class="map-title">Affine.Earth OpenUSD · LIVE ATC map</div>' +
      '<div class="map-sub" id="mapSubTitle">manifold ' +
      currentBand.label +
      " · " +
      focusIcao +
      " · live ADS-B</div>" +
      '<div class="map-band" id="mapBandHud">' +
      currentBand.id +
      " · UUM-8D</div>";
    container.appendChild(chrome);

    // Always-visible ATC twin chrome: airport + UUM-8D views + wx + dead-cat doctrine
    var twin = document.createElement("div");
    twin.id = "atc-twin-chrome";
    twin.className = "atc-twin-chrome";
    twin.setAttribute("data-uum8d-twin", "1");
    twin.setAttribute("role", "toolbar");
    twin.setAttribute("aria-label", "UUM-8D ATC twin controls");
    var apBtns = ICAO_ORDER.map(function (icao) {
      return (
        '<button type="button" class="twin-icao' +
        (icao === focusIcao ? " active" : "") +
        '" data-icao="' +
        icao +
        '" title="' +
        (AIRPORTS[icao] ? AIRPORTS[icao].name : icao) +
        '">' +
        icao +
        "</button>"
      );
    }).join("");
    var viewIds = ["HEMISPHERE", "REGIONAL", "METRO", "AIRPORT_WALK"];
    var viewBtns = viewIds
      .map(function (id) {
        return (
          '<button type="button" class="twin-view' +
          (id === manifoldStageId ? " active" : "") +
          '" data-band="' +
          id +
          '" title="UUM-8D manifold view ' +
          id +
          '">' +
          id +
          "</button>"
        );
      })
      .join("");
    twin.innerHTML =
      '<div class="twin-label">Airport focus</div>' +
      '<div class="twin-airports" id="twinAirportGrid">' +
      apBtns +
      "</div>" +
      '<div class="twin-label">UUM-8D manifold view <span class="twin-c4" id="twinC4Meta">c₄ zoom↔band</span></div>' +
      '<div class="twin-views" id="twinViewGrid">' +
      viewBtns +
      "</div>" +
      '<div class="twin-wx" id="twinWxPanel" data-wx-panel="1">WX · loading METAR / wind…</div>' +
      '<div class="twin-doctrine" id="twinDoctrine">' +
      "DEAD_CAT_REFUSED: subterranean · satellite-about/orbital as primary scene · " +
      "surface twin only (coast/FIR/terrain floors)</div>";
    container.appendChild(twin);

    // Zoom controls
    var zoomStack = document.createElement("div");
    zoomStack.className = "zoom-stack";
    zoomStack.innerHTML =
      '<button type="button" id="btnZoomIn" title="Zoom in (drives c₄ zoom_milli)">+</button>' +
      '<button type="button" id="btnZoomOut" title="Zoom out (drives c₄ zoom_milli)">−</button>' +
      '<button type="button" id="btnZoomAirport" title="AIRPORT_WALK band">⌖</button>' +
      '<button type="button" id="btnZoomMetro" title="METRO band">▣</button>' +
      '<button type="button" id="btnZoomRegional" title="REGIONAL band">▦</button>' +
      '<button type="button" id="btnZoomHemi" title="HEMISPHERE band">◎</button>';
    container.appendChild(zoomStack);

    var lastWeatherPkt = null;
    var lastGlobePkt = null;
    var lastC4ZoomDepth = 0;

    function syncUrlState() {
      try {
        var u = new URL(location.href);
        u.searchParams.set("icao", focusIcao);
        u.searchParams.set("band", manifoldStageId);
        u.searchParams.set(
          "zoom_milli",
          String(Math.round(zoomLevel * 1000))
        );
        history.replaceState(null, "", u.pathname + u.search + u.hash);
      } catch (_) {}
    }

    function syncTwinChrome() {
      twin.querySelectorAll(".twin-icao").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-icao") === focusIcao);
      });
      twin.querySelectorAll(".twin-view").forEach(function (b) {
        b.classList.toggle("active", b.getAttribute("data-band") === manifoldStageId);
      });
      var c4El = document.getElementById("twinC4Meta");
      if (c4El) {
        c4El.textContent =
          "c₄ zoom_milli=" +
          Math.round(zoomLevel * 1000) +
          " depth=" +
          lastC4ZoomDepth +
          " band=" +
          manifoldStageId;
      }
      document.querySelectorAll("#airportGrid button").forEach(function (b) {
        b.classList.toggle(
          "active-airport",
          b.getAttribute("data-icao") === focusIcao
        );
      });
      var skinSel = document.getElementById("skinSelect");
      if (skinSel && currentBand && currentBand.skin) {
        var want = currentBand.skin;
        if (skinSel.value !== want) {
          for (var i = 0; i < skinSel.options.length; i++) {
            if (skinSel.options[i].value === want) {
              skinSel.selectedIndex = i;
              break;
            }
          }
        }
      }
      syncUrlState();
    }

    function updateTwinWxPanel() {
      var el = document.getElementById("twinWxPanel");
      if (!el) return;
      var live = SW && SW.metarLive ? SW.metarLive() : null;
      var wx = lastWeatherPkt || live || {};
      var raw = wx.raw || (live && live.raw) || "";
      var status = wx.status || (live && live.status) || wxStatus || "UNKNOWN";
      var goes =
        (live && live.goesStatus) ||
        "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH";
      var windKt = wx.windKt != null ? wx.windKt : live && live.windKt;
      var windDir = wx.windDirDeg != null ? wx.windDirDeg : live && live.windDirDeg;
      var windTxt =
        windKt != null
          ? "wind " + (windDir != null ? windDir + "°/" : "VRB/") + windKt + "kt"
          : "wind —";
      el.setAttribute("data-wx-status", status);
      el.setAttribute("data-goes", goes);
      el.innerHTML =
        '<span class="wx-status">' +
        status +
        "</span> · " +
        windTxt +
        (wx.shearRisk || (live && live.shearRisk)
          ? " · shear=" + (wx.shearRisk || live.shearRisk)
          : "") +
        "<br/><span class=\"wx-metar\">" +
        (raw ? raw.slice(0, 96) : "METAR pending / observation void") +
        '</span><br/><span class="wx-goes">radar ' +
        goes +
        "</span>";
    }

    function bandSpanDeg(band) {
      var mul = band && band.spanMul != null ? band.spanMul : 1.6;
      return Math.max(2.5, viewSpanDeg * mul);
    }

    var rerootState = { active: false, zoomDepth: 0 };
    var useLocalC4 = false;

    function buildMapMesh(band) {
      var span = bandSpanDeg(band);
      var cosLat = Math.cos((centerLat * Math.PI) / 180);
      var sizeX = Math.max(viewSpanDeg * 1.35, span) * mapScale * cosLat;
      var sizeZ = Math.max(viewSpanDeg * 1.35, span) * mapScale;
      var tex = makeBasemapTexture(THREE, centerLat, centerLon, span, band.id);
      var geo = new THREE.PlaneGeometry(sizeX, sizeZ);
      var mat = new THREE.MeshBasicMaterial({
        map: tex,
        depthWrite: true,
      });
      var base = new THREE.Mesh(geo, mat);
      base.rotation.x = -Math.PI / 2;
      base.position.y = -0.1;
      // Secondary: faint c₄ LOD grid + origin crosshair (Study09 / manifold cue)
      var grid = makeProceduralManifoldGrid(
        THREE,
        Math.max(sizeX, sizeZ),
        band.id,
        rerootState.zoomDepth || 0
      );
      // Hide solid ocean from procedural group — basemap already paints geography
      grid.children.forEach(function (ch) {
        if (ch.isMesh && ch.material && !ch.material.map) {
          ch.visible = false;
        }
        if (ch.isLineSegments && ch.material) {
          ch.material.opacity = band.id === "AIRPORT_WALK" ? 0.35 : 0.18;
          ch.material.transparent = true;
        }
      });
      grid.position.y = 0.01;
      var group = new THREE.Group();
      group.add(base);
      group.add(grid);
      group.userData.bandId = band.id;
      group.userData.geographic = true;
      group.userData.dispose = function () {
        if (tex) tex.dispose();
        geo.dispose();
        mat.dispose();
        if (grid.userData && typeof grid.userData.dispose === "function") {
          grid.userData.dispose();
        }
      };
      return group;
    }

    if (MS && MS.applySkin) MS.applySkin(currentBand.skin);
    var mapMesh = buildMapMesh(currentBand);
    var mapMeshPrev = null;
    scene.add(mapMesh);
    container.setAttribute("data-procedural-c4", "1");
    container.setAttribute("data-no-raster-video", "1");
    document.body.classList.add("manifold-viewer");

    // Solar + weather overlay (band LOD) — above basemap, below aircraft
    var SW = global.SolarWeather || null;
    var TW = global.TrafficWarnings || null;
    var wxOverlayMesh = null;
    var wxMeta = null;
    var wxStatus = "UNKNOWN";
    var lastWxRebuildMs = 0;
    var warningState = { warnings: [], minima: null, pairCount: 0 };
    var warnLineGroup = new THREE.Group();
    scene.add(warnLineGroup);

    function rebuildWxOverlay() {
      if (!SW || !SW.makeOverlayTexture) return;
      try {
        var span = bandSpanDeg(currentBand);
        var built = SW.makeOverlayTexture(
          THREE,
          centerLat,
          centerLon,
          span,
          currentBand.id,
          new Date()
        );
        wxMeta = built.meta;
        wxStatus = (built.meta && built.meta.weatherStatus) || wxStatus;
        var size = Math.max(viewSpanDeg * 1.35, span) * mapScale;
        if (wxOverlayMesh) disposeMapMesh(wxOverlayMesh);
        var cosLatWx = Math.cos((centerLat * Math.PI) / 180);
        wxOverlayMesh = new THREE.Mesh(
          new THREE.PlaneGeometry(size * cosLatWx, size),
          new THREE.MeshBasicMaterial({
            map: built.texture,
            transparent: true,
            opacity: currentBand.id === "HEMISPHERE" ? 0.38 : 0.48,
            depthWrite: false,
          })
        );
        wxOverlayMesh.rotation.x = -Math.PI / 2;
        wxOverlayMesh.position.y = -0.03;
        scene.add(wxOverlayMesh);
        hud.setAttribute("data-wx-status", wxStatus);
        hud.setAttribute(
          "data-solar-elev",
          built.meta && built.meta.solar ? built.meta.solar.elevationDeg.toFixed(1) : ""
        );
        container.setAttribute("data-wx-status", wxStatus);
      } catch (e) {
        wxStatus = "OVERLAY_SOFT_FAIL";
        hud.setAttribute("data-wx-status", wxStatus);
        hud.setAttribute("data-wx-error", String(e).slice(0, 80));
      }
    }

    if (SW && SW.refreshFeedStatus) {
      SW.refreshFeedStatus().then(function () {
        wxStatus = (SW.feedStatus() || {}).noaa || wxStatus;
        rebuildWxOverlay();
      });
    }
    rebuildWxOverlay();

    // Warning list panel
    var warnPanel = document.createElement("div");
    warnPanel.id = "openusd-warn-panel";
    warnPanel.className = "warn-panel";
    warnPanel.innerHTML =
      '<div class="warn-panel-title">WARNINGS <span id="warnBadge" class="warn-badge">0</span></div>' +
      '<div class="warn-panel-meta" id="warnMeta">minima —</div>' +
      '<div class="warn-panel-list" id="warnList">awaiting live tracks…</div>';
    container.appendChild(warnPanel);

    // Airport ring
    var ring = new THREE.Mesh(
      new THREE.RingGeometry(0.35, 0.55, 32),
      new THREE.MeshBasicMaterial({
        color: 0xf5c518,
        transparent: true,
        opacity: 0.85,
        side: THREE.DoubleSide,
      })
    );
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.05;
    scene.add(ring);

    var planeTex = makePlaneTextureFallback(THREE);
    var planeTexHeavy = planeTex;
    var planeTexLight = planeTex;
    var acGroup = new THREE.Group();
    scene.add(acGroup);
    var meshByIcao = {};
    var MAX_AC = 400;
    // Strobe-class membrane poll — c₄/uum8d packets are cheap; paint must stay hot.
    // 700ms balances ADS-B cell load vs lightning scene reproject. Override: ?poll_ms=
    var POLL_MS = (function () {
      try {
        var q = new URLSearchParams(location.search).get("poll_ms");
        if (q != null && q !== "") {
          var n = parseInt(q, 10);
          if (isFinite(n) && n >= 200 && n <= 15000) return n;
        }
      } catch (_) {}
      return 700;
    })();

    // Hot-load Affine SVG sprites (assets/sprites/*.svg)
    loadSpriteTexture(THREE, "assets/sprites/aircraft.svg", makePlaneTextureFallback).then(
      function (tex) {
        planeTex = tex;
        Object.keys(meshByIcao).forEach(function (k) {
          var m = meshByIcao[k];
          if (m && m.material && (!m.userData.variant || m.userData.variant === "jet")) {
            m.material.map = tex;
            m.material.needsUpdate = true;
          }
        });
      }
    );
    loadSpriteTexture(THREE, "assets/sprites/aircraft-heavy.svg", makePlaneTextureFallback).then(
      function (tex) {
        planeTexHeavy = tex;
      }
    );
    loadSpriteTexture(THREE, "assets/sprites/aircraft-light.svg", makePlaneTextureFallback).then(
      function (tex) {
        planeTexLight = tex;
      }
    );

    var raf = 0;
    var strobeTick = 0;
    var membraneTicks = 0;
    var liveRefreshTicks = 0;
    var aircraftCount = 0;
    var lastFetchMs = 0;
    var trackError = "";
    var disposed = false;
    var t0 = performance.now();
    var lastHudMs = 0;

    function applyOrtho() {
      var half = orthoHalf / zoomLevel;
      var aspect = (container.clientWidth || w) / (container.clientHeight || h || 1);
      camera.left = -half * aspect;
      camera.right = half * aspect;
      camera.top = half;
      camera.bottom = -half;
      camera.position.x = panX;
      camera.position.z = panZ;
      camera.lookAt(panX, 0, panZ);
      camera.updateProjectionMatrix();
    }

    function screenToWorld(clientX, clientY) {
      var rect = renderer.domElement.getBoundingClientRect();
      var ndcX = ((clientX - rect.left) / rect.width) * 2 - 1;
      var ndcY = -(((clientY - rect.top) / rect.height) * 2 - 1);
      var half = orthoHalf / zoomLevel;
      var aspect = rect.width / (rect.height || 1);
      return {
        x: panX + ndcX * half * aspect,
        z: panZ - ndcY * half,
      };
    }

    function zoomAt(clientX, clientY, factor) {
      var before = screenToWorld(clientX, clientY);
      var next = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, targetZoom * factor));
      targetZoom = next;
      // Keep point under cursor stable after zoom settles (adjust target pan)
      var afterZoom = next;
      var half = orthoHalf / afterZoom;
      var rect = renderer.domElement.getBoundingClientRect();
      var ndcX = ((clientX - rect.left) / rect.width) * 2 - 1;
      var ndcY = -(((clientY - rect.top) / rect.height) * 2 - 1);
      var aspect = rect.width / (rect.height || 1);
      targetPanX = before.x - ndcX * half * aspect;
      targetPanZ = before.z + ndcY * half;
    }

    function disposeMapMesh(mesh) {
      if (!mesh) return;
      scene.remove(mesh);
      if (mesh.userData && typeof mesh.userData.dispose === "function") {
        mesh.userData.dispose();
        return;
      }
      if (mesh.material && mesh.material.map) mesh.material.map.dispose();
      if (mesh.material) mesh.material.dispose();
      if (mesh.geometry) mesh.geometry.dispose();
    }

    function transitionManifoldBand(nextBand) {
      if (!nextBand || nextBand.id === manifoldStageId) return;
      currentBand = nextBand;
      manifoldStageId = nextBand.id;
      pendingSkin = nextBand.skin;
      if (MS && MS.applySkin) MS.applySkin(nextBand.skin);
      // Swap procedural LOD grid (depth/LOD on constraints — not texture mipmaps)
      disposeMapMesh(mapMeshPrev);
      mapMeshPrev = null;
      disposeMapMesh(mapMesh);
      mapMesh = buildMapMesh(nextBand);
      scene.add(mapMesh);
      skinCrossfade = 1;
      container.setAttribute("data-manifold-band", manifoldStageId);
      container.setAttribute("data-walk-mode", nextBand.walkMode ? "1" : "0");
      container.setAttribute("data-procedural-c4", "1");
      hud.setAttribute("data-manifold-band", manifoldStageId);
      hud.setAttribute("data-walk-mode", nextBand.walkMode ? "1" : "0");
      var bandEl = document.getElementById("mapBandHud");
      if (bandEl) bandEl.textContent = nextBand.id + " · " + nextBand.label;
      rebuildWxOverlay();
      if (rawTrackCache.length) upsertAircraft(rawTrackCache);
      var needDist = nextBand.fetchDistNm || 100;
      if (Math.abs(needDist - lastFetchDist) > 40) refreshTracks(true);
      syncTwinChrome();
    }

    function syncManifoldFromZoom() {
      if (!MS) return;
      var next = MS.bandForZoom(zoomLevel);
      if (next.id !== manifoldStageId) transitionManifoldBand(next);
      else syncTwinChrome();
    }

    function setManifoldView(bandId, opts) {
      opts = opts || {};
      var id = String(bandId || "").toUpperCase();
      if (id === "AIRPORT" || id === "WALK") id = "AIRPORT_WALK";
      var z =
        MS && MS.zoomForBand
          ? MS.zoomForBand(id)
          : id === "AIRPORT_WALK"
            ? 4.2
            : id === "METRO"
              ? 2.0
              : id === "REGIONAL"
                ? 0.75
                : 0.22;
      targetZoom = z;
      if (opts.snap) zoomLevel = z;
      targetPanX = 0;
      targetPanZ = 0;
      var next = MS && MS.bandById ? MS.bandById(id) : MS ? MS.bandForZoom(z) : null;
      if (next) transitionManifoldBand(next);
      syncTwinChrome();
      refreshTracks(true);
    }

    function setAirport(icao) {
      icao = (icao || "KJFK").toUpperCase();
      if (!AIRPORTS[icao]) return;
      focusIcao = icao;
      ap = AIRPORTS[icao];
      centerLat = ap.lat;
      centerLon = ap.lon;
      viewSpanDeg = ap.zoom;
      orthoHalf = (viewSpanDeg * mapScale) / 2.4;
      // Re-enter at METRO for airport focus (user can change UUM-8D view)
      targetZoom = 1.45;
      zoomLevel = 1.45;
      targetPanX = 0;
      targetPanZ = 0;
      panX = 0;
      panZ = 0;
      var band = MS ? MS.bandForZoom(zoomLevel) : currentBand;
      disposeMapMesh(mapMeshPrev);
      mapMeshPrev = null;
      disposeMapMesh(mapMesh);
      currentBand = band;
      manifoldStageId = band.id;
      if (MS && MS.applySkin) MS.applySkin(band.skin);
      mapMesh = buildMapMesh(band);
      scene.add(mapMesh);
      skinCrossfade = 1;
      rebuildWxOverlay();
      applyOrtho();
      hud.setAttribute("data-focus-icao", focusIcao);
      hud.setAttribute("data-manifold-band", manifoldStageId);
      container.setAttribute("data-manifold-band", manifoldStageId);
      container.setAttribute("data-focus-icao", focusIcao);
      var sub = document.getElementById("mapSubTitle");
      if (sub)
        sub.textContent =
          band.label + " · " + focusIcao + " · " + ap.name + " · live ADS-B";
      var bandEl = document.getElementById("mapBandHud");
      if (bandEl) bandEl.textContent = band.id + " · " + band.label + " · UUM-8D";
      syncTwinChrome();
      refreshTracks(true);
    }

    function clearWarnLines() {
      while (warnLineGroup.children.length) {
        var ln = warnLineGroup.children[0];
        warnLineGroup.remove(ln);
        if (ln.geometry) ln.geometry.dispose();
        if (ln.material) ln.material.dispose();
      }
    }

    function severityColor(sev) {
      if (sev === "CRITICAL") return 0xff3344;
      if (sev === "HIGH") return 0xff7a2e;
      if (sev === "MEDIUM") return 0xe0a35c;
      return 0x8aa0ad;
    }

    function renderWarnings(filteredRows) {
      // Prefer Swift OS projection warnings when already stamped this refresh.
      if (!(warningState && warningState.source === "SWIFT_UUM8D_ZOOM")) {
        if (!TW || !TW.evaluate) {
          warningState = { warnings: [], minima: null, pairCount: 0 };
        } else {
          warningState = TW.evaluate(filteredRows, manifoldStageId, { maxWarnings: 30 });
        }
      }
      clearWarnLines();
      (warningState.warnings || []).forEach(function (w) {
        if (w.kind !== "SEPARATION" || w.latB == null) return;
        var a = lonLatToWorld(w.latA, w.lonA, centerLat, centerLon, mapScale);
        var b = lonLatToWorld(w.latB, w.lonB, centerLat, centerLon, mapScale);
        var geo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(a.x, 0.35, a.z),
          new THREE.Vector3(b.x, 0.35, b.z),
        ]);
        var mat = new THREE.LineBasicMaterial({
          color: severityColor(w.severity),
          transparent: true,
          opacity: w.severity === "CRITICAL" ? 0.95 : 0.75,
        });
        warnLineGroup.add(new THREE.Line(geo, mat));
      });
      var listEl = document.getElementById("warnList");
      var badge = document.getElementById("warnBadge");
      var meta = document.getElementById("warnMeta");
      var n = (warningState.warnings || []).length;
      if (badge) {
        badge.textContent = String(n);
        badge.className =
          "warn-badge" +
          (n === 0
            ? ""
            : warningState.warnings[0].severity === "CRITICAL"
              ? " sev-critical"
              : warningState.warnings[0].severity === "HIGH"
                ? " sev-high"
                : " sev-med");
      }
      if (meta) {
        if (warningState.minima && warningState.minima.lateralNm != null) {
          meta.textContent =
            manifoldStageId +
            " minima lat≥" +
            warningState.minima.lateralNm +
            "nm vert≥" +
            warningState.minima.verticalFt +
            "ft · " +
            (warningState.minima.label || "enroute");
        } else if (TW && TW.minimaForBand) {
          var jm = TW.minimaForBand(manifoldStageId);
          meta.textContent =
            manifoldStageId +
            " minima lat≥" +
            jm.lateralNm +
            "nm vert≥" +
            jm.verticalFt +
            "ft · " +
            (jm.label || "enroute");
        }
      }
      if (listEl) {
        if (!n) {
          listEl.textContent = "no separation breaches at this LOD";
        } else {
          listEl.innerHTML = warningState.warnings
            .slice(0, 12)
            .map(function (w) {
              return (
                '<div class="warn-row sev-' +
                String(w.severity || "LOW").toLowerCase() +
                '"><span class="sev">' +
                w.severity +
                "</span> " +
                (w.message || w.kind) +
                "</div>"
              );
            })
            .join("");
        }
      }
      hud.setAttribute("data-warn-count", String(n));
      hud.setAttribute(
        "data-warn-top",
        n ? warningState.warnings[0].severity + ":" + warningState.warnings[0].kind : ""
      );
      container.setAttribute("data-warn-count", String(n));
    }

    function viewHalfWorld() {
      return orthoHalf / Math.max(ZOOM_MIN, zoomLevel);
    }

    function aircraftWorldScale(altFt, variant) {
      // FR24-class: sprites must remain readable at every manifold band.
      // Prior bug: fixed ~1.5 world units → ~2px at HEMISPHERE (invisible).
      var vh = viewHalfWorld();
      var hPx = container.clientHeight || h || 900;
      var worldPerPx = (2 * vh) / Math.max(1, hPx);
      var targetPx =
        currentBand.id === "HEMISPHERE"
          ? 18
          : currentBand.id === "REGIONAL"
            ? 20
            : currentBand.id === "METRO"
              ? 24
              : 28;
      var spriteMul = currentBand.spriteScale != null ? currentBand.spriteScale : 1;
      var alt = Number(altFt) || 0;
      var altMul = alt < 100 ? 0.92 : alt < 10000 ? 1.0 : 1.12;
      var varMul = variant === "heavy" ? 1.15 : variant === "light" ? 0.88 : 1;
      var sc = worldPerPx * targetPx * spriteMul * altMul * varMul;
      var lo = vh * 0.014;
      var hi = vh * 0.06;
      if (sc < lo) sc = lo;
      if (sc > hi) sc = hi;
      return sc;
    }

    function upsertAircraft(rows) {
      rawTrackCache = rows || [];
      var seen = {};
      // When Swift already thinned + re-rooted, do not re-filter in JS.
      var filtered =
        useLocalC4 || (rawTrackCache[0] && rawTrackCache[0]._swiftProjected)
          ? (rawTrackCache || []).slice(0, MAX_AC)
          : MS
            ? MS.filterTracksForBand(rawTrackCache, currentBand, centerLat, centerLon)
            : (rawTrackCache || []).slice(0, MAX_AC);
      lodTrackCount = filtered.length;
      var list = filtered.slice(0, MAX_AC);
      // Local milli → world: relative re-root only (never absolute milli-deg as world).
      var localScale = mapScale / 1000;
      list.forEach(function (a) {
        var icao = String(a.icao || "").toLowerCase();
        if (!icao) return;
        var hasLL = a.lat != null && a.lon != null && isFinite(Number(a.lat)) && isFinite(Number(a.lon));
        if (!hasLL && !(useLocalC4 && a.local_x_milli != null && a.local_z_milli != null)) return;
        seen[icao] = true;
        var ll;
        // Prefer lat/lon always — local_* from membrane are often absolute milli-deg
        // (lon_milli / lat_milli), which placed aircraft thousands of units off-screen.
        if (hasLL) {
          ll = lonLatToWorld(Number(a.lat), Number(a.lon), centerLat, centerLon, mapScale);
        } else {
          var lx = Number(a.local_x_milli);
          var lz = Number(a.local_z_milli);
          // Absolute milli-deg heuristic: |coord| > 5° from origin → treat as lon/lat milli
          if (Math.abs(lx) > 5000 || Math.abs(lz) > 5000) {
            ll = lonLatToWorld(lz / 1000, lx / 1000, centerLat, centerLon, mapScale);
          } else {
            ll = { x: lx * localScale, z: -lz * localScale };
          }
        }
        var mesh = meshByIcao[icao];
        var alt0 = Number(a.alt_baro_ft) || 0;
        var gs0 = Number(a.gs_kt) || 0;
        var variant = "jet";
        if (alt0 < 80 && gs0 < 80) variant = "light";
        else if (alt0 > 28000 || gs0 > 420) variant = "heavy";
        if (!mesh) {
          var map =
            variant === "light"
              ? planeTexLight || planeTex
              : variant === "heavy"
                ? planeTexHeavy || planeTex
                : planeTex;
          // Yellow heading sprite (Sprite) — Cone fallback if texture missing.
          if (!map) {
            var cone = new THREE.ConeGeometry(0.35, 1.1, 3);
            var cmat = new THREE.MeshBasicMaterial({ color: 0xf5c518 });
            mesh = new THREE.Mesh(cone, cmat);
            mesh.rotation.x = Math.PI / 2;
          } else {
            var mat = new THREE.SpriteMaterial({
              map: map,
              transparent: true,
              depthWrite: false,
              depthTest: true,
              color: 0xffffff,
              sizeAttenuation: true,
            });
            mesh = new THREE.Sprite(mat);
            mesh.center.set(0.5, 0.5);
          }
          mesh.userData.icao = icao;
          mesh.userData.variant = variant;
          mesh.renderOrder = 10;
          acGroup.add(mesh);
          meshByIcao[icao] = mesh;
        } else if (mesh.userData.variant !== variant && mesh.material && mesh.material.map) {
          mesh.userData.variant = variant;
          mesh.material.map =
            variant === "light"
              ? planeTexLight || planeTex
              : variant === "heavy"
                ? planeTexHeavy || planeTex
                : planeTex;
          mesh.material.needsUpdate = true;
        }
        var alpha = mesh.userData.seeded ? 0.45 : 1;
        mesh.userData.seeded = true;
        mesh.position.x += (ll.x - mesh.position.x) * alpha;
        mesh.position.z += (ll.z - mesh.position.z) * alpha;
        mesh.position.y = 0.35 + (Number(a.zoom_depth) || 0) * 0.02;
        var track = Number(a.track_deg) || 0;
        if (mesh.material && mesh.material.rotation != null) {
          mesh.material.rotation = (-track * Math.PI) / 180;
        } else {
          mesh.rotation.z = (-track * Math.PI) / 180;
        }
        mesh.userData.callsign = a.callsign || icao;
        mesh.userData.alt = a.alt_baro_ft || 0;
        mesh.userData.gs = a.gs_kt || 0;
        mesh.userData.track = track;
        mesh.userData.density = a.density_milli || 0;
        mesh.userData.zoomDepth = a.zoom_depth || 0;
        var sc = aircraftWorldScale(alt0, variant);
        mesh.userData.baseScale = sc;
        if (mesh.isSprite) mesh.scale.set(sc, sc, 1);
        else mesh.scale.set(sc * 0.55, sc * 0.55, sc * 0.55);
      });
      Object.keys(meshByIcao).forEach(function (icao) {
        if (!seen[icao]) {
          acGroup.remove(meshByIcao[icao]);
          if (meshByIcao[icao].material) meshByIcao[icao].material.dispose();
          delete meshByIcao[icao];
        }
      });
      aircraftCount = Object.keys(meshByIcao).length;
      renderWarnings(list);
    }

    function rowsFromSwiftZoomPacket(pkt) {
      var rows = pkt && pkt.viewport_aircraft ? pkt.viewport_aircraft : [];
      return rows.map(function (a) {
        return {
          icao: a.icao,
          callsign: a.callsign,
          lat: Number(a.lat_milli_deg) / 1000,
          lon: Number(a.lon_milli_deg) / 1000,
          alt_baro_ft: Number(a.alt_baro_ft) || 0,
          track_deg: Number(a.track_deg_milli || a.heading_milli_deg) / 1000,
          gs_kt: Number(a.gs_kt_milli || a.velocity_milli_kt) / 1000,
          density_milli: Number(a.density_milli) || 0,
          zoom_depth: Number(a.zoom_depth) || 0,
          local_x_milli: a.local_x_milli,
          local_y_milli: a.local_y_milli,
          local_z_milli: a.local_z_milli,
          _swiftProjected: true,
        };
      });
    }

    function warningsFromSwiftZoomPacket(pkt) {
      var list = (pkt && pkt.warnings) || [];
      return {
        warnings: list.map(function (w) {
          if (w.kind === "TERRAIN_INTERSECT" || w.elevation_limit_ft != null) {
            return {
              severity: w.severity || "MEDIUM",
              kind: "TERRAIN_INTERSECT",
              icao_a: w.icao,
              callsign_a: w.callsign,
              vertical_ft: Number(w.alt_baro_ft) || 0,
              floor_ft: Number(w.elevation_limit_ft) || 0,
              message:
                (w.severity || "?") +
                " TERRAIN " +
                (w.callsign || w.icao) +
                " alt=" +
                (w.alt_baro_ft || "?") +
                "ft floor=" +
                (w.elevation_limit_ft || "?") +
                "ft",
            };
          }
          return {
            severity: w.severity || "LOW",
            kind: w.lateral_breach && w.vertical_breach ? "SEPARATION" : "NEAR",
            icao_a: w.icao_a,
            icao_b: w.icao_b,
            callsign_a: w.callsign_a,
            callsign_b: w.callsign_b,
            lateral_nm: (Number(w.lateral_milli_nm) || 0) / 1000,
            vertical_ft: Number(w.vertical_ft) || 0,
            message:
              (w.severity || "?") +
              " " +
              (w.callsign_a || w.icao_a) +
              "↔" +
              (w.callsign_b || w.icao_b),
          };
        }),
        minima: (function () {
          var m = pkt.minima || {};
          var latNm =
            m.lateralNm != null
              ? Number(m.lateralNm)
              : m.lateral_milli_nm != null
                ? Number(m.lateral_milli_nm) / 1000
                : null;
          var vert =
            m.verticalFt != null
              ? Number(m.verticalFt)
              : m.vertical_ft != null
                ? Number(m.vertical_ft)
                : null;
          if (latNm == null && vert == null) return null;
          return {
            lateralNm: latNm != null ? latNm : 5,
            verticalFt: vert != null ? vert : 1000,
            label: m.label || m.band || "enroute",
            band: m.band || null,
          };
        })(),
        pairCount: list.length,
        source: "SWIFT_UUM8D_ZOOM",
        boundaryCount: (pkt.globe_constraints && pkt.globe_constraints.boundary_count) || pkt.boundary_count || 0,
        terrainHitCount: (pkt.globe_constraints && pkt.globe_constraints.terrain_hit_count) || pkt.terrain_hit_count || 0,
      };
    }

    var boundaryGroup = new THREE.Group();
    boundaryGroup.name = "uum8d-structural-boundaries";
    scene.add(boundaryGroup);
    var elevFloorMesh = null;
    var convectiveGroup = new THREE.Group();
    convectiveGroup.name = "study09-convective-bond";
    scene.add(convectiveGroup);
    var confidenceHorizonMesh = null;

    function clearBoundaryGroup() {
      while (boundaryGroup.children.length) {
        var ch = boundaryGroup.children[0];
        boundaryGroup.remove(ch);
        if (ch.geometry) ch.geometry.dispose();
        if (ch.material) ch.material.dispose();
      }
      if (elevFloorMesh) {
        scene.remove(elevFloorMesh);
        if (elevFloorMesh.geometry) elevFloorMesh.geometry.dispose();
        if (elevFloorMesh.material) elevFloorMesh.material.dispose();
        elevFloorMesh = null;
      }
    }

    function clearConvectiveGroup() {
      while (convectiveGroup.children.length) {
        var ch = convectiveGroup.children[0];
        convectiveGroup.remove(ch);
        if (ch.geometry) ch.geometry.dispose();
        if (ch.material) ch.material.dispose();
      }
      if (confidenceHorizonMesh) {
        scene.remove(confidenceHorizonMesh);
        if (confidenceHorizonMesh.geometry) confidenceHorizonMesh.geometry.dispose();
        if (confidenceHorizonMesh.material) confidenceHorizonMesh.material.dispose();
        confidenceHorizonMesh = null;
      }
    }

    function latLonToWorld(lat, lon) {
      // Same equirectangular local frame as aircraft (mapScale) — not nm.
      return lonLatToWorld(lat, lon, centerLat, centerLon, mapScale);
    }

    function applyGlobeConstraints(pkt) {
      var globe = pkt && pkt.globe_constraints;
      if ((!globe || !globe.boundaries || !globe.boundaries.length) && pkt && pkt.boundaries) {
        globe = pkt;
      }
      if (!globe || !globe.boundaries || !globe.boundaries.length) {
        globe = surfaceTwinStub(focusIcao);
        container.setAttribute("data-globe-source", "SURFACE_TWIN_STUB");
      } else {
        container.setAttribute(
          "data-globe-source",
          globe.proven || "SWIFT_UUM8D_BOUNDARY_ENGINE"
        );
      }
      if (!globe || !globe.boundaries) {
        container.setAttribute("data-globe-boundaries", "0");
        return;
      }
      lastGlobePkt = globe;
      clearBoundaryGroup();
      var colors = {
        fir: 0x3d7ea6,
        airport: 0xf5c518,
        runway: 0xffe08a,
        coastline: 0x4ecfbf,
        airspace: 0x6b8cae,
      };
      var yLift = {
        fir: 0.04,
        coastline: 0.06,
        airspace: 0.05,
        airport: 0.08,
        runway: 0.1,
      };
      (globe.boundaries || []).forEach(function (b) {
        var curve = b.curve_milli || [];
        if (curve.length < 2) {
          // box from AABB
          curve = [
            [b.min_lat_milli, b.min_lon_milli],
            [b.min_lat_milli, b.max_lon_milli],
            [b.max_lat_milli, b.max_lon_milli],
            [b.max_lat_milli, b.min_lon_milli],
            [b.min_lat_milli, b.min_lon_milli],
          ];
        }
        var pts = [];
        for (var i = 0; i < curve.length; i++) {
          var lat = Number(curve[i][0]) / 1000;
          var lon = Number(curve[i][1]) / 1000;
          var w = latLonToWorld(lat, lon);
          pts.push(new THREE.Vector3(w.x, yLift[b.kind] || 0.05, w.z));
        }
        if (pts.length < 2) return;
        var geom = new THREE.BufferGeometry().setFromPoints(pts);
        var mat = new THREE.LineBasicMaterial({
          color: colors[b.kind] || 0x88aacc,
          transparent: true,
          opacity:
            b.kind === "runway" || b.kind === "airport"
              ? 0.98
              : b.kind === "coastline"
                ? 0.85
                : b.kind === "fir"
                  ? 0.7
                  : 0.55,
          linewidth: 1,
        });
        var line = new THREE.Line(geom, mat);
        line.userData.structural = true;
        line.userData.kind = b.kind;
        boundaryGroup.add(line);
      });
      // Elevation floor cue — procedural plane tinted by queried floor (not JPEG).
      var elevFt =
        globe.elevation_query_ft != null
          ? Number(globe.elevation_query_ft)
          : null;
      if (elevFt != null && isFinite(elevFt)) {
        var elevY = Math.max(0.02, elevFt / 12000);
        var plane = new THREE.Mesh(
          new THREE.PlaneGeometry(18, 18),
          new THREE.MeshBasicMaterial({
            color: elevFt <= 20 ? 0x1a3a38 : 0x2a4030,
            transparent: true,
            opacity: 0.22,
            side: THREE.DoubleSide,
            depthWrite: false,
          })
        );
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = elevY;
        plane.userData.elevationFloor = true;
        scene.add(plane);
        elevFloorMesh = plane;
        container.setAttribute("data-elevation-floor-ft", String(elevFt));
      }
      container.setAttribute("data-globe-boundaries", String(globe.boundary_count || globe.boundaries.length));
      container.setAttribute("data-structural-skins", "1");
      hud.setAttribute("data-boundary-count", String(globe.boundary_count || globe.boundaries.length));
      hud.setAttribute("data-terrain-hits", String(globe.terrain_hit_count || 0));
    }

    /** Study 09 — fourth globe layer. REFUSED ≠ clear sky. Never paint void as calm. */
    function applyConvectiveBond(pkt) {
      var bond = pkt && pkt.convective_bond;
      clearConvectiveGroup();
      if (!bond || !bond.cells) {
        container.setAttribute("data-study09", "0");
        return;
      }
      var termColors = {
        CALORIE: 0x3ecf8e,
        CURE: 0xe0a35c,
        REFUSED: 0x8b3a5c, // distinct void — never calm ocean blue
      };
      var lead = String(bond.lead_band || "");
      var allowCells =
        lead.indexOf("0_90") >= 0 || lead === "LEAD_0_90_MIN_CELLS";
      var allowMeso =
        allowCells ||
        lead.indexOf("90M_6H") >= 0 ||
        lead === "LEAD_90M_6H_MESO";
      (bond.cells || []).forEach(function (c) {
        var cls = String(c.object_class || "");
        if (cls === "TRAFFIC_PROBE_CELL" && !allowCells) return;
        if (cls === "TRAFFIC_PROBE_MESO" && !allowMeso) return;
        var lat = Number(c.lat_milli) / 1000;
        var lon = Number(c.lon_milli) / 1000;
        if (!isFinite(lat) || !isFinite(lon)) return;
        var w = latLonToWorld(lat, lon);
        var term = String(c.terminal || "CALORIE");
        var color = termColors[term] || 0x88aacc;
        if (cls === "CONFIDENCE_HORIZON") {
          var r = Math.max(2, Number(bond.confidence_horizon_min || 90) / 45);
          var ring = new THREE.Mesh(
            new THREE.RingGeometry(r * 0.92, r, 48),
            new THREE.MeshBasicMaterial({
              color: 0xf5c518,
              transparent: true,
              opacity: 0.35,
              side: THREE.DoubleSide,
              depthWrite: false,
            })
          );
          ring.rotation.x = -Math.PI / 2;
          ring.position.set(w.x, 0.12, w.z);
          ring.userData.confidenceHorizon = true;
          scene.add(ring);
          confidenceHorizonMesh = ring;
          return;
        }
        if (term === "REFUSED" || c.radar_void || c.geo_refused_polar) {
          // Observation void hatch — must not read as clear/calm land.
          var voidMesh = new THREE.Mesh(
            new THREE.PlaneGeometry(1.6, 1.6),
            new THREE.MeshBasicMaterial({
              color: termColors.REFUSED,
              transparent: true,
              opacity: 0.45,
              side: THREE.DoubleSide,
              depthWrite: false,
            })
          );
          voidMesh.rotation.x = -Math.PI / 2;
          voidMesh.position.set(w.x, 0.08, w.z);
          voidMesh.userData.study09 = true;
          voidMesh.userData.terminal = "REFUSED";
          convectiveGroup.add(voidMesh);
          return;
        }
        var marker = new THREE.Mesh(
          new THREE.SphereGeometry(0.22, 10, 10),
          new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: cls.indexOf("PROBE") >= 0 ? 0.85 : 0.55,
          })
        );
        marker.position.set(w.x, 0.35, w.z);
        marker.userData.study09 = true;
        marker.userData.terminal = term;
        marker.userData.objectClass = cls;
        convectiveGroup.add(marker);
      });
      // Solar heating cue on HUD (integer milli from Swift — no float seal).
      var solarMilli = bond.solar_heating_cue_milli;
      if (solarMilli != null) {
        hud.setAttribute("data-solar-heating-milli", String(solarMilli));
        container.style.setProperty(
          "--study09-solar-heat",
          String(Math.max(0, Math.min(100, (Number(solarMilli) + 1000) / 20))) + "%"
        );
      }
      var counts = bond.terminal_counts || {};
      container.setAttribute("data-study09", "1");
      container.setAttribute("data-lead-band", lead);
      container.setAttribute(
        "data-confidence-horizon-min",
        String(bond.confidence_horizon_min || 0)
      );
      container.setAttribute("data-refused-count", String(counts.REFUSED || bond.refused_count || 0));
      hud.setAttribute("data-study09", "1");
      hud.setAttribute("data-lead-band", lead);
      hud.setAttribute(
        "data-convective-refused",
        String(counts.REFUSED || bond.refused_count || 0)
      );
      hud.setAttribute(
        "data-traffic-probes",
        String(bond.traffic_probe_count || 0)
      );
    }

    var lastPacketToPaintMs = 0;
    var lastFetchMsWall = 0;
    var lastSwiftGenMs = 0;

    function markPacketPaint(fetchStartMs, stitchStartMs, pkt) {
      // fetchMs = HTTPS RTT; stitchMs = pure scene reproject after packet body in hand.
      var now = performance.now();
      lastFetchMsWall = stitchStartMs - fetchStartMs;
      lastPacketToPaintMs = now - stitchStartMs;
      lastSwiftGenMs = Number(pkt && pkt.latency_ns ? pkt.latency_ns : 0) / 1e6;
      hud.setAttribute("data-c4-fetch-ms", lastFetchMsWall.toFixed(1));
      hud.setAttribute("data-c4-paint-ms", lastPacketToPaintMs.toFixed(1));
      hud.setAttribute("data-swift-gen-ms", lastSwiftGenMs.toFixed(1));
      container.setAttribute("data-c4-fetch-ms", lastFetchMsWall.toFixed(1));
      container.setAttribute("data-c4-paint-ms", lastPacketToPaintMs.toFixed(1));
      container.setAttribute("data-swift-gen-ms", lastSwiftGenMs.toFixed(1));
      container.setAttribute("data-c4-stitch", "1");
    }

    async function refreshTracks(force) {
      if (disposed) return;
      if (!global.UUM8DShell) {
        trackError = "UUM8DShell missing";
        return;
      }
      var fetchStartMs = performance.now();
      try {
        // 1) Swift UUM8D zoom — embeds c₄ + globe structural skins + terrain
        if (global.UUM8DShell.fetchUUM8DZoomProjection) {
          try {
            var zoomPkt = await global.UUM8DShell.fetchUUM8DZoomProjection({
              icao: focusIcao,
              zoom: zoomLevel,
            });
            if (
              zoomPkt &&
              zoomPkt.proven === "AIRSPACE_UUM8D_ZOOM_PROJECTION_PROVEN" &&
              (zoomPkt.viewport_aircraft || zoomPkt.aircraft)
            ) {
              liveRefreshTicks += 1;
              trackError = "";
              if (zoomPkt.manifold_band) {
                manifoldStageId = String(zoomPkt.manifold_band);
                hud.setAttribute("data-manifold-band", manifoldStageId);
              }
              if (zoomPkt.reroot) {
                rerootState.active = !!zoomPkt.reroot.active;
                rerootState.zoomDepth = Number(zoomPkt.reroot.zoom_depth) || 0;
                useLocalC4 = rerootState.active;
                hud.setAttribute("data-reroot", rerootState.active ? "1" : "0");
                hud.setAttribute("data-zoom-depth", String(rerootState.zoomDepth));
              }
              warningState = warningsFromSwiftZoomPacket(zoomPkt);
              if (zoomPkt.weather && SW && SW.setMetarFromPacket) {
                lastWeatherPkt = SW.setMetarFromPacket(
                  zoomPkt.weather,
                  (SW.feedStatus() || {}).goes ||
                    "FOLLOW_ON_GOES_R_NOT_ON_ATC_PATH"
                );
                wxStatus = lastWeatherPkt.status || wxStatus;
                rebuildWxOverlay();
                updateTwinWxPanel();
              }
              if (zoomPkt.reroot) {
                lastC4ZoomDepth = Number(zoomPkt.reroot.zoom_depth) || 0;
              }
              if (zoomPkt.manifold_band) {
                // Swift band from same zoom_milli — HUD reflects c₄ coupling
                hud.setAttribute("data-swift-band", String(zoomPkt.manifold_band));
                container.setAttribute(
                  "data-swift-band",
                  String(zoomPkt.manifold_band)
                );
                hud.setAttribute(
                  "data-c4-zoom-milli",
                  String(
                    (zoomPkt.reroot && zoomPkt.reroot.zoom_milli) ||
                      Math.round(zoomLevel * 1000)
                  )
                );
              }
              // Scene stitch = C⁴ reproject — apply aircraft + structural skins immediately.
              var stitch0 = performance.now();
              upsertAircraft(rowsFromSwiftZoomPacket(zoomPkt));
              applyGlobeConstraints(zoomPkt);
              applyConvectiveBond(zoomPkt);
              markPacketPaint(fetchStartMs, stitch0, zoomPkt);
              hud.setAttribute(
                "data-track-source",
                "swift_uum8d_zoom lat_ns=" + String(zoomPkt.latency_ns || 0)
              );
              hud.setAttribute("data-projection-source", "SWIFT_UUM8D_ZOOM");
              syncTwinChrome();
              updateTwinWxPanel();
              return;
            }
          } catch (_) {
            /* fall through */
          }
        }
        // 2) c₄ constraint firehose (Primvar injector)
        if (global.UUM8DShell.fetchC4Constraints) {
          try {
            var c4 = await global.UUM8DShell.fetchC4Constraints({
              icao: focusIcao,
              zoom: zoomLevel,
            });
            if (
              c4 &&
              c4.proven === "ATC_C4_CONSTRAINT_STREAM_PROVEN" &&
              (c4.viewport_aircraft || c4.constraints)
            ) {
              liveRefreshTicks += 1;
              trackError = "";
              if (c4.manifold_band) {
                manifoldStageId = String(c4.manifold_band);
                hud.setAttribute("data-manifold-band", manifoldStageId);
              }
              if (c4.reroot) {
                rerootState.active = !!c4.reroot.active;
                rerootState.zoomDepth = Number(c4.reroot.zoom_depth) || 0;
                useLocalC4 = rerootState.active;
                hud.setAttribute("data-reroot", rerootState.active ? "1" : "0");
                hud.setAttribute("data-zoom-depth", String(rerootState.zoomDepth));
                container.setAttribute("data-reroot", rerootState.active ? "1" : "0");
              }
              warningState = { warnings: [], minima: null, pairCount: 0, source: "C4" };
              var stitch1 = performance.now();
              upsertAircraft(rowsFromSwiftZoomPacket(c4));
              markPacketPaint(fetchStartMs, stitch1, c4);
              hud.setAttribute(
                "data-track-source",
                "swift_c4_constraints lat_ns=" + String(c4.latency_ns || 0)
              );
              hud.setAttribute("data-projection-source", "SWIFT_C4_CONSTRAINTS");
              return;
            }
          } catch (_) {
            /* fall through */
          }
        }
        useLocalC4 = false;
        if (!global.UUM8DShell.fetchLiveTracks) {
          trackError = "fetchLiveTracks missing";
          return;
        }
        var dist = currentBand.fetchDistNm || 100;
        lastFetchDist = dist;
        var payload = await global.UUM8DShell.fetchLiveTracks({
          icao: focusIcao,
          dist: dist,
          force: !!force,
        });
        liveRefreshTicks += 1;
        trackError = payload.error || "";
        upsertAircraft(payload.aircraft || []);
        hud.setAttribute("data-track-source", payload.source || "adsb.lol_https_v2");
        hud.setAttribute("data-projection-source", "FALLBACK_TRACKS_JSON");
      } catch (e) {
        trackError = String(e);
      }
    }

    function updateHud(elapsedMs) {
      if (elapsedMs - lastHudMs < 80 && strobeTick % 6 !== 0) return;
      lastHudMs = elapsedMs;
      var clockMs = Math.floor(elapsedMs);
      var zr = MS && MS.zoomRational ? MS.zoomRational(zoomLevel) : { text: zoomLevel.toFixed(2) };
      hud.setAttribute("data-strobe-tick", String(strobeTick));
      hud.setAttribute("data-clock-ms", String(clockMs));
      hud.setAttribute("data-membrane-ticks", String(membraneTicks));
      hud.setAttribute("data-live-refresh", String(liveRefreshTicks));
      hud.setAttribute("data-aircraft", String(aircraftCount));
      hud.setAttribute("data-lod-tracks", String(lodTrackCount));
      hud.setAttribute("data-scene-mode", "atc-map");
      hud.setAttribute("data-focus-icao", focusIcao);
      hud.setAttribute("data-zoom", zoomLevel.toFixed(3));
      hud.setAttribute("data-zoom-rational", zr.text || "");
      hud.setAttribute("data-manifold-band", manifoldStageId);
      hud.setAttribute("data-walk-mode", currentBand.walkMode ? "1" : "0");
      hud.setAttribute("data-wx-status", wxStatus);
      hud.setAttribute(
        "data-warn-count",
        String((warningState.warnings || []).length)
      );
      if (wxMeta && wxMeta.solar) {
        hud.setAttribute("data-solar-elev", wxMeta.solar.elevationDeg.toFixed(1));
        hud.setAttribute(
          "data-solar-phase",
          wxMeta.solar.isDay ? "DAY" : wxMeta.solar.twilight ? "TWILIGHT" : "NIGHT"
        );
      }
      if (trackError) hud.setAttribute("data-track-error", trackError);
      else hud.removeAttribute("data-track-error");
      var wn = (warningState.warnings || []).length;
      hud.textContent =
        "band=" +
        manifoldStageId +
        " (" +
        currentBand.label +
        ") focus=" +
        focusIcao +
        " zoom=" +
        zoomLevel.toFixed(3) +
        " (" +
        (zr.text || "") +
        ") lod_ac=" +
        lodTrackCount +
        " shown=" +
        aircraftCount +
        " warn=" +
        wn +
        " wx=" +
        wxStatus +
        " solar=" +
        (wxMeta && wxMeta.solar ? wxMeta.solar.elevationDeg.toFixed(1) + "°" : "?") +
        " strobe=" +
        strobeTick +
        " liveRefresh=" +
        liveRefreshTicks +
        " c4fetch=" +
        (lastFetchMsWall ? lastFetchMsWall.toFixed(0) + "ms" : "—") +
        " c4stitch=" +
        (lastPacketToPaintMs ? lastPacketToPaintMs.toFixed(1) + "ms" : "—") +
        " swiftGen=" +
        (lastSwiftGenMs ? lastSwiftGenMs.toFixed(0) + "ms" : "—") +
        (currentBand.walkMode ? " walk=1" : "") +
        (trackError ? " err=" + trackError.slice(0, 36) : "");
      var sub = document.getElementById("mapSubTitle");
      if (sub) {
        sub.textContent =
          currentBand.label +
          " · " +
          focusIcao +
          " · zoom " +
          zoomLevel.toFixed(2) +
          " · lod_ac=" +
          lodTrackCount +
          " · warn=" +
          wn +
          " · " +
          wxStatus;
      }
      var bandEl = document.getElementById("mapBandHud");
      if (bandEl) bandEl.textContent = manifoldStageId + " · " + currentBand.label;
      container.setAttribute("data-strobe-tick", String(strobeTick));
      container.setAttribute("data-clock-ms", String(clockMs));
      container.setAttribute("data-membrane-ticks", String(membraneTicks));
      container.setAttribute("data-live-refresh", String(liveRefreshTicks));
      container.setAttribute("data-aircraft", String(aircraftCount));
      container.setAttribute("data-lod-tracks", String(lodTrackCount));
      container.setAttribute("data-openusd-animating", strobeTick > 0 ? "1" : "0");
      container.setAttribute("data-scene-mode", "atc-map");
      container.setAttribute("data-focus-icao", focusIcao);
      container.setAttribute("data-manifold-band", manifoldStageId);
      container.setAttribute("data-zoom", zoomLevel.toFixed(3));
    }

    function tick() {
      if (disposed) return;
      strobeTick += 1;
      var elapsedMs = performance.now() - t0;
      // Smooth lerp zoom + pan (lossless continuum; band LOD swaps at thresholds)
      zoomLevel += (targetZoom - zoomLevel) * 0.18;
      panX += (targetPanX - panX) * 0.22;
      panZ += (targetPanZ - panZ) * 0.22;
      if (Math.abs(targetZoom - zoomLevel) < 0.0008) zoomLevel = targetZoom;
      if (Math.abs(targetPanX - panX) < 0.001) panX = targetPanX;
      if (Math.abs(targetPanZ - panZ) < 0.001) panZ = targetPanZ;
      applyOrtho();
      syncManifoldFromZoom();

      // Procedural LOD swap — no texture opacity crossfade
      if (skinCrossfade < 1) {
        skinCrossfade = 1;
        if (mapMeshPrev) {
          disposeMapMesh(mapMeshPrev);
          mapMeshPrev = null;
        }
      }

      if (elapsedMs - lastFetchMs >= POLL_MS || liveRefreshTicks === 0) {
        lastFetchMs = elapsedMs;
        refreshTracks(false);
      }
      // Solar terminator drifts slowly — rebuild overlay every 60s
      if (elapsedMs - lastWxRebuildMs > 60000) {
        lastWxRebuildMs = elapsedMs;
        rebuildWxOverlay();
      }
      // Airport focus ring — readable fraction of current view (not fixed 0.5 world units)
      var vh = viewHalfWorld();
      var ringBase = Math.max(0.8, vh * 0.028);
      var pulse = (1 + 0.08 * Math.sin(elapsedMs * 0.004)) * (currentBand.walkMode ? 1.2 : 1);
      ring.scale.set(ringBase * pulse, ringBase * pulse, ringBase * pulse);
      // Keep sprites FR24-readable while zoom lerps between polls
      if (strobeTick % 3 === 0) {
        Object.keys(meshByIcao).forEach(function (k) {
          var m = meshByIcao[k];
          if (!m) return;
          var sc = aircraftWorldScale(m.userData.alt, m.userData.variant || "jet");
          m.userData.baseScale = sc;
          if (m.isSprite) m.scale.set(sc, sc, 1);
          else m.scale.set(sc * 0.55, sc * 0.55, sc * 0.55);
        });
      }
      updateHud(elapsedMs);
      renderer.render(scene, camera);
      raf = requestAnimationFrame(tick);
    }

    var canvas = renderer.domElement;
    var skipDragUntilUp = false;

    function panSense() {
      return currentBand.panSense != null ? currentBand.panSense : 1;
    }

    function onWheel(ev) {
      ev.preventDefault();
      // Scroll-wheel zoom toward cursor. Pinch on trackpad = ctrlKey + wheel.
      // Shift+wheel (or dominant deltaX) = pan — two-finger horizontal trackpad feel.
      // Airport walk: higher pan sensitivity (surface walk).
      if (ev.shiftKey || (!ev.ctrlKey && Math.abs(ev.deltaX) > Math.abs(ev.deltaY) * 1.15)) {
        var rect = canvas.getBoundingClientRect();
        var half = orthoHalf / zoomLevel;
        var aspect = rect.width / (rect.height || 1);
        var sx = ev.shiftKey ? ev.deltaY : ev.deltaX;
        var sy = ev.shiftKey ? 0 : ev.deltaY;
        var ps = panSense();
        targetPanX += (sx / Math.max(1, rect.width)) * (2 * half * aspect) * ps;
        targetPanZ += (sy / Math.max(1, rect.height)) * (2 * half) * ps;
        return;
      }
      var intensity = ev.ctrlKey ? 0.014 : 0.0022;
      var factor = Math.exp(-ev.deltaY * intensity);
      if (ev.deltaMode === 1) factor = Math.exp(-ev.deltaY * 0.09);
      if (!(factor > 0) || !isFinite(factor)) return;
      zoomAt(ev.clientX, ev.clientY, factor);
    }

    function onGestureChange(ev) {
      // Safari pinch
      if (typeof ev.scale !== "number") return;
      ev.preventDefault();
      var factor = ev.scale > 0 ? Math.pow(ev.scale, 0.08) : 1;
      // gesturechange fires continuously; use delta vs last
      if (!onGestureChange._last) onGestureChange._last = 1;
      var rel = ev.scale / onGestureChange._last;
      onGestureChange._last = ev.scale;
      if (!(rel > 0)) return;
      zoomAt(ev.clientX || window.innerWidth / 2, ev.clientY || window.innerHeight / 2, rel);
    }
    function onGestureEnd() {
      onGestureChange._last = 1;
    }

    function onKeyDown(ev) {
      if (ev.code === "Space" && !ev.repeat) {
        spaceDown = true;
        if (!dragging) canvas.style.cursor = "grab";
        ev.preventDefault();
      }
    }
    function onKeyUp(ev) {
      if (ev.code === "Space") {
        spaceDown = false;
        if (!dragging) canvas.style.cursor = "grab";
      }
    }

    function onPointerDown(ev) {
      if (ev.button !== 0 && ev.pointerType === "mouse") return;
      var now = performance.now();
      if (
        now - lastTapMs < 320 &&
        Math.abs(ev.clientX - lastTapX) < 12 &&
        Math.abs(ev.clientY - lastTapY) < 12
      ) {
        // Double-click / double-tap: zoom in (shift = zoom out)
        zoomAt(ev.clientX, ev.clientY, ev.shiftKey ? 1 / 1.55 : 1.55);
        lastTapMs = 0;
        skipDragUntilUp = true;
        return;
      }
      lastTapMs = now;
      lastTapX = ev.clientX;
      lastTapY = ev.clientY;
      dragging = true;
      lastPtr = { x: ev.clientX, y: ev.clientY };
      canvas.setPointerCapture(ev.pointerId);
      canvas.style.cursor = "grabbing";
    }

    function onPointerMove(ev) {
      if (!dragging || !lastPtr || skipDragUntilUp) return;
      var rect = canvas.getBoundingClientRect();
      var half = orthoHalf / zoomLevel;
      var aspect = rect.width / (rect.height || 1);
      var dx = ev.clientX - lastPtr.x;
      var dy = ev.clientY - lastPtr.y;
      var ps = panSense();
      // Click-drag / space-drag / touch-drag → pan (airport walk uses higher sense)
      targetPanX -= (dx / rect.width) * (2 * half * aspect) * ps;
      targetPanZ -= (dy / rect.height) * (2 * half) * ps;
      lastPtr = { x: ev.clientX, y: ev.clientY };
    }

    function onPointerUp(ev) {
      dragging = false;
      lastPtr = null;
      skipDragUntilUp = false;
      try {
        canvas.releasePointerCapture(ev.pointerId);
      } catch (_) {}
      canvas.style.cursor = spaceDown ? "grab" : "grab";
    }

    canvas.addEventListener("wheel", onWheel, { passive: false });
    canvas.addEventListener("gesturestart", function (e) {
      e.preventDefault();
      onGestureChange._last = 1;
    }, { passive: false });
    canvas.addEventListener("gesturechange", onGestureChange, { passive: false });
    canvas.addEventListener("gestureend", onGestureEnd);
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("pointercancel", onPointerUp);
    canvas.addEventListener("contextmenu", function (e) {
      e.preventDefault();
    });
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);

    document.getElementById("btnZoomIn").onclick = function () {
      var rect = canvas.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, 1.35);
    };
    document.getElementById("btnZoomOut").onclick = function () {
      var rect = canvas.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, 1 / 1.35);
    };
    document.getElementById("btnZoomAirport").onclick = function () {
      setManifoldView("AIRPORT_WALK");
    };
    var btnMetro = document.getElementById("btnZoomMetro");
    if (btnMetro) {
      btnMetro.onclick = function () {
        setManifoldView("METRO");
      };
    }
    var btnRegional = document.getElementById("btnZoomRegional");
    if (btnRegional) {
      btnRegional.onclick = function () {
        setManifoldView("REGIONAL");
      };
    }
    var btnHemi = document.getElementById("btnZoomHemi");
    if (btnHemi) {
      btnHemi.onclick = function () {
        setManifoldView("HEMISPHERE");
      };
    }
    twin.querySelectorAll(".twin-icao").forEach(function (b) {
      b.onclick = function () {
        setAirport(b.getAttribute("data-icao"));
      };
    });
    twin.querySelectorAll(".twin-view").forEach(function (b) {
      b.onclick = function () {
        setManifoldView(b.getAttribute("data-band"));
      };
    });

    // Boot from ?icao=&band=&zoom_milli=
    try {
      var bootQs = new URLSearchParams(location.search);
      var bootIcao = (bootQs.get("icao") || "").toUpperCase();
      var bootBand = (bootQs.get("band") || "").toUpperCase();
      var bootZm = parseInt(bootQs.get("zoom_milli") || "", 10);
      if (bootIcao && AIRPORTS[bootIcao] && bootIcao !== focusIcao) {
        setAirport(bootIcao);
      }
      if (bootBand && ["HEMISPHERE", "REGIONAL", "METRO", "AIRPORT_WALK"].indexOf(bootBand) >= 0) {
        setManifoldView(bootBand, { snap: true });
      } else if (isFinite(bootZm) && bootZm > 0) {
        targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, bootZm / 1000));
        zoomLevel = targetZoom;
      }
    } catch (_) {}

    applyOrtho();
    syncManifoldFromZoom();
    syncTwinChrome();
    updateTwinWxPanel();
    tick();

    function onResize() {
      var rect = container.getBoundingClientRect();
      var nw = Math.max(container.clientWidth || 0, Math.floor(rect.width) || 0) || 640;
      var nh = Math.max(container.clientHeight || 0, Math.floor(rect.height) || 0) || 420;
      renderer.setSize(nw, nh);
      applyOrtho();
    }
    window.addEventListener("resize", onResize);
    // Re-measure after CSS grid settles (zero-width column bug leaves clientWidth=0 at first paint)
    requestAnimationFrame(function () {
      onResize();
      requestAnimationFrame(onResize);
    });
    setTimeout(onResize, 100);
    setTimeout(onResize, 500);

    return {
      dispose: function () {
        disposed = true;
        cancelAnimationFrame(raf);
        window.removeEventListener("resize", onResize);
        canvas.removeEventListener("wheel", onWheel);
        canvas.removeEventListener("gesturechange", onGestureChange);
        canvas.removeEventListener("gestureend", onGestureEnd);
        canvas.removeEventListener("pointerdown", onPointerDown);
        canvas.removeEventListener("pointermove", onPointerMove);
        canvas.removeEventListener("pointerup", onPointerUp);
        canvas.removeEventListener("pointercancel", onPointerUp);
        window.removeEventListener("keydown", onKeyDown);
        window.removeEventListener("keyup", onKeyUp);
        renderer.dispose();
        if (hud.parentNode) hud.parentNode.removeChild(hud);
        if (chrome.parentNode) chrome.parentNode.removeChild(chrome);
        if (twin.parentNode) twin.parentNode.removeChild(twin);
        if (zoomStack.parentNode) zoomStack.parentNode.removeChild(zoomStack);
        if (warnPanel.parentNode) warnPanel.parentNode.removeChild(warnPanel);
        clearWarnLines();
        disposeMapMesh(mapMeshPrev);
        disposeMapMesh(mapMesh);
        disposeMapMesh(wxOverlayMesh);
      },
      hintCount: hints.length,
      timeSampleCount: 0,
      sceneMode: "atc-map",
      setAirport: setAirport,
      setManifoldZoom: function (z) {
        targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, Number(z) || targetZoom));
      },
      getZoom: function () {
        return zoomLevel;
      },
      forceRefresh: function () {
        return refreshTracks(true);
      },
      zoomToBand: function (bandId) {
        setManifoldView(bandId, { snap: false });
      },
      setManifoldView: setManifoldView,
      zoomBy: function (factor) {
        var rect = canvas.getBoundingClientRect();
        zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
      },
      applyMembraneTick: function (info) {
        membraneTicks += 1;
        var detail = info && info.gameId ? String(info.gameId) : "aviation_atc";
        hud.setAttribute("data-last-membrane", detail);
        refreshTracks(false);
      },
      getLiveState: function () {
        var zr = MS && MS.zoomRational ? MS.zoomRational(zoomLevel) : { text: "" };
        return {
          strobeTick: strobeTick,
          clockMs: Math.floor(performance.now() - t0),
          membraneTicks: membraneTicks,
          liveRefreshTicks: liveRefreshTicks,
          aircraftCount: aircraftCount,
          lodTrackCount: lodTrackCount,
          sceneMode: "atc-map",
          focusIcao: focusIcao,
          trackSource: hud.getAttribute("data-track-source") || "swift_uum8d_zoom",
          projectionSource: hud.getAttribute("data-projection-source") || "",
          trackError: trackError,
          zoom: zoomLevel,
          zoomRational: zr.text || "",
          manifoldBand: manifoldStageId,
          manifoldLabel: currentBand.label,
          walkMode: !!currentBand.walkMode,
          wxStatus: wxStatus,
          solarElev:
            wxMeta && wxMeta.solar ? wxMeta.solar.elevationDeg : null,
          warnCount: (warningState.warnings || []).length,
          warnTop:
            warningState.warnings && warningState.warnings[0]
              ? warningState.warnings[0]
              : null,
          minima: warningState.minima,
          panX: panX,
          panZ: panZ,
          packetToPaintMs: lastPacketToPaintMs,
          swiftGenMs: lastSwiftGenMs,
          pollMs: POLL_MS,
          c4Stitch: true,
        };
      },
    };
  }

  function buildScene(THREE, container, hints, usdaText, opts) {
    var schema = schemaOf(usdaText);
    var isAtc =
      schema.indexOf("airspace_atc") >= 0 ||
      /gaia:focus_icao\s*=/.test(usdaText || "") ||
      /gaia:tracks_path\s*=/.test(usdaText || "") ||
      (opts && opts.forceAtc);
    if (isAtc) return buildAtcScene(THREE, container, hints, usdaText, opts);
    return buildLatticeScene(THREE, container, hints, usdaText);
  }

  global.OpenUSDPlayer = {
    parseUsdHints: parseUsdHints,
    parseTranslateTimeSamples: parseTranslateTimeSamples,
    AIRPORTS: AIRPORTS,
    ManifoldStage: global.ManifoldStage || null,
    mount: function (container, usdaText, THREE, opts) {
      if (!THREE) throw new Error("THREE.js not loaded");
      var hints = parseUsdHints(usdaText);
      try {
        return buildScene(THREE, container, hints, usdaText, opts || {});
      } catch (err) {
        // Never leave a void page: body-level + in-viewport 2D HUD when WebGL fails.
        var msg = String(err && err.message ? err.message : err);
        container.innerHTML = "";
        container.style.cssText =
          (container.style.cssText || "") +
          ";display:flex;align-items:center;justify-content:center;background:#0a1628;color:#e8eef2;padding:24px;";
        var box = document.createElement("div");
        box.style.cssText =
          "max-width:520px;font:14px/1.45 ui-sans-serif,system-ui,sans-serif;border:1px solid #f5c518;padding:16px 18px;background:rgba(10,16,24,0.95);";
        box.innerHTML =
          "<div style='font-weight:700;color:#f5c518;margin-bottom:8px'>Affine.Earth OpenUSD — WebGL unavailable</div>" +
          "<div style='font:12px/1.4 ui-monospace,monospace;color:#c8d0d6;white-space:pre-wrap'></div>";
        box.lastChild.textContent = msg;
        container.appendChild(box);
        var boot = document.getElementById("openusdBootStatus");
        if (boot) boot.textContent = "WEBGL_FAIL: " + msg.slice(0, 120);
        return {
          dispose: function () {},
          sceneMode: "webgl-fallback",
          applyMembraneTick: function () {},
          getLiveState: function () {
            return { sceneMode: "webgl-fallback", trackError: msg };
          },
        };
      }
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
