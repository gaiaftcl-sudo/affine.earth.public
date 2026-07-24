#!/usr/bin/env python3
"""Unit test: TrafficWarnings separation engine with live-shaped tracks.

Loads traffic-warnings.js via Node (or embeds minima) and asserts:
- two aircraft inside METRO minima → SEPARATION HIGH/CRITICAL
- two aircraft outside minima → no SEPARATION
- AIRPORT_WALK uses tighter lateral (1.0 nm)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WARN_JS = ROOT / "openusd-player" / "traffic-warnings.js"


def run_js(script: str) -> dict:
    proc = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "node failed")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> int:
    if not WARN_JS.exists():
        print("MISSING", WARN_JS, file=sys.stderr)
        return 2

    harness = r"""
const fs = require('fs');
const path = %s;
const code = fs.readFileSync(path, 'utf8');
const g = globalThis;
eval(code);
const TW = g.TrafficWarnings;
const tight = [
  {icao:'aaa111', callsign:'TST1', lat:40.6413, lon:-73.7781, alt_baro_ft:3000, gs_kt:220, track_deg:90},
  {icao:'bbb222', callsign:'TST2', lat:40.6450, lon:-73.7700, alt_baro_ft:3200, gs_kt:210, track_deg:270},
];
const loose = [
  {icao:'aaa111', callsign:'FAR1', lat:40.6413, lon:-73.7781, alt_baro_ft:3000, gs_kt:220, track_deg:90},
  {icao:'bbb222', callsign:'FAR2', lat:41.1000, lon:-72.5000, alt_baro_ft:3200, gs_kt:210, track_deg:270},
];
const metro = TW.evaluate(tight, 'METRO');
const hemi = TW.evaluate(tight, 'HEMISPHERE');
const walk = TW.evaluate(tight, 'AIRPORT_WALK');
const clear = TW.evaluate(loose, 'METRO');
const out = {
  metro_sep: metro.warnings.filter(w => w.kind==='SEPARATION').length,
  hemi_sep: hemi.warnings.filter(w => w.kind==='SEPARATION').length,
  walk_sep: walk.warnings.filter(w => w.kind==='SEPARATION').length,
  clear_sep: clear.warnings.filter(w => w.kind==='SEPARATION').length,
  metro_min_lat: metro.minima.lateralNm,
  walk_min_lat: walk.minima.lateralNm,
  hemi_min_lat: hemi.minima.lateralNm,
  metro_top: metro.warnings[0] || null,
};
console.log(JSON.stringify(out));
""" % json.dumps(str(WARN_JS))

    result = run_js(harness)
    print(json.dumps(result, indent=2))

    ok = True
    if result["metro_sep"] < 1:
        print("FAIL: expected METRO separation on tight pair", file=sys.stderr)
        ok = False
    if result["walk_sep"] < 1:
        print("FAIL: expected AIRPORT_WALK separation on tight pair", file=sys.stderr)
        ok = False
    if result["clear_sep"] != 0:
        print("FAIL: loose pair should not SEPARATION", file=sys.stderr)
        ok = False
    if result["metro_min_lat"] != 3.0 or result["walk_min_lat"] != 1.0 or result["hemi_min_lat"] != 5.0:
        print("FAIL: minima table mismatch", result, file=sys.stderr)
        ok = False
    if not ok:
        return 1
    print("TRAFFIC_WARNINGS_SEPARATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
