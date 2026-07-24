# ATC OpenUSD / RealityPro narration — 2026-07-24

## Membrane ATC path

1. `GET /language-invariant/healthz` → HTTP 200 · `ok:true` · `cloud_openai:0`
2. `GET /language-invariant/games` → `aviation_atc` status **LIVE** · `ATCContextAgent` · NATS prefix `gaiaftcl.aviation.flow`
3. Teaching ingest → HTTP 200 · `CALORIE_GAME_INGEST` · `CALORIE_ATC_SECTOR_FLOW` · concept_ids present
4. Teaching project → HTTP 200 · `GYROID` · `ATC_SECTOR` / `ATC_CLEARANCE` / `AVIATION_ATC`
5. Richer clearance ingest (UAL772 VECTOR) → same CALORIE path
6. Context → `ATCContextAgent` with prior turns

## OpenUSD + RealityPro

1. `GET /language-game/airspace-lattice.usda` → HTTP 200 · `timeSamples` · `gaia:strobe=live` · `gaia:live_endpoint=out.adsb.lol:1365`
2. No ATC-specific USDA (`atc.usda` / `aviation_atc.usda` → 404) — airspace lattice is the scene
3. RealityPro HTML title contains RealityPro
4. Playwright (headless Chromium) on live RealityPro with `aviation_atc` ingest/project:
   - s1: strobe≈256 clock≈4667ms membrane=1 canvas=true
   - s2: strobe≈952 clock≈15984ms membrane=8 canvas=true
5. Screenshots: `realitypro_s1.png`, `realitypro_s2.png`

## Honest gaps

- Public HTTPS has no `/adsb` or `/tracks.json` dump (404).
- WAN live track REST is not the public teaching contract; cell ADS-B agents are steward mesh work (not re-landed here).
- observer-demo: `BLOCKED_USDKIT_NOT_LINKED_LINUX_CELL` with Swift schema apply PROVEN.
