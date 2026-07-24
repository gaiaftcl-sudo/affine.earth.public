# ATC ingest + project + OpenUSD (third-party SDK)

Build ATC sector-flow solutions on the live **Affine.Earth OS** membrane.  
Engine = Affine.Earth OS at `https://affine.earth`. OpenAI `/v1` is wire shape only — **not** cloud OpenAI/Anthropic.

**Measured:** 2026-07-24 · evidence in [`receipts/atc_openusd_20260724/`](receipts/atc_openusd_20260724/) · compliance [`receipts/atc_sdk_validation_20260724.json`](receipts/atc_sdk_validation_20260724.json)

## What is live on the public membrane

| Surface | Path | Measured |
|---------|------|----------|
| Health | `GET /language-invariant/healthz` | HTTP 200 · `ok:true` · `cloud_openai:0` |
| Games catalog | `GET /language-invariant/games` | `aviation_atc` **LIVE** · `ATCContextAgent` |
| ATC ingest | `POST /language-invariant/game/aviation_atc/ingest` | HTTP 200 · `CALORIE_GAME_INGEST` · `CALORIE_ATC_SECTOR_FLOW` |
| ATC project | `POST /language-invariant/game/aviation_atc/project` | HTTP 200 · `GYROID` · kinds `AVIATION_ATC` / `ATC_SECTOR` / `ATC_CLEARANCE` |
| ATC context | `GET /language-invariant/game/aviation_atc/context` | HTTP 200 · prior turns + payload shape |
| OpenUSD airspace | `GET /language-game/airspace-lattice.usda` | HTTP 200 · `timeSamples` · `gaia:strobe=live` |
| RealityPro | `https://affine.earth/language-game/realitypro/` | HTTP 200 · Playwright strobe/membrane advanced |
| NATS-shaped subjects | `gaiaftcl.aviation.flow.*` · `gaiaftcl.reality.manifold.realitypro.apex` | Returned on ingest / USDA |

Concept kinds (catalog): `AVIATION_ATC`, `ATC_SECTOR`, `ATC_CLEARANCE`.  
Payload shape: `sector_id,callsign,clearance_kind,node_id,tau_height` (+ optional richer fields accepted on ingest).

## Honest gap — ADS-B track dump vs sector-flow CALORIE

Cell-side multi-cell ADS-B ingest (`AffineAirspaceIngestAgent`) is steward territory (already sealed on cells 1…9). The **public HTTPS teaching membrane** validated here:

- **PASS:** ATC language-game ingest → project → context (CALORIE sector flow).
- **PASS:** OpenUSD airspace lattice + RealityPro live 3D projection path.
- **NOT exposed on public HTTPS (measured 404):** `/language-invariant/adsb`, `/language-game/adsb.json`, `/language-game/tracks.json`, ATC-specific USDA (`atc.usda`, `aviation_atc.usda`).
- USDA declares `gaia:live_endpoint = "out.adsb.lol:1365"` as the airspace lattice live endpoint annotation — that is **not** a public REST track feed on `affine.earth`.
- `GET /language-invariant/observer-demo` returns geographic observer bind **PROVEN** with `BLOCKED_USDKIT_NOT_LINKED_LINUX_CELL` (USDKit C++ on Linux cell) while Swift schema apply is `PROVEN_SWIFT_SCHEMA_APPLY`.

Do **not** claim a public REST “live tracks JSON” API from this surface. Claim the measured contract: **ATC Concept_ID calorie path + OpenUSD airspace strobe**.

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

Also:

```bash
python3 examples/games/aviation_atc.py
python3 examples/10_openusd_airspace_fetch.py
```

## curl recipe (ran)

```bash
# Catalog
curl -sS https://affine.earth/language-invariant/games | python3 -m json.tool | head

# Teaching ingest
curl -sS -X POST https://affine.earth/language-invariant/game/aviation_atc/ingest \
  -H 'Content-Type: application/json' \
  -d '{"sector_id":"ZNY-42","callsign":"GAIA001","clearance_kind":"CLIMB","node_id":"apex","session_id":"atc-doc","tau_height":0,"amplitudes":["3/5","4/5"],"title":"ATC sector flow teaching clearance","locale":"en"}'

# Project
curl -sS -X POST https://affine.earth/language-invariant/game/aviation_atc/project \
  -H 'Content-Type: application/json' \
  -d '{"sector_id":"ZNY-42","callsign":"GAIA001","clearance_kind":"CLIMB","node_id":"apex","session_id":"atc-doc","tau_height":0,"amplitudes":["3/5","4/5"],"title":"ATC sector flow teaching clearance","locale":"en"}'

# Context
curl -sS https://affine.earth/language-invariant/game/aviation_atc/context | python3 -m json.tool | head

# OpenUSD
curl -sS https://affine.earth/language-game/airspace-lattice.usda | head -40
```

Teaching seed builder: `affine_earth_sdk.game_seeds.teaching_seed("aviation_atc")`.

## Binding ATC project → OpenUSD / RealityPro

There is **no** separate ATC USDA on the apex today (404). The binding is:

1. `POST .../aviation_atc/ingest|project` seals sector-flow Concept_IDs and returns `nats_subject` under `gaiaftcl.aviation.flow.*`.
2. RealityPro loads `/language-game/airspace-lattice.usda` (`gaia.airspace_lattice.v1`, cell xforms, `timeSamples`, `gaia:strobe=live`).
3. Each ingest/project in the player calls `applyMembraneTick()` → visible lattice pulse (video-like).
4. Auto-strobe projects the selected game (set `aviation_atc`) every ~2.5s.

Open:

```text
https://affine.earth/language-game/realitypro/
```

Local:

```bash
cd realitypro-player && python3 -m http.server 8765
# http://127.0.0.1:8765/?apex=https://affine.earth
```

## Building an ATC product on this contract

1. **Ingest** clearances / sector events as `aviation_atc` seeds (not free-text chat dumps).
2. **Project** to obtain locale Concept_IDs (`ATC_SECTOR@en`, …) and Gyroid primitive.
3. **Context** for language-game next-move / prior turns (§0.16).
4. **Scene:** fetch airspace USDA; drive RealityPro or your own OpenUSD consumer with membrane ticks after each project.
5. **Mesh ADS-B:** use cell-sealed airspace agents / NATS `gaiaftcl.*` on the OS mesh — outside this public REST teaching surface; do not invent mock tracks.

## Related docs

- [DOMAINS.md](DOMAINS.md) — Aviation / ATC row
- [OPENUSD_AND_REALITYPRO.md](OPENUSD_AND_REALITYPRO.md) — live 3D player
- [LANGUAGE_GAMES_TEACHING.md](LANGUAGE_GAMES_TEACHING.md) — `aviation_atc` teaching PASS
- [AFFINE_EARTH_GOALS_COMPLIANCE.md](AFFINE_EARTH_GOALS_COMPLIANCE.md) — compliance table
