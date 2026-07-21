# Exam miss → reinject → closure loop

Permanent local loop for **ARC-AGI-2**, **ARC-AGI-3**, and **HLE**. A miss means
the S-state is incomplete — not that compute failed. Franklin repairs **S1–S4**
and locks **C4** within a **29-turn Aristotelian** budget. **No Kaggle submit.**

Canonical doc: [`docs/EXAM_MISS_REINJECTION_LOOP.md`](../docs/EXAM_MISS_REINJECTION_LOOP.md)

Franklin baseline: [UUM-8D game comprehension](../docs/FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md)

Hub: [Language Games — Exam Invariants](Language-Games-Exam-Invariants)

## Run

```bash
./bin/run-exam-reinjection-loop.sh --once
./bin/run-exam-reinjection-loop.sh --daemon --interval-seconds 30
```

Requires `configs/NO_KAGGLE_SUBMIT.lock`.

## Cycle

1. Load local fail receipts (ARC-2 failure cases, ARC-3 trajectory gap, HLE misses)
2. Franklin turn: UUM-8D + [S⁴ projection protocol](Franklin-S4-Projection-Language-Game) `WRAPPER_EVIDENCE` → typed S4 `LOCKED|REINJECT` JSON
3. Local named validator fills `validator_result`; false `LOCKED` demotes to `REINJECT`
4. Record grammar under `reports/exam_reinjection/grammar/`
5. Re-test affected tasks via hybrid solver / HLE mastery / AGI-3 schema gate
6. Log turns in `reports/exam_reinjection/turns.jsonl` toward closure

## Keep running

```bash
nohup ./bin/run-exam-reinjection-loop.sh --daemon --interval-seconds 30 \
  > reports/exam_reinjection/daemon.log 2>&1 &
```

State survives restarts in `reports/exam_reinjection/state.json`.
