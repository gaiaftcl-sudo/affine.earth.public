# ATC ingest + project + OpenUSD (third-party SDK)

Build ATC sector-flow solutions **and** the live airport [Affine.Earth OpenUSD](https://affine.earth/language-game/openusd/) scene on **Affine.Earth OS**.  
Engine = Affine.Earth OS at `https://affine.earth`. OpenAI `/v1` is wire shape only — **not** cloud OpenAI/Anthropic.

**Measured:** 2026-07-24 · evidence in [`receipts/atc_airport_video_20260724/`](receipts/atc_airport_video_20260724/) · [`receipts/atc_openusd_20260724/`](receipts/atc_openusd_20260724/)

## What is live on the public membrane

| Surface | Path | Measured |
|---------|------|----------|
| Health | `GET /language-invariant/healthz` | HTTP 200 · `ok:true` · `cloud_openai:0` · `adsb_tracks:true` |
| Games catalog | `GET /language-invariant/games` | `aviation_atc` **LIVE** · `ATCContextAgent` |
| ATC ingest | `POST /language-invariant/game/aviation_atc/ingest` | HTTP 200 · `CALORIE_GAME_INGEST` · `CALORIE_ATC_SECTOR_FLOW` |
| ATC project | `POST /language-invariant/game/aviation_atc/project` | HTTP 200 · `GYROID` · kinds `AVIATION_ATC` / `ATC_SECTOR` / `ATC_CLEARANCE` |
| ATC context | `GET /language-invariant/game/aviation_atc/context` | HTTP 200 · prior turns + payload shape |
| **Live ADS-B tracks** | `GET /language-invariant/adsb/tracks?icao=KJFK&dist=80` | HTTP 200 · `gaia.airspace_tracks.v1` · **360+ aircraft** · `source=adsb.lol_https_v2` |
| Tracks mirror | `GET /language-game/tracks.json` | HTTP 200 · same schema (cell poller mirror) |
| OpenUSD ATC stage | `GET /language-game/airspace-atc-world.usda` | HTTP 200 · KJFK framing + world markers (no authored aircraft loop) |
| OpenUSD lattice | `GET /language-game/airspace-lattice.usda` | HTTP 200 · cell lattice |
| Affine.Earth OpenUSD | `https://affine.earth/language-game/openusd/` | HTTP 200 · live tracks → Three.js · wheel/pinch/pan · HUD zoom + ac count |
| NATS-shaped subjects | `gaiaftcl.aviation.adsb.tracks` · `gaiaftcl.aviation.flow.*` | Returned on tracks / ingest |

Concept kinds (catalog): `AVIATION_ATC`, `ATC_SECTOR`, `ATC_CLEARANCE`.  
Payload shape: `sector_id,callsign,clearance_kind,node_id,tau_height` (+ optional richer fields accepted on ingest).

## Live data path (exact)

1. Cell `language-inject-helper` polls **live** `https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{nm}` (same org as Beast `out.adsb.lol:1365`).
2. Serves `GET /language-invariant/adsb/tracks` and mirrors `tracks.json` / `lattice-snapshot.json` under `/language-game/`.
3. OpenUSD player loads USDA stage (`airspace-atc-world.usda`) for **KJFK** airport framing, then projects aircraft from track JSON — **positions advance when live snapshots refresh**, not from authored timeSamples loops. Manual scroll/pinch/drag is first-class.
4. `aviation_atc` ingest/project still seals membrane CALORIE alongside the live scene.

**Honest:** Beast TCP `out.adsb.lol:1365` remains `FOLLOW_ON_WAN_NOT_BRIDGED` on cells. Public track surface is **adsb.lol HTTPS v2 via OS helper** — not a mock generator. On HTTP 420 rate-limit, helper serves **stale-while-revalidate** last good snapshot when available.

### Prove non-empty live aircraft

```bash
curl -sS 'https://affine.earth/language-invariant/adsb/tracks?icao=KJFK&dist=80' \
  | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d["aircraft_count"], d["source"], d.get("error"))'
# measured: 360+  adsb.lol_https_v2  None
```

## SDK install

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public/developer-suite
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # AFFINE_BASE_URL=https://affine.earth
```

## One-command recipe (ran)

```bash
python3 examples/14_atc_ingest_project_openusd.py
# → ATC_INGEST_PROJECT_OPENUSD_PASS
```

## curl recipe (ran)

```bash
# Live tracks
curl -sS 'https://affine.earth/language-invariant/adsb/tracks?icao=KJFK&dist=80' | python3 -m json.tool | head

# Teaching ingest
curl -sS -X POST https://affine.earth/language-invariant/game/aviation_atc/ingest \
  -H 'Content-Type: application/json' \
  -d '{"sector_id":"ZNY-42","callsign":"GAIA001","clearance_kind":"CLIMB","node_id":"apex","session_id":"atc-doc","tau_height":0,"amplitudes":["3/5","4/5"],"title":"ATC sector flow teaching clearance","locale":"en"}'

# OpenUSD ATC stage
curl -sS https://affine.earth/language-game/airspace-atc-world.usda | head -40
```

## OpenUSD play instructions

```text
https://affine.earth/language-game/openusd/
```

1. USDA path = `/language-game/airspace-atc-world.usda` → **Load USDA** (or **ATC map scene**)
2. Scroll / pinch to zoom · drag / space-drag to pan · double-click zoom · airport buttons for quick focus
3. Game select = `aviation_atc` → Ingest → Project (membrane ticks)
4. Viewport HUD: focus ICAO · `ac=` live count · `zoom=` · `liveRefresh` advances with snapshots

**Screen video:** [`receipts/atc_airport_video_20260724/`](receipts/atc_airport_video_20260724/) · wiki [ATC OpenUSD Airport App](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/ATC-OpenUSD-Airport-App)

## Related docs

- [DOMAINS.md](DOMAINS.md) — Aviation / ATC row
- [OPENUSD_AND_REALITYPRO.md](OPENUSD_AND_REALITYPRO.md) — live 3D player
- [LANGUAGE_GAMES_TEACHING.md](LANGUAGE_GAMES_TEACHING.md) — `aviation_atc` teaching PASS
- [AFFINE_EARTH_GOALS_COMPLIANCE.md](AFFINE_EARTH_GOALS_COMPLIANCE.md) — compliance table
