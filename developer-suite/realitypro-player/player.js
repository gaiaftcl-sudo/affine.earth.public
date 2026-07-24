/**
 * RealityPro OpenUSD lattice preview — live 3D state (video-like strobe).
 * Three.js CDN only; no vendored Pixar libusd / WASM.
 *
 * Animation contract (Affine.Earth goals):
 * - Wall clock + strobeTick drive time-evolving mesh (orbit + lattice pulse)
 * - Optional USDA timeSamples (xformOp:translate.timeSamples) modulate radii
 * - Membrane project ticks call applyMembraneTick() → visible state change
 * - DOM/data attributes expose clock for CDP/headless proof without WebGL pixels
 */
(function (global) {
  "use strict";

  function parseUsdHints(usda) {
    const names = [];
    const re = /\bdef\s+(\w+)\s+"([^"]+)"/g;
    let m;
    while ((m = re.exec(usda || ""))) {
      names.push({ type: m[1], name: m[2] });
    }
    return names;
  }

  /**
   * Parse simple USD timeSamples blocks:
   *   double3 xformOp:translate.timeSamples = { 0: (1, 0, 0), 1: (0, 1, 0), ... }
   * Returns [{t, x, y, z}, ...] sorted by t, or [].
   */
  function parseTranslateTimeSamples(usda) {
    const text = usda || "";
    const blockRe =
      /xformOp:translate\.timeSamples\s*=\s*\{([^}]*)\}/gi;
    const samples = [];
    let block;
    while ((block = blockRe.exec(text))) {
      const body = block[1];
      const sampleRe =
        /(\d+(?:\.\d+)?)\s*:\s*\(\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*,\s*([-\d.eE+]+)\s*\)/g;
      let s;
      while ((s = sampleRe.exec(body))) {
        samples.push({
          t: parseFloat(s[1]),
          x: parseFloat(s[2]),
          y: parseFloat(s[3]),
          z: parseFloat(s[4]),
        });
      }
    }
    samples.sort(function (a, b) {
      return a.t - b.t;
    });
    return samples;
  }

  function lerpSamples(samples, tNorm) {
    if (!samples.length) return null;
    if (samples.length === 1) return samples[0];
    const t0 = samples[0].t;
    const t1 = samples[samples.length - 1].t;
    const span = t1 > t0 ? t1 - t0 : 1;
    const t = t0 + (tNorm % 1) * span;
    let i = 0;
    while (i < samples.length - 1 && samples[i + 1].t < t) i += 1;
    const a = samples[i];
    const b = samples[Math.min(i + 1, samples.length - 1)];
    const den = b.t - a.t;
    const u = den > 0 ? (t - a.t) / den : 0;
    return {
      t: t,
      x: a.x + (b.x - a.x) * u,
      y: a.y + (b.y - a.y) * u,
      z: a.z + (b.z - a.z) * u,
    };
  }

  function buildScene(THREE, container, hints, usdaText) {
    const w = container.clientWidth || 640;
    const h = container.clientHeight || 420;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 200);
    camera.position.set(4.5, 3.2, 5.5);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // Live-state HUD for CDP / headless proof (works even if WebGL pixels fail)
    const hud = document.createElement("div");
    hud.id = "realitypro-live-hud";
    hud.setAttribute("data-realitypro-live", "1");
    hud.setAttribute("data-strobe-tick", "0");
    hud.setAttribute("data-clock-ms", "0");
    hud.setAttribute("data-membrane-ticks", "0");
    hud.setAttribute("data-nats-subject", "gaiaftcl.reality.manifold.realitypro.apex");
    hud.style.cssText =
      "position:absolute;left:8px;bottom:8px;z-index:2;font:11px/1.35 ui-monospace,monospace;" +
      "color:#8aa0ad;background:rgba(11,17,21,0.72);padding:6px 8px;border:1px solid #2a3a44;border-radius:4px;";
    hud.textContent = "strobe=0 clock=0ms membrane=0";
    container.style.position = container.style.position || "relative";
    container.appendChild(hud);

    scene.add(new THREE.AmbientLight(0x668888, 0.7));
    const dir = new THREE.DirectionalLight(0xffffff, 0.85);
    dir.position.set(3, 6, 2);
    scene.add(dir);

    const grid = new THREE.GridHelper(10, 20, 0x3ecf8e, 0x24343c);
    scene.add(grid);

    const group = new THREE.Group();
    scene.add(group);

    const timeSamples = parseTranslateTimeSamples(usdaText);
    const n = Math.max(hints.length, 8);
    const basePositions = [];
    for (let i = 0; i < n; i++) {
      const hint = hints[i] || { type: "Xform", name: "node_" + i };
      const geo =
        hint.type.toLowerCase().indexOf("mesh") >= 0
          ? new THREE.BoxGeometry(0.35, 0.35, 0.35)
          : new THREE.SphereGeometry(0.18, 16, 16);
      const mat = new THREE.MeshStandardMaterial({
        color: hint.type.toLowerCase().indexOf("mesh") >= 0 ? 0xe0a35c : 0x3ecf8e,
        metalness: 0.2,
        roughness: 0.55,
        emissive: 0x000000,
        emissiveIntensity: 0,
      });
      const mesh = new THREE.Mesh(geo, mat);
      const angle = (i / n) * Math.PI * 2;
      const r = 1.6 + (i % 3) * 0.35;
      const pos = {
        x: Math.cos(angle) * r,
        y: (i % 5) * 0.25 - 0.5,
        z: Math.sin(angle) * r,
      };
      basePositions.push(pos);
      mesh.position.set(pos.x, pos.y, pos.z);
      mesh.userData.label = hint.name;
      mesh.userData.baseIndex = i;
      group.add(mesh);
    }

    const lineMat = new THREE.LineBasicMaterial({
      color: 0x4a7a88,
      transparent: true,
      opacity: 0.55,
    });
    const lineGeo = new THREE.BufferGeometry();
    const line = new THREE.LineSegments(lineGeo, lineMat);
    scene.add(line);

    function rebuildEdges() {
      const pts = [];
      group.children.forEach(function (ch, idx) {
        const next = group.children[(idx + 1) % group.children.length];
        pts.push(ch.position.clone(), next.position.clone());
      });
      lineGeo.setFromPoints(pts);
    }
    rebuildEdges();

    let raf = 0;
    let strobeTick = 0;
    let membraneTicks = 0;
    let membranePulse = 0;
    let projectPhase = 0;
    const t0 = performance.now();
    let lastHudMs = 0;

    function applyLivePose(elapsedMs) {
      const tNorm = (elapsedMs / 8000) % 1; // 8s loop ≈ video cycle
      const sample = lerpSamples(timeSamples, tNorm);
      const orbit = elapsedMs * 0.00035;
      group.rotation.y = orbit + projectPhase * 0.15;

      // Strobe: lattice radii breathe; timeSamples offset centroid when present
      const breath = 1 + 0.12 * Math.sin(elapsedMs * 0.004 + strobeTick * 0.05);
      const pulse = membranePulse > 0 ? 1 + membranePulse * 0.35 : 1;
      const cx = sample ? sample.x * 0.35 : 0;
      const cy = sample ? sample.y * 0.35 : 0;
      const cz = sample ? sample.z * 0.35 : 0;

      group.children.forEach(function (mesh, i) {
        const b = basePositions[i];
        mesh.position.set(
          b.x * breath * pulse + cx,
          b.y * breath + cy + 0.15 * Math.sin(elapsedMs * 0.003 + i),
          b.z * breath * pulse + cz
        );
        if (mesh.material && mesh.material.emissive) {
          const glow = membranePulse > 0.05 ? membranePulse : 0.08 + 0.08 * Math.sin(elapsedMs * 0.006 + i);
          mesh.material.emissive.setHex(0x3ecf8e);
          mesh.material.emissiveIntensity = glow;
        }
      });
      rebuildEdges();
      if (membranePulse > 0) membranePulse *= 0.92;
    }

    function updateHud(elapsedMs) {
      if (elapsedMs - lastHudMs < 50 && strobeTick % 4 !== 0) return;
      lastHudMs = elapsedMs;
      const clockMs = Math.floor(elapsedMs);
      hud.setAttribute("data-strobe-tick", String(strobeTick));
      hud.setAttribute("data-clock-ms", String(clockMs));
      hud.setAttribute("data-membrane-ticks", String(membraneTicks));
      hud.setAttribute("data-time-samples", String(timeSamples.length));
      hud.setAttribute("data-orbit-y", group.rotation.y.toFixed(4));
      hud.textContent =
        "strobe=" +
        strobeTick +
        " clock=" +
        clockMs +
        "ms membrane=" +
        membraneTicks +
        " samples=" +
        timeSamples.length +
        " orbitY=" +
        group.rotation.y.toFixed(3);
      // Mirror onto viewport for CDP querySelector
      container.setAttribute("data-strobe-tick", String(strobeTick));
      container.setAttribute("data-clock-ms", String(clockMs));
      container.setAttribute("data-membrane-ticks", String(membraneTicks));
      container.setAttribute("data-realitypro-animating", strobeTick > 0 ? "1" : "0");
    }

    function tick() {
      strobeTick += 1;
      const elapsedMs = performance.now() - t0;
      applyLivePose(elapsedMs);
      updateHud(elapsedMs);
      renderer.render(scene, camera);
      raf = requestAnimationFrame(tick);
    }
    tick();

    function onResize() {
      const nw = container.clientWidth || 640;
      const nh = container.clientHeight || 420;
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
      /** Membrane project / ingest tick → visible strobe pulse + orbit phase */
      applyMembraneTick: function (info) {
        membraneTicks += 1;
        membranePulse = 1;
        projectPhase += 1;
        const detail = info && info.gameId ? String(info.gameId) : "tick";
        hud.setAttribute("data-last-membrane", detail);
        hud.setAttribute(
          "data-nats-subject",
          "gaiaftcl.game.realitypro.projection." + detail
        );
        updateHud(performance.now() - t0);
      },
      getLiveState: function () {
        return {
          strobeTick: strobeTick,
          clockMs: Math.floor(performance.now() - t0),
          membraneTicks: membraneTicks,
          timeSampleCount: timeSamples.length,
          orbitY: group.rotation.y,
          natsSubject: hud.getAttribute("data-nats-subject"),
        };
      },
    };
  }

  global.RealityProPlayer = {
    parseUsdHints: parseUsdHints,
    parseTranslateTimeSamples: parseTranslateTimeSamples,
    mount: function (container, usdaText, THREE) {
      if (!THREE) throw new Error("THREE.js not loaded");
      const hints = parseUsdHints(usdaText);
      return buildScene(THREE, container, hints, usdaText);
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
