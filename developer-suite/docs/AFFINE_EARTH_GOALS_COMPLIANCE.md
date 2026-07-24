# Affine.Earth goals compliance (measured)

**Date:** 2026-07-24  
**Scope:** public wiki + `developer-suite` (SDK, examples, Affine.Earth OpenUSD)  
**Doctrine:** Affine.Earth OS is the only model/membrane. OpenAI `/v1` = wire compatibility only.

Evidence folders:
- [`docs/receipts/atc_airport_video_20260724/`](receipts/atc_airport_video_20260724/)
- [`docs/receipts/atc_openusd_20260724/`](receipts/atc_openusd_20260724/)

| Goal | Result | Evidence |
|------|--------|----------|
| HTTPS membrane `https://affine.earth/v1` documented as OS (not cloud OpenAI) | **PASS** | `docs/OPENAI_V1.md`, README, wiki FAQ / Examples-Cookbook |
| No runnable Anthropic / OpenAI cloud recipes in wiki+SDK | **PASS** | Cloud recipes deleted or labeled HISTORICAL |
| MCP `/language-invariant/mcp` in developer surface | **PASS** | `examples/01_mcp_tools_list.py`, OpenUSD MCP button |
| Language games ingest → project → context | **PASS** | OpenUSD ingest/project + `examples/11_*` / `13_*` |
| OpenUSD URL serves OpenUSD player (not Franklin) | **PASS** | `https://affine.earth/language-game/openusd/` title `Affine.Earth OpenUSD — live ATC map` |
| USDA loads with live markers | **PASS** | `airspace-atc-world.usda` + `airspace-lattice.usda` |
| OpenUSD ATC map is time-evolving (live tracks) | **PASS** | Playwright `ac` + `liveRefresh` + nav zoom attrs |
| Trackpad/mouse zoom & pan first-class | **PASS** | `capture_openusd_nav.py` → `OPENUSD_NAV_INTERACTION_PASS` |
| Binary-free developer surface | **PASS** | `docs/NO_BINARIES.md` |
| ATC `aviation_atc` ingest → project | **PASS** | `docs/ATC_INGEST_PROJECT.md` · example 14 |
| Public HTTPS ADS-B tracks | **PASS** | `GET /language-invariant/adsb/tracks` · `adsb.lol_https_v2` · 360+ ac |
| ATC FR24-class live map | **PASS** | dark map + yellow SVG sprites · wiki `ATC-OpenUSD-Airport-App` |
| No RealityPro trademark in teaching UI | **PASS** | `/language-game/openusd/`; legacy `/realitypro/` is redirect stub only |

## Remaining gaps (honest)

1. Beast TCP `out.adsb.lol:1365` remains `FOLLOW_ON_WAN_NOT_BRIDGED` on cells — public tracks use adsb.lol HTTPS v2.
2. Historical wiki tables may still name third-party models under HISTORICAL banners.
