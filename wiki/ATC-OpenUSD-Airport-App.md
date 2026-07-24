# Affine.Earth OpenUSD — live ATC map

**Product:** [Affine.Earth OpenUSD](https://affine.earth/language-game/openusd/) — dark geographic map, **yellow heading-aware SVG plane sprites**, airport focus, **live ADS-B only**, trackpad/mouse zoom & pan.

**Target look:** Flightradar24-class live map (dark basemap + dense yellow aircraft). Not a sparse 3D lattice demo.

---

## How to zoom / pan

| Input | Action |
|:---|:---|
| Scroll wheel / two-finger scroll | Zoom toward cursor (smooth lerp) |
| Pinch (trackpad → `ctrl`+wheel / Safari gesture) | Zoom toward cursor |
| Click-drag / space-drag / touch-drag | Pan |
| Shift+wheel or dominant horizontal wheel | Pan |
| Double-click / double-tap | Zoom in at point |
| Shift + double-click | Zoom out at point |
| Airport buttons (KJFK, EGLL, …) | Quick-zoom focus + live tracks |
| `+` / `−` / `⌖` | Zoom in / out / fit airport |

Sprites stay heading-correct while you navigate; size scales slightly with zoom so dense traffic stays readable.

---

## Screen video — live map + nav

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/our_app_fr24_look.png">
  <source src="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-nav-interaction.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-nav-interaction.webm" type="video/webm">
  <source src="https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/atc-fr24-live-map.mp4" type="video/mp4">
</video>
</p>

- Nav interaction: [mp4](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-nav-interaction.mp4) · [webm](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/openusd-nav-interaction.webm)
- Live map: [mp4](https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/videos/atc-fr24-live-map.mp4)
- Receipt: [`developer-suite/docs/receipts/atc_airport_video_20260724/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/developer-suite/docs/receipts/atc_airport_video_20260724)

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

1. Click an airport (**KJFK / EGLL / EHAM / LFPG / …**)
2. Use trackpad/mouse zoom & pan (or **+ / − / ⌖**)
3. USDA stage: `/language-game/airspace-atc-world.usda`
4. Game `aviation_atc` → Ingest / Project seals membrane CALORIE alongside the map
5. HUD: airport focus · live track count · zoom level

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
