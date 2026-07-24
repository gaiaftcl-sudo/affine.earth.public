# ATC LIVE OpenUSD / RealityPro — 2026-07-24

## Live data source
- **Primary:** `GET https://affine.earth/language-invariant/adsb/tracks?icao=KJFK&dist=80`
- **Upstream:** `https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{nm}` (live community ADS-B)
- **Cell bridge:** `language-inject-helper.py` poller on all 9 cells (Affine.Earth OS membrane)
- **Static mirrors:** `/language-game/tracks.json`, `lattice-snapshot.json`
- **Beast TCP** `out.adsb.lol:1365`: `FOLLOW_ON_WAN_NOT_BRIDGED` (not used for this surface)

## Scene
- Focus airport: **KJFK**
- USDA stage: `/language-game/airspace-atc-world.usda` (airport + world markers only)
- Aircraft: projected from live track JSON into RealityPro Three.js (no authored aircraft loop)
- Camera: one-shot zoom into KJFK, then hold while live polls refresh (~2.5s)

## Prove
```bash
curl -sS 'https://affine.earth/language-invariant/adsb/tracks?icao=KJFK&dist=80' | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["aircraft_count"], d["source"], d.get("error"))'
# measured: 370+ aircraft, source=adsb.lol_https_v2, error=None
```

## Video
- `atc-kjfk-live-tracks.webm` / `.mp4` in this receipt + `wiki/assets/videos/`
