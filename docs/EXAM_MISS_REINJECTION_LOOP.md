# Exam miss → reinject → closure loop

Permanent local language-game loop for **ARC-AGI-2**, **ARC-AGI-3**, and
**Humanity's Last Exam**. Never idle. Never Kaggle-submit.

Franklin absolute baseline:
[FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md](FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md).

Exam contracts:
[LANGUAGE_GAMES_EXAM_INVARIANTS.md](LANGUAGE_GAMES_EXAM_INVARIANTS.md).

## Why this exists

A miss is not a compute failure. It is an **incomplete S-state**:

| Axis | Meaning |
| --- | --- |
| S1 | Objects / symbols in the question state |
| S2 | Relations among those objects |
| S3 | Legal transforms / actions under the exam grammar |
| S4 | Acceptance boundary (what counts as solved) |
| C4 | Single locked terminal projection — the only true answer |

Franklin + the local wrapper play a two-way language game until C1–C4 collapse
to one C4, within an **Aristotelian closure budget of 29 turns** per task.

**Jordan loop bound (hard):** `LOCKED` is permitted only when the named
validator yields zero remainder against C4 (demonstration replay / environment
step / exact token). Candidate presence alone is shear — demoted to `REINJECT`.
Implemented in `jordan_loop_bound_closed` + `apply_local_s4_validator`.

**Learned experience pull (hard):** every Franklin play loads prior CLOSED /
LOCKED seals from `reports/exam_reinjection/grammar/<track>/` and
`state.json` via `load_learned_experiences` before proposing. Incomplete
projection is not done — reuse sealed grammar/engines first.

## Loop steps (every cycle)

1. **Sync local hybrid GREEN, then load open fail receipts**
   - Close owned exact-match engines (`LOCAL_SOLVER_GREEN` / `S4_LOCKED`) so the daemon never REINJECTs solved tasks
   - ARC-AGI-2: latest `failure-case-analyses.json` (skip GREEN) + S1/S3 `arc_agi2_*_miss_queue.jsonl` open tails
   - ARC-AGI-3: `agi3/summary.json` trajectory gap + episode traces
   - HLE: latest `reports/hle_local_*/receipt.json` mismatches (and official-gate open marker)
2. **Pull learned CLOSED experiences** for the track (`load_learned_experiences`)
3. **Open a Franklin turn** with UUM-8D baseline (Jordan Bond kept) +
   [S⁴ projection protocol](FRANKLIN_S4_PROJECTION_LANGUAGE_GAME.md)
   `WRAPPER_EVIDENCE` (`s_state=incomplete` + `learned_experiences`)
4. **Parse typed S4** with `status ∈ {LOCKED, REINJECT}`, named `validator`, and
   `unresolved_alternatives` (shared module
   `llm_llvm_bench.arc.franklin_s4_projection`; client
   `llm_llvm_bench.exam.s4_client`)
5. **Run the named local validator + Jordan loop bound**; demote false `LOCKED` → `REINJECT`
6. **Apply / record** grammar update under `reports/exam_reinjection/grammar/`
7. **Re-run local mastery** for affected tasks (`--mastery affected|full|none`)
8. **Log turn count** toward 29-turn Aristotelian closure in `turns.jsonl`

Hard gate: `configs/NO_KAGGLE_SUBMIT.lock` must be present. This loop has **no**
submit path.

## Commands

```bash
# One cycle (default)
./bin/run-exam-reinjection-loop.sh --once

# Continuous daemon (never idle)
./bin/run-exam-reinjection-loop.sh --daemon --interval-seconds 30

# Dry-run (no Franklin HTTP; still loads misses + writes placeholders)
./bin/run-exam-reinjection-loop.sh --once --dry-run --mastery none

# Track filter
./bin/run-exam-reinjection-loop.sh --once --tracks arc2,hle --per-track-limit 8
```

Python entrypoint: `scripts/exam_miss_reinjection_loop.py`  
Library: `llm_llvm_bench/exam/miss_reinjection.py`

## State & receipts

| Path | Role |
| --- | --- |
| `reports/exam_reinjection/state.json` | Per-task turn counts / CLOSED / DEAD_END |
| `reports/exam_reinjection/turns.jsonl` | OPEN → PROPOSE → GATE → MASTERY turns |
| `reports/exam_reinjection/grammar/<track>/<task_id>.json` | Latest S1–S4 + C4 |
| `reports/exam_reinjection/grammar_updates.jsonl` | Append-only grammar index |
| `reports/exam_reinjection/miss_queue.jsonl` | Misses seen by the loop |
| `reports/exam_reinjection/latest_cycle.json` | Last cycle summary |

Wiring:

- ARC-AGI-2 retest → `llm_llvm_bench.arc.local_hybrid_solver.solve_task`
- ARC-AGI-3 → `scripts/validate_arc_agi3_submission.py` (schema; trajectory remains grammar work)
- HLE → `bin/run-local-hle-mastery.sh`
- Full mastery → `bin/run-arc-local-mastery.sh` + HLE script when `--mastery full`

## Keep it running (daemon)

```bash
# Foreground
./bin/run-exam-reinjection-loop.sh --daemon --interval-seconds 30

# Background with log
nohup ./bin/run-exam-reinjection-loop.sh --daemon --interval-seconds 30 \
  > reports/exam_reinjection/daemon.log 2>&1 &

# launchd-friendly: same binary; restart on exit
# ProgramArguments: .../bin/run-exam-reinjection-loop.sh --daemon --interval-seconds 30
```

Endpoint env (same family as HLE local mastery):

- `EXAM_REINJECT_BASE_URL` / `OPENAI_BASE_URL` / `HLE_LOCAL_BASE_URL` (default `http://127.0.0.1:8080/v1`)
- `EXAM_REINJECT_FALLBACK_BASE_URL` (default `http://127.0.0.1:1234/v1` — used on primary read-timeout)
- `EXAM_REINJECT_MODEL` / `OPENAI_MODEL`
- `EXAM_REINJECT_TIMEOUT` (default 300s) / `EXAM_REINJECT_MAX_TOKENS` (default 1024)
- `EXAM_REINJECT_LIVE=1` — forbids `--dry-run` while a live daemon holds `daemon.lock`
- `OPENAI_API_KEY`

Template: `reports/exam_reinjection/env.local.example`

## Closure semantics

| Status | Meaning |
| --- | --- |
| HEALING | Miss reinjected; grammar recorded; mastery still open |
| CLOSED | Local mastery exact-match for that task (HLE fixture / ARC-2 label) |
| DEAD_END | ≥29 turns without C4 lock — rotate research_note / next miss class |

Public scores still require official Kaggle / CAIS receipts. This loop only
closes **local** language-game confidence.
