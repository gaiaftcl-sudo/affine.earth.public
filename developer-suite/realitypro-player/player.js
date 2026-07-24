/**
 * RealityPro-style USDA lattice preview — Three.js CDN, no vendored binaries.
 * Parses simple def Xform / points hints from USDA text for a demo mesh.
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

  function buildScene(THREE, container, hints) {
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

    scene.add(new THREE.AmbientLight(0x668888, 0.7));
    const dir = new THREE.DirectionalLight(0xffffff, 0.85);
    dir.position.set(3, 6, 2);
    scene.add(dir);

    const grid = new THREE.GridHelper(10, 20, 0x3ecf8e, 0x24343c);
    scene.add(grid);

    const group = new THREE.Group();
    scene.add(group);

    const n = Math.max(hints.length, 8);
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
      });
      const mesh = new THREE.Mesh(geo, mat);
      const angle = (i / n) * Math.PI * 2;
      const r = 1.6 + (i % 3) * 0.35;
      mesh.position.set(Math.cos(angle) * r, (i % 5) * 0.25 - 0.5, Math.sin(angle) * r);
      mesh.userData.label = hint.name;
      group.add(mesh);
    }

    // Lattice edges
    const pts = [];
    group.children.forEach(function (ch, idx) {
      const next = group.children[(idx + 1) % group.children.length];
      pts.push(ch.position.clone(), next.position.clone());
    });
    const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
    const line = new THREE.LineSegments(
      lineGeo,
      new THREE.LineBasicMaterial({ color: 0x4a7a88, transparent: true, opacity: 0.55 })
    );
    scene.add(line);

    let raf = 0;
    function tick() {
      group.rotation.y += 0.004;
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
      },
      hintCount: hints.length,
    };
  }

  global.RealityProPlayer = {
    parseUsdHints: parseUsdHints,
    mount: function (container, usdaText, THREE) {
      if (!THREE) throw new Error("THREE.js not loaded");
      const hints = parseUsdHints(usdaText);
      return buildScene(THREE, container, hints);
    },
  };
})(typeof window !== "undefined" ? window : globalThis);
