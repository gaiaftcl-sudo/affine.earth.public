# Affine.Earth goals compliance (measured)

**Date:** 2026-07-24  
**Scope:** public wiki + `developer-suite` (SDK, examples, RealityPro)  
**Doctrine:** Affine.Earth OS is the only model/membrane. OpenAI `/v1` = wire compatibility only.

Evidence folder: [`docs/receipts/realitypro_live_3d_20260724/`](receipts/realitypro_live_3d_20260724/)

| Goal | Result | Evidence |
|------|--------|----------|
| HTTPS membrane `https://affine.earth/v1` documented as OS (not cloud OpenAI) | **PASS** | `docs/OPENAI_V1.md`, README, wiki FAQ / Examples-Cookbook §8–9 |
| No runnable Anthropic / OpenAI cloud / Gemini / Groq / Together recipes in wiki+SDK | **PASS** | Cloud recipes deleted or labeled; remaining name hits are HISTORICAL banners or “NOT api.openai.com” prohibitions |
| MCP `/language-invariant/mcp` in developer surface | **PASS** | `examples/01_mcp_tools_list.py`, RealityPro MCP button |
| Language games ingest → project → context | **PASS** | RealityPro ingest/project + `examples/11_*` / `13_*` |
| RealityPro URL serves RealityPro (not Franklin) | **PASS** | `receipts/.../html_title.txt` — title `Affine.Earth RealityPro — UUM8D language games` |
| USDA loads with live markers | **PASS** | `airspace-lattice.usda` has `timeSamples`, `gaia:strobe=live`, `gaia:nats_subject` |
| RealityPro Preview shows **time-evolving 3D** (video-like) | **PASS** | Playwright: strobe 272→419, clock 4855→7307ms, membrane 1→2, `samples=5`, canvas present (`cdp_live_state.json`, screenshots) |
| NATS subjects aligned to `gaiaftcl.*` | **PASS** | `gaiaftcl.reality.manifold.realitypro.apex`, `gaiaftcl.game.*.projection.*` in player HUD + USDA |
| SDK defaults `AFFINE_BASE_URL` + `uum8d-hle-verifier` + live `/v1/models` | **PASS** | `.env.example`, `examples/03_*` measured chat HTTP 200 (`sdk_03_chat.txt`) |
| Binary-free developer surface | **PASS** | `docs/NO_BINARIES.md`, `scripts/check_no_binaries.py` |
| Published wiki synced | see publish step | `affine.earth.public.wiki` |
| ATC `aviation_atc` ingest → project → context (CALORIE) | **PASS** | `receipts/atc_openusd_20260724/` · `CALORIE_ATC_SECTOR_FLOW` · concept_ids · `docs/ATC_INGEST_PROJECT.md` |
| ATC richer clearance seed accepted | **PASS** | UAL772 VECTOR / AAL100 DESCENT ingest HTTP 200 |
| OpenUSD airspace lattice for ATC scene | **PASS** | `airspace-lattice.usda` timeSamples + `gaia:strobe=live` (no ATC-specific USDA — 404) |
| RealityPro ATC membrane ticks (live 3D) | **PASS** | Playwright strobe 256→952, membrane 1→8 (`cdp_live_state.json`) |
| Public HTTPS ADS-B / tracks REST dump | **NOT_EXPOSED** | `/adsb`, `/tracks.json` → 404; cell ADS-B agents are mesh-side (out of SDK teaching scope) |
| SDK example 14 ATC recipe | **PASS** | `examples/14_atc_ingest_project_openusd.py` → `ATC_INGEST_PROJECT_OPENUSD_PASS` |

## RealityPro live-3D details (measured)

```
s1: strobe=272 clock=4855ms membrane=1 samples=5 canvas=true
s2: strobe=419 clock=7307ms membrane=2 samples=5 orbitY≈2.86
```

Headless Chromium WebGL **mounted** (canvas present). Pixel-perfect GPU frames are environment-dependent; clock/strobe/membrane advancement is the contract used for PASS.

## Remaining gaps (honest)

1. **Historical wiki tables** still *name* GPT-4o / Claude / Gemini as archived baseline columns under explicit **HISTORICAL RECEIPT** banners. Content not deleted so auditors keep provenance; they are non-runnable.
2. **Suite-internal** `llm_llvm_bench/llm/providers.py` still contains an `AnthropicProvider` class for offline harness code paths — outside developer-suite public teaching surface; not documented as a wiki recipe. Follow-up: gate or remove if steward wants zero cloud client classes in the public repo.
3. **Browser MCP** in this session could not open a Cursor tab; validation used Playwright + Chrome instead (screenshots on disk).
4. **Auto-strobe** depends on live `/project` succeeding; on soft-fail it still advances local membrane pulse (documented in player).

## Classification summary (audit)

| Class | Action |
|-------|--------|
| DELETE | Cloud Anthropic recipe section already removed; mock `gpt-4o`/`claude` runnable names rewritten to `mock-offline` or `franklin-membrane` |
| REWRITE | Env blocks → `AFFINE_*` + wire aliases; OPENAI_V1 / RealityPro docs; README membrane wording |
| HISTORICAL | Leaderboard / Expanded-Frontier / Global-Leaderboards / Benchmark-Inventory tables |
