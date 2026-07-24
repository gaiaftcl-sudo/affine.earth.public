# Affine.Earth OpenUSD — UUM8D manifold ATC map

**Product:** [Affine.Earth OpenUSD](https://affine.earth/language-game/openusd/) — **UUM8D lossless manifold zoom**, yellow heading-aware SVG sprites, airport focus, **live ADS-B only**. Not RealityPro.

**Physics:** Observer zoom is a fiber on S⁴/UUM8D staging bands. Crossing a band threshold swaps map skin + traffic LOD + label density (crossfade). Not a CSS `scale()` that pixelates.

**Target look:** professional dark / regional / metro / airport-diagram skins with live traffic density that thickens as you zoom in.

---

## Manifold bands (thresholds)

| Band | Zoom | Skin | Traffic LOD |
|:---|:---|:---|:---|
| `HEMISPHERE` | `[0, 0.42)` | `map-hemisphere.css` | max 48 · ≥18k ft · thin stride 4 · fetch ~900 nm |
| `REGIONAL` | `[0.42, 1.15)` | `map-regional.css` | max 120 · ≥8k ft · stride 2 · ~350 nm |
| `METRO` | `[1.15, 3.60)` | `map-metro.css` | max 220 · all alt · ~120 nm |
| `AIRPORT_WALK` | `[3.60, 14]` | `map-airport.css` | max 160 · prefer arrivals/ground · ~45 nm · high pan sense |

Boot stage = **HEMISPHERE**. `⌖` jumps to airport walk; `◎` returns to hemisphere.

---

## How to zoom / pan

| Input | Action |
|:---|:---|
| Scroll wheel / two-finger scroll | Zoom toward cursor (smooth lerp across bands) |
| Pinch (trackpad → `ctrl`+wheel / Safari gesture) | Zoom toward cursor |
| Click-drag / space-drag / touch-drag | Pan (higher sensitivity in `AIRPORT_WALK`) |
| Shift+wheel or dominant horizontal wheel | Pan |
| Double-click / double-tap | Zoom in at point |
| Shift + double-click | Zoom out at point |
| Airport buttons (KJFK, EGLL, …) | Focus ICAO + live tracks (METRO entry) |
| `+` / `−` / `⌖` / `◎` | Zoom in / out / airport walk / hemisphere |

HUD shows: **band name · zoom rational · lod track count · focus ICAO**.

---

## Screen video — manifold bands (hemisphere → airport walk)

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/our_app_fr24_look.png">
  <source src="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-manifold-bands.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-manifold-bands.webm" type="video/webm">
  <source src="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-nav-interaction.mp4" type="video/mp4">
</video>
</p>

- Manifold bands: [mp4](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-manifold-bands.mp4) · [webm](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-manifold-bands.webm)
- Nav interaction: [mp4](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-nav-interaction.mp4)
- Receipt: [`developer-suite/docs/receipts/atc_airport_video_20260724/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/developer-suite/docs/receipts/atc_airport_video_20260724) · `capture_manifold_bands.py` → `OPENUSD_MANIFOLD_BANDS_PASS`

---

## Look comparison — FR24 target vs our app

| | |
|:---|:---|
| **FR24 reference (target look)** | ![FR24 reference](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/fr24-reference-target.png) |
| **Affine.Earth OpenUSD ATC LIVE** | ![Our app](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/our_app_fr24_look.png) |

Shared visual contract: dark map chrome · bright yellow plane silhouettes · rotation by live heading · dense traffic · airport-focused zoom + manual nav.

---

## Open the app

```text
https://affine.earth/language-game/openusd/
```

1. Boot lands on **HEMISPHERE** (planetary skin + thinned major flows)
2. Scroll / pinch in → REGIONAL → METRO → **AIRPORT_WALK** (traffic LOD densifies)
3. Or click **⌖** for airport walk / **◎** for hemisphere / airport ICAO buttons for focus
4. USDA stage: `/language-game/airspace-atc-world.usda`
5. Game `aviation_atc` → Ingest / Project seals membrane CALORIE alongside the map
6. HUD: manifold band · zoom rational · `lod_ac` · focus ICAO

## Weather + solar + warnings

| Layer | Source | Notes |
|:---|:---|:---|
| Solar terminator / elevation | **Computed** from UTC + lat/lon | Always on; hemisphere LOD emphasizes terminator |
| Synoptic cloud/precip stylization | Affine canvas (not FR24 art) | LOD by band; **not** claimed as live NOAA radar |
| NOAA / METAR membrane | `GET /language-invariant/economics-config` → `live_feeds.noaa_weather` | Often `BLOCKED_NOAA_WEATHER_FEED` / `BLOCKED_FOLLOW_ON` — HUD shows honest status |
| Aircraft | Live ADS-B membrane | Unchanged |
| Separation / anomaly warnings | `traffic-warnings.js` on each live snapshot | Colored panel + conflict lines |

### Separation minima (band-pegged)

| Band | Lateral | Vertical | Label |
|:---|:---|:---|:---|
| HEMISPHERE | 5.0 nm | 1000 ft | enroute |
| REGIONAL | 5.0 nm | 1000 ft | corridor |
| METRO | 3.0 nm | 1000 ft | terminal |
| AIRPORT_WALK | 1.0 nm | 500 ft | airport |

Closing-speed alert when range &lt; 1.5× lateral minimum and vertical also tight. Severity: CRITICAL / HIGH / MEDIUM / LOW. Anomalies: unreasonable GS vs altitude / airport-walk speed.

### UI how-to

1. Open https://affine.earth/language-game/openusd/ — boot **HEMISPHERE** (terminator + synoptic cue)
2. WARNINGS panel (top-right): live count badge + minima line + messages
3. Zoom in: weather LOD shifts to local METAR chip / wind cue; traffic densifies; minima tighten at AIRPORT_WALK
4. Conflict pairs draw colored lines between aircraft when separation breaches

Prove: `capture_wx_warnings.py` → `OPENUSD_WX_WARNINGS_PASS` · unit `tests/test_traffic_warnings_separation.py`

### Honest gaps

- Basemap is Affine-branded **procedural canvas** (continents + runway diagram), not WebMercator raster tiles.
- True airport CAD / IFR charts are not ingested; walk mode uses diagram-quality runway/taxi overlay.
- NOAA radar/METAR live ingest remains membrane-blocked — solar is computed; weather overlay is stylized + status-honest, not fake radar.

---

## Live data source (exact)

| Surface | Role |
|:---|:---|
| `GET /language-invariant/adsb/tracks?icao=KJFK&dist=80` | Live membrane read |
| `GET /language-game/tracks.json` | Cell poller mirror (preferred by player) |
| Upstream | `https://api.adsb.lol/v2/...` — live community ADS-B |
| Beast TCP `out.adsb.lol:1365` | `FOLLOW_ON_WAN_NOT_BRIDGED` on cells |
| Motion | Sprites move when live snapshots refresh — **no authored loop** |

### Prove

```bash
curl -sS 'https://affine.earth/language-invariant/adsb/tracks?icao=KJFK&dist=80' \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["aircraft_count"], d["source"], d.get("error"))'
curl -sS -o /dev/null -w "%{http_code}\n" https://affine.earth/language-game/openusd/
```

SDK: [`docs/ATC_INGEST_PROJECT.md`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/developer-suite/docs/ATC_INGEST_PROJECT.md) · example `14_atc_ingest_project_openusd.py`
