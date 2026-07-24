# Affine.Earth OS — Public Evidence Rig

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](pyproject.toml)
[![Wiki](https://img.shields.io/badge/wiki-story%20spine-informational.svg)](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki)

**Affine.Earth OS** is a sovereign wallet operating surface with live language games. This repository is the public **evidence rig**: UI proof, MEASURED local receipts, and agent-executable open AGI harness wrappers — not a sterile command dump, and not invented Pass@k tables.

**Live product:** [https://affine.earth](https://affine.earth) · **Wiki story:** [Home](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/Home)

**Developer suite (MCP · OpenAI `/v1` · OpenUSD · RealityPro):** [`developer-suite/`](developer-suite/) — binary-free Python examples for third parties. See [developer-suite/README.md](developer-suite/README.md) and wiki [Examples-Cookbook](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/Examples-Cookbook).

---

## Proof in action — UI all-tests

Onboard → **all 12 LIVE Games** → Franklin answers in the membrane. Captured 2026-07-20 on live Affine.Earth.

![UI all Games + live answers](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-ui-all-tests.gif)

| | |
|:---|:---|
| **Video** | [mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.mp4) · [webm](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-ui-all-tests.webm) |
| **Chapters** | [In action](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/In-Action) |
| **FoT** | UI membrane turns ≠ CLI harness Pass@k |

Create a wallet once to reproduce: [Create account](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/Create-Account-Signup) (signup video lives **only** on that wiki page).

---

## Story (wiki)

| Chapter | Wiki page |
|:---|:---|
| What is Affine.Earth OS | [What-Is-Affine-Earth-OS](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/What-Is-Affine-Earth-OS) |
| How we tested | [How-We-Tested](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/How-We-Tested) |
| In action | [In-Action](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/In-Action) |
| Results & Scores | [Results-And-Scores](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/Results-And-Scores) |
| AGI agent execution | [AGI-Agent-Execution](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/AGI-Agent-Execution) |

Provenance: **MEASURED** (receipt under `reports/`) · **RUNNABLE** (wrapper exists, no Pass@k archived) · **BASELINE_TABLE_ONLY** (demoted) · **UI FoT** (product demo). Details: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

---

## What this repo runs

- **UI / product FoT** — documented in the wiki (video + stills).
- **Local MEASURED** — pytest, exact rationals, Clang opt levels, live healthz probe (`./bin/verify-rig.sh`).
- **AGI-executable suites** — thin wrappers for HLE, ARC-AGI, GPQA, GAIA, Inspect, lm-eval hard, LiveCodeBench, SWE-bench scorer (`./bin/run-open-agi-harnesses.sh`). Upstream manuals are linked, not re-taught.
- **Classic harnesses** — lm-eval / BigCode / FastChat via `./bin/run-official-leaderboard-harnesses.sh` when `/models` returns JSON.

---

## Install + local green

```bash
git clone https://github.com/gaiaftcl-sudo/affine.earth.public.git
cd affine.earth.public
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
./bin/verify-rig.sh
```

---

## AGI agents — short commands

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Edit endpoint + model to a JSON OpenAI-compatible /v1.

./bin/run-open-agi-harnesses.sh --harness lm-eval-hard
./bin/run-open-agi-harnesses.sh --harness hle
./bin/run-open-agi-harnesses.sh --harness arc-agi-2
./bin/run-open-agi-harnesses.sh --harness gaia
./bin/run-open-agi-harnesses.sh --harness inspect-gpqa
```

Full matrix, status labels, and upstream links: [wiki/AGI-Agent-Execution](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/AGI-Agent-Execution) · [docs/OPEN_AGI_FRAMEWORKS.md](docs/OPEN_AGI_FRAMEWORKS.md).

---

## ARC local ownership — UI audit

ARC production exam work uses a task-by-task Cursor UI audit, with a raw
primary-display MP4 and strict local `attempt_1` / `attempt_2` validation for
each task. It writes only local artifacts and retains
`configs/NO_KAGGLE_SUBMIT.lock`; it has no Kaggle-submit path.

Before running it, grant **Accessibility** and **Screen Recording** to both
Terminal and Cursor in macOS **System Settings → Privacy & Security**, then
restart both applications. Missing permissions make the AppleScript UI turn or
AVFoundation/ffmpeg capture unavailable.

```bash
./bin/run-arc-ui-audit-orchestrator.sh --preflight
./bin/run-arc-ui-audit-orchestrator.sh --task-id 0934a4d8 --wait-seconds 10
```

See [ARC UI Audit Orchestrator](docs/ARC_UI_AUDIT_ORCHESTRATOR.md) and the
[wiki production path](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/ARC-UI-Audit-Orchestrator).

---

## Reports

Generated under `reports/` (gitignored). Never publish a score without the artifact path and provenance label. Comparative 100% baseline tables are **BASELINE_TABLE_ONLY** until matching upstream receipts exist.

## License

[MIT](LICENSE) · see [CONTRIBUTING.md](CONTRIBUTING.md).
