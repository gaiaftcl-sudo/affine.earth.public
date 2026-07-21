# Results & Scores

Scores without proof-in-action do not lead this wiki. Start with [In action](In-Action) (UI all-tests). This page lists **what we ran**, **how we scored**, and **what is still RUNNABLE / BASELINE only**. No invented Pass@k.

---

## A. Front and center — AGI-executable suites

Agents run these via `bin/run-open-agi-harnesses.sh`. Deep harness manuals live **upstream** ([Upstream frameworks](Upstream-Frameworks)). Commands: [AGI agent execution](AGI-Agent-Execution).

| Suite | Harness key | Affine status (this wiki) | What “score” would require |
|:---|:---|:---|:---|
| Humanity's Last Exam | `hle` | **MEASURED STEWARD GATE** — loopback up; Hub user `rpg67` OAuth found; `cais/hle` parquet still 403 until terms accepted | [Live record](Humanitys-Last-Exam-Live): `reports/hle_live_20260721T102858Z/` (+ prior `reports/hle_live_20260721T102039Z/`) |
| ARC Prize 2026 ARC-AGI-3 (Kaggle) | `bin/run-arc-prize-kaggle.sh` | **MEASURED BLOCKER** — CLI auth OK; `userHasEntered=false` | [Live record](ARC-Prize-Kaggle-Live): accept rules at competition URL, then download / submit; no score until platform returns one |
| ARC-AGI / ARC-AGI-2 | `arc-agi` / `arc-agi-2` | **RUNNABLE** — no sample-task substitution | Checkout + task data + official scorer output |
| GPQA Diamond | `gpqa` / `inspect-gpqa` | **RUNNABLE** | lm-eval or Inspect artifact bundle |
| BIG-Bench Hard / MMLU-Pro | `bbh` / `mmlu-pro` / `lm-eval-hard` | **RUNNABLE** | lm-eval JSON under `reports/third_party/open_agi/` |
| GAIA | `gaia` / `inspect` | **RUNNABLE** | Inspect AI tool sandbox + final-answer log |
| LiveCodeBench | `livecodebench` | **RUNNABLE** | `lcb_runner` checkout + native metrics |
| SWE-bench Verified | `swe-bench` | **RUNNABLE** (needs real predictions JSONL) | Official scorer + container logs |
| FrontierMath | `frontiermath` | **NEEDS_UPSTREAM** (exit 3) | Public full suite not available to this launcher |

Capability map (what each suite exercises): [Hardest Tests](Hardest-Tests).

---

## B. MEASURED — local rig + live probe (2026-07-20)

From `reports/real_verification_proof.json` and pytest:

| Check | Result | Provenance |
|:---|:---|:---|
| Pytest | **10 passed** | **MEASURED** |
| Rational float drift | **0.0** (10k adds) | **MEASURED** |
| Live healthz | **HTTP 200** | **MEASURED** |
| Clang `-O0`…`-Os` microbench | `PASS=10000`, `.text` 16,384 B | **MEASURED** |
| Stamp | `REAL_NUMBERS_VERIFIED_NO_FLUB` | **MEASURED** |

LLVM CLI averages (same day) — see [Live Leaderboard](Live-Leaderboard) §1 or regenerate with `llvm run`.

---

## C. UI FoT — Games battery (not Pass@k)

| Evidence | Label |
|:---|:---|
| `affine-earth-demo-ui-all-tests.*` + `ui-tests-*.png` | **UI FoT** — [In action](In-Action) |
| Wallet · QFOT Profile **PROVEN 100/1** in demo | **UI FoT** (economics onboard) — not a coding benchmark |

---

## D. BASELINE tables — demoted

Comparative 100% / frontier tables (e.g. `EXPANDED_FRONTIER_BASELINES`, `reports/affine_earth_vs_frontier_models.*`) are **BASELINE_TABLE_ONLY** unless a matching upstream artifact exists for that cell.

| Location | Label |
|:---|:---|
| [Live Leaderboard](Live-Leaderboard) §2–3 | **BASELINE** — read legend; do not cite Affine 100% cells as MEASURED Pass@k |
| Expanded Coding / Reasoning suite pages | **BASELINE** aggregates |

Audit FAQ: [FAQ — Are all 100% scores from full upstream harness runs?](FAQ#q-are-all-100-scores-from-full-upstream-harness-runs).

---

## E. How we score (short)

1. Prefer **UI FoT** + **MEASURED** receipts over any table.
2. For AGI suites: run the agent launcher → keep upstream JSON/logs → only then upgrade **RUNNABLE** → **MEASURED**.
3. Never copy a Pass@k into this wiki without the command, model id, timestamp, and artifact path.

Methodology: [How we tested](How-We-Tested).
