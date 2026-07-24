/**
 * Teaching seeds for all 12 LIVE games — mirrors affine_earth_sdk/game_seeds.py
 * Used by Affine.Earth OpenUSD ingest/project so the player exercises real domain payloads.
 */
(function (global) {
  "use strict";

  function amps() {
    return ["3/5", "4/5"];
  }

  function teachingSeed(gameId, sessionSuffix) {
    const gid = String(gameId || "coding").toLowerCase();
    const s = (sessionSuffix || "openusd") + "-" + gid;
    const table = {
      cinema: {
        film_id: "affine-horizon",
        title: "Affine Horizon — teaching reel",
        characters: ["Franklin", "Steward", "Observer"],
        structural_bound: "FEATURE_LENGTH",
        H_start: "0/1",
        H_end: "1/1",
        node_id: "apex",
        session_id: s,
        tau_height: 0,
        amplitudes: amps(),
        locale: "en",
        statement: "Narrative manifold seed for cinema teaching example",
      },
      aviation: {
        role: "AVIATION_PILOT",
        flight_id: "GAIA001",
        node_id: "apex",
        session_id: s,
        tau_height: 0,
        amplitudes: amps(),
        title: "Pilot role matrix teaching flight",
        locale: "en",
      },
      aviation_atc: {
        sector_id: "ZNY-42",
        callsign: "GAIA001",
        clearance_kind: "CLIMB",
        node_id: "apex",
        session_id: s,
        tau_height: 0,
        amplitudes: amps(),
        title: "ATC sector flow teaching clearance",
        locale: "en",
      },
      gaming: {
        session_id: s,
        node_id: "apex",
        title: "rule-desync teaching match",
        layer_labels: ["RULE_VIOLATION", "DESYNC"],
        amplitudes: amps(),
        tau_height: 0,
        locale: "en",
      },
      coding: {
        session_id: s,
        node_id: "apex",
        title: "affine_add_app — teaching coding application",
        workspace_hint: "fixtures/coding/affine_add_app",
        amplitudes: amps(),
        tau_height: 0,
        statement: "Long-play coding: ingest affine_add_app then project compile narrative",
        locale: "en",
      },
      reality: {
        room_id: "room-teach",
        presence_id: "presence-teach-1",
        node_id: "apex",
        torsion_num: 0,
        torsion_den: 1,
        session_id: s,
        amplitudes: amps(),
        title: "Reality immersion teaching room",
        locale: "en",
      },
      topological_sandbox: {
        action: "heal",
        torsion_num: 0,
        torsion_den: 1,
        node_id: "apex",
        session_id: s,
        amplitudes: amps(),
        title: "Sandbox heal teaching stroke",
        locale: "en",
      },
      formal_manifold: {
        domain: "coding",
        amplitudes: amps(),
        statement: "2+2 collapses to 4 on the formal manifold",
        node_id: "apex",
        tau_height: 0,
        session_id: s,
        title: "Formal observer teaching collapse",
        locale: "en",
      },
      wallet_qfot: {
        address: "bc1qaffineearthteach0000000000000000000",
        lat_micro: 40712800,
        lon_micro: -74006000,
        amount_num: 0,
        amount_den: 1,
        domain: "coding",
        node_id: "apex",
        session_id: s,
        amplitudes: ["1/1", "0/1"],
        title: "Wallet/QFOT teaching bind (zero transfer)",
        locale: "en",
      },
      linguistic_membrane: {
        intent: "OPEN_CURVE",
        scf_hash: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        user_vqbit_hash: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        vqbit_signature: "cccccccccccccccccccccccccccccccc",
        locale: "en",
        node_id: "apex",
        session_id: s,
        amplitudes: amps(),
        title: "Linguistic membrane teaching turn envelope",
      },
      umc_gav: {
        domain: "coding",
        session_id: s,
        node_id: "apex",
        title: "UMC GAV teaching long play",
        max_turns: 8,
        tau_height: 0,
        amplitudes: amps(),
        locale: "en",
      },
      torsion_dialogue: {
        room_id: "room-teach",
        agreement: 1,
        operator_tensor: "AGREE",
        node_id: "apex",
        session_id: s,
        amplitudes: amps(),
        title: "Torsion dialogue agreement fuse",
        locale: "en",
      },
    };
    return table[gid] || {
      node_id: "apex",
      session_id: s,
      title: "openusd-" + gid,
      tau_height: 0,
      amplitudes: amps(),
    };
  }

  global.TeachingSeeds = { teachingSeed: teachingSeed };
})(typeof window !== "undefined" ? window : globalThis);
