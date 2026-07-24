/**
 * UUM8D language-game shell — games catalog, ingest/project, MCP health.
 * Same-origin when deployed under /language-game/openusd/; else set apex.
 */
(function (global) {
  "use strict";

  function apexBase() {
    const q = new URLSearchParams(location.search).get("apex");
    if (q) return q.replace(/\/$/, "");
    // When served from language-game/openusd on affine.earth → same origin
    if (location.hostname.endsWith("affine.earth") || location.hostname.endsWith("gaiaftcl.com")) {
      return location.origin;
    }
    return "https://affine.earth";
  }

  async function jget(path) {
    const r = await fetch(apexBase() + path, { credentials: "omit" });
    const text = await r.text();
    let body;
    try {
      body = JSON.parse(text);
    } catch (_) {
      body = { raw: text.slice(0, 500) };
    }
    if (!r.ok) throw new Error(path + " → " + r.status + " " + JSON.stringify(body).slice(0, 200));
    return body;
  }

  async function jpost(path, obj) {
    const r = await fetch(apexBase() + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj || {}),
      credentials: "omit",
    });
    const text = await r.text();
    let body;
    try {
      body = JSON.parse(text);
    } catch (_) {
      body = { raw: text.slice(0, 500) };
    }
    if (!r.ok) throw new Error(path + " → " + r.status + " " + JSON.stringify(body).slice(0, 200));
    return body;
  }

  async function loadGames() {
    return jget("/language-invariant/games");
  }

  async function ingest(gameId, seed) {
    return jpost("/language-invariant/game/" + encodeURIComponent(gameId) + "/ingest", seed);
  }

  async function project(gameId, seed) {
    return jpost("/language-invariant/game/" + encodeURIComponent(gameId) + "/project", seed);
  }

  async function mcpTools() {
    return jpost("/language-invariant/mcp", {
      jsonrpc: "2.0",
      id: 1,
      method: "tools/list",
      params: {},
    });
  }

  async function umcDirect(domain) {
    return jpost("/language-invariant/umc/direct", {
      domain: domain || "coding",
      session_id: "openusd",
      node_id: "apex",
      title: "openusd-player",
      tau_height: 0,
      max_turns: 8,
    });
  }

  async function fetchUsda(path) {
    const p = path || "/language-game/airspace-atc-world.usda";
    const r = await fetch(apexBase() + p);
    if (!r.ok) throw new Error("USDA " + r.status);
    return r.text();
  }

  /**
   * Live ADS-B tracks from Affine.Earth OS membrane (adsb.lol HTTPS via cell helper).
   * Not authored timeSamples. Not a mock generator.
   */
  async function fetchLiveTracks(opts) {
    const o = opts || {};
    const icao = o.icao || "KJFK";
    const dist = o.dist != null ? o.dist : 80;
    const force = !!o.force;
    // Prefer static mirror (Caddy) — avoids hammering upstream adsb.lol (HTTP 420).
    if (!force) {
      try {
        const cached = await jget("/language-game/tracks.json");
        if (cached && intOr(cached.aircraft_count, 0) > 0) return cached;
      } catch (_) {}
    }
    const path =
      "/language-invariant/adsb/tracks?icao=" +
      encodeURIComponent(icao) +
      "&dist=" +
      encodeURIComponent(String(dist)) +
      (force ? "&force=1" : "");
    return jget(path);
  }

  /**
   * Swift OS UUM8D zoom projection — source of truth for band + tracks + warnings.
   * Browser remains a thin viewport; do not recompute separation here when this lands.
   */
  async function fetchUUM8DZoomProjection(opts) {
    const o = opts || {};
    const icao = o.icao || "KJFK";
    const zoom = Number(o.zoom);
    const zoomMilli =
      o.zoom_milli != null
        ? intOr(o.zoom_milli, 220)
        : Math.round((isNaN(zoom) ? 0.22 : zoom) * 1000);
    const path =
      "/language-invariant/airspace/uum8d-zoom?zoom_milli=" +
      encodeURIComponent(String(zoomMilli)) +
      "&icao=" +
      encodeURIComponent(icao);
    return jget(path);
  }

  function intOr(v, d) {
    const n = parseInt(v, 10);
    return isNaN(n) ? d : n;
  }

  global.UUM8DShell = {
    apexBase: apexBase,
    loadGames: loadGames,
    ingest: ingest,
    project: project,
    mcpTools: mcpTools,
    umcDirect: umcDirect,
    fetchUsda: fetchUsda,
    fetchLiveTracks: fetchLiveTracks,
    fetchUUM8DZoomProjection: fetchUUM8DZoomProjection,
  };
})(typeof window !== "undefined" ? window : globalThis);
