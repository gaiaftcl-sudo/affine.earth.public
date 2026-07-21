# How we tested

Evidence before narrative. Every published number on this wiki carries a provenance label. Tables without receipts are demoted or marked **BASELINE**.

![MEASURED vs BASELINE](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/banner-measured-vs-baseline.png)

---

## Provenance labels

| Label | Meaning |
|:---|:---|
| **MEASURED** | Dated run with command, host/tool identity, and raw artifact under `reports/` (or wiki assets for UI FoT). |
| **RUNNABLE** | Wrapper / command path exists (`bin/run-open-agi-harnesses.sh`, etc.); no Affine Pass@k archived yet. |
| **BASELINE_TABLE_ONLY** | Comparative or model-card aggregate — **not** a run this project archived. |
| **UI FoT** | Live product demo (video / stills). Not a CLI harness score. |
| **NEEDS_UPSTREAM** | Launcher exits non-zero until an external suite is available (e.g. FrontierMath). |

Do not promote a **BASELINE** cell as if it were **MEASURED**. Do not invent Pass@k.

---

## Evidence pipeline

```text
1. Identity (optional for local Clang/pytest)
   → Create account once in the UI
2. Local green
   → ./bin/verify-rig.sh
   → reports/real_verification_proof.json
3. UI FoT
   → Games battery on https://affine.earth
   → wiki assets: affine-earth-demo-ui-all-tests.* + ui-tests-*.png
4. Open AGI / upstream harnesses (agents)
   → ./bin/run-open-agi-harnesses.sh --harness <id>
   → retain reports/third_party/open_agi/<suite>/
5. Publish only with labels above
```

![Evidence pipeline](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/banner-evidence-pipeline.png)

---

## Receipt paths (this repo)

| Artifact | Provenance | Notes |
|:---|:---|:---|
| `reports/real_verification_proof.json` | **MEASURED** | Rationals + Clang + healthz stamp |
| `reports/llvm_benchmark*.json` | **MEASURED** | Local `llvm run` |
| `reports/receipts_*` | **MEASURED** | Bundle timestamps |
| `reports/third_party/open_agi/` | **RUNNABLE** until filled | Upstream harness native output |
| `reports/affine_earth_vs_frontier_models.*` | Check producer | Domain runner / baseline mix — read footer before citing |
| Wiki `assets/affine-earth-demo-ui-all-tests.*` | **UI FoT** | All Games + live answers |
| Wiki `assets/affine-earth-demo-signup-app-qa.*` | Signup FoT | **Only** on [Create account](Create-Account-Signup) |

Longer audit notes: [Un-Mocked Verification Methodology](Un-Mocked-Verification-Methodology-and-Instructions) · [Reports & Artifacts](Reports-And-Artifacts) · repo [`docs/METHODOLOGY.md`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/docs/METHODOLOGY.md).

---

## Refresh MEASURED local snapshot

```bash
cd affine.earth.public   # or llm-llvm-benchmark-suite/
python3 -m pytest tests/ -v
python3 scripts/verify_real_numbers_no_flub.py
python3 -m llm_llvm_bench.cli.main llvm run \
  --opt-levels -O0,-O2,-O3,-Os --compiler clang \
  --out reports/llvm_benchmark_live.json
```

Next: [In action](In-Action) · [Results & Scores](Results-And-Scores).
