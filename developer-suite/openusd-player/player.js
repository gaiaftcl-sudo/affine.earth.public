/**
 * Affine.Earth OpenUSD — OpenUSD lattice + FR24-class live ATC map.
 * Three.js CDN only; no Pixar libusd.
 *
 * ATC map contract:
 * - Dark geographic basemap (top-down)
 * - Bright yellow plane silhouettes rotated by live heading
 * - Positions from GET /language-invariant/adsb/tracks (live) — no authored loops
 * - Airport zoom (KJFK / EGLL / EHAM / LFPG / …)
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
    var land = (root.getPropertyValue("--ae-land") || "").trim() || "#1a2820";
    var label = (root.getPropertyValue("--ae-label") || "").trim() || "#c8d0d6";
    var accent = (root.getPropertyValue("--ae-accent") || "").trim() || "#f5c518";
    return { ocean: ocean, land: land, label: label, accent: accent };
  }

  /** Dark geographic basemap canvas (ocean + land blobs + labels) — skin-aware. */
  function makeBasemapTexture(THREE, centerLat, centerLon, spanDeg) {
    var pal = skinPalette();
    var W = 1024;
    var H = 1024;
    var c = document.createElement("canvas");
    c.width = W;
    c.height = H;
    var g = c.getContext("2d");
    // ocean
    g.fillStyle = pal.ocean;
    g.fillRect(0, 0, W, H);
    // subtle gradient
    var grd = g.createRadialGradient(W * 0.5, H * 0.45, 40, W * 0.5, H * 0.5, W * 0.7);
    grd.addColorStop(0, pal.ocean);
    grd.addColorStop(1, "#071018");
    g.fillStyle = grd;
    g.fillRect(0, 0, W, H);

    function project(lat, lon) {
      var x = ((lon - (centerLon - spanDeg / 2)) / spanDeg) * W;
      var y = ((centerLat + spanDeg / 2 - lat) / spanDeg) * H;
      return { x: x, y: y };
    }

    // Coarse land polygons (approximate continents / regions) — visual feel only
    var lands = [
      // Europe
      [
        [71, -10], [70, 30], [60, 40], [55, 40], [45, 30], [36, 28],
        [36, -9], [43, -10], [51, -11], [59, -8], [71, -10],
      ],
      // UK / Ireland
      [[60, -8], [59, 2], [50, 2], [50, -6], [52, -11], [55, -8], [60, -8]],
      // N Africa strip
      [[36, -10], [36, 35], [30, 35], [28, -10], [36, -10]],
      // Eastern US / Canada slice when KJFK
      [[48, -85], [47, -65], [40, -70], [38, -78], [42, -85], [48, -85]],
      // Western Europe denser blob
      [[55, -5], [54, 12], [48, 12], [44, 5], [43, -2], [48, -6], [55, -5]],
    ];

    g.fillStyle = pal.land;
    g.strokeStyle = "#2a3a34";
    g.lineWidth = 1.2;
    lands.forEach(function (poly) {
      g.beginPath();
      poly.forEach(function (ll, i) {
        var p = project(ll[0], ll[1]);
        if (i === 0) g.moveTo(p.x, p.y);
        else g.lineTo(p.x, p.y);
      });
      g.closePath();
      g.fill();
      g.stroke();
    });

    // Lat/lon grid
    g.strokeStyle = "rgba(70,100,120,0.28)";
    g.lineWidth = 1;
    var step = spanDeg > 25 ? 5 : spanDeg > 12 ? 2 : 1;
    for (var lat = Math.floor(centerLat - spanDeg / 2); lat <= centerLat + spanDeg / 2; lat += step) {
      var a = project(lat, centerLon - spanDeg / 2);
      var b = project(lat, centerLon + spanDeg / 2);
      g.beginPath();
      g.moveTo(a.x, a.y);
      g.lineTo(b.x, b.y);
      g.stroke();
    }
    for (var lon = Math.floor(centerLon - spanDeg / 2); lon <= centerLon + spanDeg / 2; lon += step) {
      var c1 = project(centerLat + spanDeg / 2, lon);
      var c2 = project(centerLat - spanDeg / 2, lon);
      g.beginPath();
      g.moveTo(c1.x, c1.y);
      g.lineTo(c2.x, c2.y);
      g.stroke();
    }

    // City / airport labels near center airports
    g.font = "600 14px sans-serif";
    Object.keys(AIRPORTS).forEach(function (icao) {
      var ap = AIRPORTS[icao];
      if (Math.abs(ap.lat - centerLat) > spanDeg * 0.55) return;
      if (Math.abs(ap.lon - centerLon) > spanDeg * 0.55) return;
      var p = project(ap.lat, ap.lon);
      g.beginPath();
      g.fillStyle = pal.accent;
      g.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
      g.fill();
      g.fillStyle = pal.label;
      g.fillText(ap.name.split(" ")[0], p.x + 6, p.y - 4);
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
    // Smooth zoom + pan (trackpad/mouse first-class)
    var zoomLevel = 1; // display / HUD
    var targetZoom = 1;
    var panX = 0;
    var panZ = 0;
    var targetPanX = 0;
    var targetPanZ = 0;
    var ZOOM_MIN = 0.35;
    var ZOOM_MAX = 12;
    var dragging = false;
    var spaceDown = false;
    var lastPtr = null;
    var lastTapMs = 0;
    var lastTapX = 0;
    var lastTapY = 0;

    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    renderer.domElement.style.cursor = "grab";
    renderer.domElement.style.touchAction = "none";

    var hud = makeHud(container);
    hud.setAttribute("data-scene-mode", "atc-map");
    hud.setAttribute("data-focus-icao", focusIcao);
    hud.setAttribute("data-track-source", "adsb.lol_https_v2");

    // Title chrome
    var chrome = document.createElement("div");
    chrome.className = "map-chrome top-left";
    chrome.innerHTML =
      '<div class="map-title">Affine.Earth OpenUSD · LIVE ATC map</div>' +
      '<div class="map-sub" id="mapSubTitle">zoom ' +
      focusIcao +
      " · SVG sprites · live ADS-B</div>";
    container.appendChild(chrome);

    // Zoom controls
    var zoomStack = document.createElement("div");
    zoomStack.className = "zoom-stack";
    zoomStack.innerHTML =
      '<button type="button" id="btnZoomIn" title="Zoom in">+</button>' +
      '<button type="button" id="btnZoomOut" title="Zoom out">−</button>' +
      '<button type="button" id="btnZoomAirport" title="Fit airport">⌖</button>';
    container.appendChild(zoomStack);

    // Basemap
    var basemapTex = makeBasemapTexture(THREE, centerLat, centerLon, viewSpanDeg * 1.35);
    var mapSize = viewSpanDeg * mapScale;
    var mapMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(mapSize, mapSize),
      new THREE.MeshBasicMaterial({ map: basemapTex })
    );
    mapMesh.rotation.x = -Math.PI / 2;
    mapMesh.position.y = -0.1;
    scene.add(mapMesh);

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
    var POLL_MS = 3500;

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

    function setAirport(icao) {
      icao = (icao || "KJFK").toUpperCase();
      if (!AIRPORTS[icao]) return;
      focusIcao = icao;
      ap = AIRPORTS[icao];
      centerLat = ap.lat;
      centerLon = ap.lon;
      viewSpanDeg = ap.zoom;
      orthoHalf = (viewSpanDeg * mapScale) / 2.4;
      targetZoom = 1.4;
      zoomLevel = 1.4;
      targetPanX = 0;
      targetPanZ = 0;
      panX = 0;
      panZ = 0;
      // rebuild basemap
      scene.remove(mapMesh);
      if (mapMesh.material.map) mapMesh.material.map.dispose();
      mapMesh.material.dispose();
      mapMesh.geometry.dispose();
      basemapTex = makeBasemapTexture(THREE, centerLat, centerLon, viewSpanDeg * 1.35);
      mapSize = viewSpanDeg * mapScale;
      mapMesh = new THREE.Mesh(
        new THREE.PlaneGeometry(mapSize, mapSize),
        new THREE.MeshBasicMaterial({ map: basemapTex })
      );
      mapMesh.rotation.x = -Math.PI / 2;
      mapMesh.position.y = -0.1;
      scene.add(mapMesh);
      applyOrtho();
      hud.setAttribute("data-focus-icao", focusIcao);
      var sub = document.getElementById("mapSubTitle");
      if (sub)
        sub.textContent =
          "zoom " + focusIcao + " · " + ap.name + " · live ADS-B · scroll/pinch/drag";
      refreshTracks(true);
    }

    function upsertAircraft(rows) {
      var seen = {};
      var list = (rows || []).slice(0, MAX_AC);
      list.forEach(function (a) {
        var icao = String(a.icao || "").toLowerCase();
        if (!icao || a.lat == null || a.lon == null) return;
        seen[icao] = true;
        var ll = lonLatToWorld(a.lat, a.lon, centerLat, centerLon, mapScale);
        var mesh = meshByIcao[icao];
        if (!mesh) {
          var alt0 = Number(a.alt_baro_ft) || 0;
          var gs0 = Number(a.gs_kt) || 0;
          var variant = "jet";
          var map = planeTex;
          if (alt0 < 80 && gs0 < 80) {
            variant = "light";
            map = planeTexLight || planeTex;
          } else if (alt0 > 28000 || gs0 > 420) {
            variant = "heavy";
            map = planeTexHeavy || planeTex;
          }
          var mat = new THREE.SpriteMaterial({
            map: map,
            transparent: true,
            depthWrite: false,
            color: 0xffffff,
          });
          mesh = new THREE.Sprite(mat);
          mesh.scale.set(1.15, 1.15, 1);
          mesh.userData.icao = icao;
          mesh.userData.variant = variant;
          acGroup.add(mesh);
          meshByIcao[icao] = mesh;
        }
        var alpha = mesh.userData.seeded ? 0.45 : 1;
        mesh.userData.seeded = true;
        mesh.position.x += (ll.x - mesh.position.x) * alpha;
        mesh.position.z += (ll.z - mesh.position.z) * alpha;
        mesh.position.y = 0.2;
        // Sprite material rotation (radians) — heading from north clockwise
        var track = Number(a.track_deg) || 0;
        mesh.material.rotation = (-track * Math.PI) / 180;
        mesh.userData.callsign = a.callsign || icao;
        mesh.userData.alt = a.alt_baro_ft || 0;
        mesh.userData.gs = a.gs_kt || 0;
        mesh.userData.track = track;
        // Size by altitude + inverse-ish zoom so dense traffic stays readable
        var alt = Number(a.alt_baro_ft) || 0;
        var sc = alt < 100 ? 0.95 : alt < 10000 ? 1.05 : 1.2;
        var zf = 1 / Math.sqrt(Math.max(0.5, zoomLevel));
        sc *= 0.85 + 0.55 * zf;
        mesh.userData.baseScale = sc;
        mesh.scale.set(sc, sc, 1);
      });
      Object.keys(meshByIcao).forEach(function (icao) {
        if (!seen[icao]) {
          acGroup.remove(meshByIcao[icao]);
          if (meshByIcao[icao].material) meshByIcao[icao].material.dispose();
          delete meshByIcao[icao];
        }
      });
      aircraftCount = Object.keys(meshByIcao).length;
    }

    async function refreshTracks(force) {
      if (disposed) return;
      if (!global.UUM8DShell || !global.UUM8DShell.fetchLiveTracks) {
        trackError = "fetchLiveTracks missing";
        return;
      }
      try {
        var payload = await global.UUM8DShell.fetchLiveTracks({
          icao: focusIcao,
          dist: force ? 120 : 100,
          force: !!force,
        });
        liveRefreshTicks += 1;
        trackError = payload.error || "";
        upsertAircraft(payload.aircraft || []);
        hud.setAttribute("data-track-source", payload.source || "adsb.lol_https_v2");
        var sub = document.getElementById("mapSubTitle");
        if (sub) {
          sub.textContent =
            focusIcao +
            " · ac=" +
            aircraftCount +
            " · liveRefresh=" +
            liveRefreshTicks +
            " · " +
            (payload.source || "adsb.lol_https_v2") +
            (trackError ? " · " + String(trackError).slice(0, 40) : "");
        }
      } catch (e) {
        trackError = String(e);
      }
    }

    function updateHud(elapsedMs) {
      if (elapsedMs - lastHudMs < 80 && strobeTick % 6 !== 0) return;
      lastHudMs = elapsedMs;
      var clockMs = Math.floor(elapsedMs);
      hud.setAttribute("data-strobe-tick", String(strobeTick));
      hud.setAttribute("data-clock-ms", String(clockMs));
      hud.setAttribute("data-membrane-ticks", String(membraneTicks));
      hud.setAttribute("data-live-refresh", String(liveRefreshTicks));
      hud.setAttribute("data-aircraft", String(aircraftCount));
      hud.setAttribute("data-scene-mode", "atc-map");
      hud.setAttribute("data-focus-icao", focusIcao);
      hud.setAttribute("data-zoom", zoomLevel.toFixed(2));
      if (trackError) hud.setAttribute("data-track-error", trackError);
      else hud.removeAttribute("data-track-error");
      hud.textContent =
        "mode=atc-map " +
        focusIcao +
        " strobe=" +
        strobeTick +
        " clock=" +
        clockMs +
        "ms membrane=" +
        membraneTicks +
        " liveRefresh=" +
        liveRefreshTicks +
        " ac=" +
        aircraftCount +
        " zoom=" +
        zoomLevel.toFixed(2) +
        " src=adsb.lol_https_v2" +
        (trackError ? " err=" + trackError.slice(0, 36) : "");
      var sub = document.getElementById("mapSubTitle");
      if (sub) {
        sub.textContent =
          "zoom " +
          focusIcao +
          " · " +
          zoomLevel.toFixed(2) +
          "× · ac=" +
          aircraftCount +
          " · SVG sprites · live ADS-B";
      }
      container.setAttribute("data-strobe-tick", String(strobeTick));
      container.setAttribute("data-clock-ms", String(clockMs));
      container.setAttribute("data-membrane-ticks", String(membraneTicks));
      container.setAttribute("data-live-refresh", String(liveRefreshTicks));
      container.setAttribute("data-aircraft", String(aircraftCount));
      container.setAttribute("data-openusd-animating", strobeTick > 0 ? "1" : "0");
      container.setAttribute("data-scene-mode", "atc-map");
      container.setAttribute("data-focus-icao", focusIcao);
    }

    function tick() {
      if (disposed) return;
      strobeTick += 1;
      var elapsedMs = performance.now() - t0;
      // Smooth lerp zoom + pan (pro map feel)
      zoomLevel += (targetZoom - zoomLevel) * 0.18;
      panX += (targetPanX - panX) * 0.22;
      panZ += (targetPanZ - panZ) * 0.22;
      if (Math.abs(targetZoom - zoomLevel) < 0.0008) zoomLevel = targetZoom;
      if (Math.abs(targetPanX - panX) < 0.001) panX = targetPanX;
      if (Math.abs(targetPanZ - panZ) < 0.001) panZ = targetPanZ;
      applyOrtho();

      if (elapsedMs - lastFetchMs >= POLL_MS || liveRefreshTicks === 0) {
        lastFetchMs = elapsedMs;
        refreshTracks(false);
      }
      // Pulse airport ring
      var pulse = 1 + 0.08 * Math.sin(elapsedMs * 0.004);
      ring.scale.set(pulse, pulse, pulse);
      updateHud(elapsedMs);
      renderer.render(scene, camera);
      raf = requestAnimationFrame(tick);
    }

    var canvas = renderer.domElement;
    var skipDragUntilUp = false;

    function onWheel(ev) {
      ev.preventDefault();
      // Scroll-wheel zoom toward cursor. Pinch on trackpad = ctrlKey + wheel.
      // Shift+wheel (or dominant deltaX) = pan — two-finger horizontal trackpad feel.
      if (ev.shiftKey || (!ev.ctrlKey && Math.abs(ev.deltaX) > Math.abs(ev.deltaY) * 1.15)) {
        var rect = canvas.getBoundingClientRect();
        var half = orthoHalf / zoomLevel;
        var aspect = rect.width / (rect.height || 1);
        var sx = ev.shiftKey ? ev.deltaY : ev.deltaX;
        var sy = ev.shiftKey ? 0 : ev.deltaY;
        targetPanX += (sx / Math.max(1, rect.width)) * (2 * half * aspect);
        targetPanZ += (sy / Math.max(1, rect.height)) * (2 * half);
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
      // Click-drag / space-drag / touch-drag → pan
      targetPanX -= (dx / rect.width) * (2 * half * aspect);
      targetPanZ -= (dy / rect.height) * (2 * half);
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
      targetZoom = 1.6;
      targetPanX = 0;
      targetPanZ = 0;
      refreshTracks(true);
    };

    applyOrtho();
    tick();

    function onResize() {
      var nw = container.clientWidth || 640;
      var nh = container.clientHeight || 420;
      renderer.setSize(nw, nh);
      applyOrtho();
    }
    window.addEventListener("resize", onResize);

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
        if (zoomStack.parentNode) zoomStack.parentNode.removeChild(zoomStack);
      },
      hintCount: hints.length,
      timeSampleCount: 0,
      sceneMode: "atc-map",
      setAirport: setAirport,
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
        return {
          strobeTick: strobeTick,
          clockMs: Math.floor(performance.now() - t0),
          membraneTicks: membraneTicks,
          liveRefreshTicks: liveRefreshTicks,
          aircraftCount: aircraftCount,
          sceneMode: "atc-map",
          focusIcao: focusIcao,
          trackSource: "adsb.lol_https_v2",
          trackError: trackError,
          zoom: zoomLevel,
          panX: panX,
          panZ: panZ,
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
    mount: function (container, usdaText, THREE, opts) {
      if (!THREE) throw new Error("THREE.js not loaded");
      var hints = parseUsdHints(usdaText);
      return buildScene(THREE, container, hints, usdaText, opts || {});
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
