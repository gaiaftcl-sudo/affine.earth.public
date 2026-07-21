# Affine.Earth OS

![Affine.Earth — language games on a sovereign wallet OS](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hero-language-game.png)

**Affine.Earth OS** is a sovereign wallet operating surface with live language games — not a slide deck of benchmark percentages. You open an edge wallet, enter the app, and watch Franklin answer real Games suites in the UI.

**Public repo:** [`gaiaftcl-sudo/affine.earth.public`](https://github.com/gaiaftcl-sudo/affine.earth.public) · **Wiki:** [this site](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki) · **Live:** [`https://affine.earth`](https://affine.earth) · **healthz:** [`/language-invariant/healthz`](https://affine.earth/language-invariant/healthz)

---

## Proof in action — UI all-tests (primary)

Onboard → **all 12 LIVE Games** → Franklin replies in `#messageList` (Socratic clarifying turns). Captured **2026-07-20** against live `https://affine.earth`.

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/ui-tests-07-games-catalog.png">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.webm" type="video/webm">
</video>
</p>

![UI all Games + live answers](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-ui-all-tests.gif)

| | |
|:---|:---|
| **Video** | [mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.mp4) · [webm](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.webm) · [gif](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-ui-all-tests.gif) |
| **Still chapters** | [In action](In-Action) (`ui-tests-*.png`) |
| **FoT** | Live UI answers are membrane turns — **not** CLI Pass@k. Harness scores need receipts under `reports/`. |

---

## The story (read in order)

| Chapter | Page | What you get |
|:---|:---|:---|
| 1. Product | [What is Affine.Earth OS](What-Is-Affine-Earth-OS) | Sovereignty, wallet OS, language games — screenshots of the running app |
| 2. Method | [How we tested](How-We-Tested) | MEASURED vs BASELINE, evidence pipeline, receipt paths |
| 3. Demo | [In action](In-Action) | Full all-tests embed + chapter stills (Games suites live-answered) |
| 4. Scores | [Results & Scores](Results-And-Scores) | What we ran, with provenance — AGI-executable suites front and center |
| 4a. HLE live record | [Humanity’s Last Exam](Humanitys-Last-Exam-Live) | Local drills **3/3** (`reports/hle_local_20260721T104720Z/`, `c3cf4d3`); `official_hle_accuracy=null`; `HF_TOKEN` absent; UI `exam-ui-hle-*` embedded |
| 4b. ARC Prize live | [ARC Prize Kaggle Live](ARC-Prize-Kaggle-Live) | Format validators **GREEN**; probe **0.12** (ref 54875048); submit **LOCKED**; report `reports/arc_local_20260721T105900Z/` (`7ab6e05`) |
| 4c. ARC-AGI-2 Kaggle live | [ARC-AGI-2 live record](ARC-Prize-AGI-2-Kaggle-Live) | Format validators **GREEN**; train **298/1076**; eval **1/172** (hybrid MIT icecuber+DSL; was 0); probe **0.00**; submit **LOCKED**; main `db71c28`; `reports/arc_local_20260721T110813Z/` |
| 4d. Exam game contract | [Language Games — Exam Invariants](Language-Games-Exam-Invariants) | Pre-submission hub: context, answer artifacts, drift checks, and public-submission gate |
| 4d+. UI audit protocol | [ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator) | macOS permission preflight → VideoToolbox capture → Cursor injection → nine-cell reduction → artifact validation; local GREEN before any submit |
| 4e. ARC-AGI-2 game | [Language Games — ARC-AGI-2](Language-Games-ARC-AGI-2) | Demonstrations → two exact-grid attempts |
| 4f. ARC-AGI-3 game | [Language Games — ARC-AGI-3](Language-Games-ARC-AGI-3) | Agent observation → legal action trajectory → parquet |
| 4f+. Top-score formats | [Kaggle ARC top-score formats](Kaggle-ARC-Top-Score-Formats) | Exact JSON/parquet; FoT 0.00≠~65 / 0.12≠~1.86 |
| 4g. HLE game | [Language Games — HLE](Language-Games-HLE) | Context → exact answer → CAIS judge; local fixtures + UI embeds; doctrine `f983986` |
| 5. Agents | [AGI agent execution](AGI-Agent-Execution) | Short commands (`bin/run-open-agi-harnesses.sh`); deep docs link upstream |
| 6. Reproduce | [Create account (once)](Create-Account-Signup) | **Only** page with the signup / login walkthrough video |

→ **Start here to reproduce:** [Create account (once)](Create-Account-Signup)

> **FoT:** AGI-2 MEASURED Kaggle publicScore **0.00** (COMPLETE) — [ARC Prize ARC-AGI-2 live record](ARC-Prize-AGI-2-Kaggle-Live)

---

## What is already MEASURED (local + live probe)

Snapshot **2026-07-20** — regenerate anytime; see [How we tested](How-We-Tested).

| Check | Result | Reproduce |
|:---|:---|:---|
| Pytest | **10 passed** | `python3 -m pytest tests/ -v` |
| Exact rationals | float_drift **0.0** | `python3 scripts/verify_real_numbers_no_flub.py` |
| Live healthz | **HTTP 200** | `curl -sS https://affine.earth/language-invariant/healthz` |
| Clang microbench | `PASS=10000` at `-O0`…`-Os` | same verify script |
| Stamp | `REAL_NUMBERS_VERIFIED_NO_FLUB` | `reports/real_verification_proof.json` |

AGI harnesses (HLE, ARC-AGI, GPQA, GAIA, Inspect, lm-eval hard, …) ship as **RUNNABLE** agent wrappers — not invented Pass@k. Status matrix: [Results & Scores](Results-And-Scores).

---

## Quick clone

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
./bin/verify-rig.sh
```

Agents: [AGI agent execution](AGI-Agent-Execution). Upstream tool manuals: [Upstream frameworks](Upstream-Frameworks) (links only).
