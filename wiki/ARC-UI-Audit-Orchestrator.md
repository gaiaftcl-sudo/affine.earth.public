# ARC UI Audit Orchestrator

The ARC UI audit is the local, evidence-producing examination protocol for
ARC-AGI-2 and ARC-AGI-3. It records how the local system reaches each typed
answer artifact. It is not a Kaggle submission mechanism and it does not
create a public score.

The implementation surfaces are `bin/run-arc-ui-audit-orchestrator.sh`, its
orchestrator script, and the local `affine_audit_logs/` evidence scaffold.
Until a recorded dry-run produces assets, this page intentionally contains no
claimed audit video or result. Capture paths below are contracts, not evidence.

## Submission boundary

```text
official inputs
  → local UI audit GREEN
  → validator receipt + submission artifact
  → explicit steward authorization
  → Kaggle submission
  → Kaggle receipt / public score
```

`configs/NO_KAGGLE_SUBMIT.lock` is required to remain present during audit and
ordinary local work. It blocks competition and kernel submission paths unless
the steward deliberately supplies `ALLOW_KAGGLE_SUBMIT=1`. A local audit is
GREEN only when its own evidence and artifact checks pass; it never removes
the lock or authorizes a submission.

## Required macOS permissions

The operator running an interactive capture must confirm these capabilities
before booting the orchestrator:

- **Accessibility:** the terminal or host process used by `osascript` may
  control Cursor. Enable it in System Settings → Privacy & Security →
  Accessibility.
- **Screen Recording:** the terminal/host process and the selected capture
  tool may record the Cursor window. Enable them in System Settings → Privacy
  & Security → Screen Recording & System Audio Recording.
- **Cursor session:** Cursor is open, the intended workspace is active, and
  the command palette/editor focus is observable to the operator.
- **VideoToolbox:** `ffmpeg` is installed with VideoToolbox support; record
  with a hardware encoder only when `ffmpeg -encoders` lists the selected
  `*_videotoolbox` encoder.
- **No bypass:** permission denial, unavailable Cursor focus, missing encoder,
  or missing source assets is an audit failure. It must be recorded as such;
  the run cannot be relabelled GREEN.

The permission check is local-machine evidence. Do not publish permissions or
screenshots as proof of ARC task quality.

## Four-phase flow

### Phase 1 — permission and run binding

1. Confirm the macOS checklist above.
2. Bind the run ID, UTC start time, repository revision, selected ARC track,
   official input revision/checksum, output directory, and operator-visible
   Cursor workspace.
3. Assert `configs/NO_KAGGLE_SUBMIT.lock` exists.
4. Create an audit manifest in the run directory before task execution.
5. Refuse the run if any required identity, permission, lock, or output path
   is absent.

The manifest distinguishes a reproducible local examination from an
unattributed recording.

### Phase 2 — orchestrator boot

`bin/run-arc-ui-audit-orchestrator.sh` is the single coordinator. It starts a
bounded local run and writes its own structured lifecycle record:

```text
preflight
  → initialize ffmpeg VideoToolbox capture
  → open per-task state machine
  → retain events, frame timestamps, and command outcomes
  → close capture
  → validate artifact and receipt
```

The capture must be a recording of the actual local audit window. The
orchestrator must not synthesize frames, reuse an unrelated recording, or
write a video placeholder that is presented as a run. Before a dry-run asset
exists, documentation uses the state diagram only:

```text
[bound] → [capturing] → [task active] → [reduced] → [validated] → [stopped]
                    ↘ failure / incomplete evidence ↗
```

### Phase 3 — per-task state machine

For every official ARC task or ARC-AGI-3 episode, the orchestrator follows
this bounded state machine:

```text
TASK_BOUND
  → CAPTURE_STARTED
  → CURSOR_PROMPT_INJECTED
  → NINE_CELL_REDUCTION
  → RESULT_JSON_EXTRACTED
  → TASK_RECORDED
  → SIGINT_STOPPED
```

1. **`TASK_BOUND`:** retain the task or episode identifier, official input
   revision, and the target artifact location.
2. **`CAPTURE_STARTED`:** start `ffmpeg` with the chosen VideoToolbox
   encoder. Record the complete command, encoder, display/window target, PID,
   and capture path in the event log.
3. **`CURSOR_PROMPT_INJECTED`:** inject the task-bound prompt into the active
   Cursor UI through `osascript`. Record the exact prompt digest, launch/exit
   status, and monotonic timestamps. Injection success does not imply an
   answer is correct.
4. **`NINE_CELL_REDUCTION`:** collect the nine-cell reduction output for the
   bound task only. Preserve cell identities, ordering, individual outcomes,
   reduction rule, and resulting task state. A missing, duplicate, or
   cross-task cell makes the task incomplete.
5. **`RESULT_JSON_EXTRACTED`:** extract structured JSON from the audited
   response, parse it, bind it back to the task identifier, and retain both
   raw and canonical JSON digests. Parsing is not validation.
6. **`TASK_RECORDED`:** append the task event record to the run manifest. It
   states `complete`, `failed`, or `incomplete`; it does not infer a Kaggle
   result.
7. **`SIGINT_STOPPED`:** terminate the capture process with `SIGINT`, wait for
   a bounded graceful exit, and record its status. A recording without a
   recorded clean stop is incomplete evidence.

The next task cannot inherit extracted state, response JSON, cells, or
capture identity from the previous task.

### Phase 4 — artifact and submission validation

After all tasks, validate the task records and the track-native artifact:

| Track | Artifact contract |
| --- | --- |
| ARC-AGI-2 | `submission.json` has every official task/test entry; each has exactly `attempt_1` and `attempt_2`, rectangular integer grids with permitted colors, and task-bound provenance. |
| ARC-AGI-3 | Official framework output is `submission.parquet`, with valid episode provenance, legal trace/terminal state, and the official schema. |

For `submission.json`, validation must reject:

- unknown, missing, or duplicate task IDs;
- test-item count mismatch;
- missing/extra attempt keys;
- non-rectangular, non-integer, or out-of-range grid cells;
- extracted JSON whose bound task ID differs from the emitted artifact; and
- a file whose canonical digest differs from the audited validated artifact.

The final audit receipt is GREEN only if:

1. each task reached `SIGINT_STOPPED` with a complete evidence record;
2. every nine-cell reduction and extracted JSON bound to its task;
3. the native artifact validator is GREEN;
4. the run manifest, capture index, and artifact digests agree; and
5. `NO_KAGGLE_SUBMIT.lock` remained present.

GREEN is a local preflight condition. It does not represent Kaggle acceptance,
a leaderboard value, or hidden-task success.

## Evidence layout

The dry-run implementation owns the exact paths. Its receipt should make
these classes independently inspectable:

```text
reports/arc_ui_audit/<run-id>/
  manifest.json
  events.jsonl
  captures/<task-or-episode>.mp4
  extracted/<task-or-episode>.json
  reductions/<task-or-episode>.json
  artifacts/submission.json | submission.parquet
  validation.json
  receipt.json
```

Raw ffmpeg MP4s are also mirrored under `affine_audit_logs/task_<ID>.mp4`
(gitignored except README/.gitkeep).

No file in this layout is an official score receipt. Only Kaggle can issue
that receipt after an intentionally authorized submission.

## Why the earlier public probes are different

The recorded ARC-AGI-2 0.00 and ARC-AGI-3 0.12 values are earlier Kaggle
process probes: they established that a particular artifact was accepted and
scored. They are neither evidence that a new local audit passed nor evidence
of puzzle mastery. In particular:

- 0.00 is schema-valid artifact delivery with no exact hidden-grid matches in
  that probe.
- 0.12 is a scored starter-process probe, not a claim that the agent's current
  task policy is locally audited or leaderboard-competitive.

The UI audit adds task-bound capture, prompt injection provenance, nine-cell
reduction provenance, extracted JSON validation, and a clean capture stop. It
prevents format-only or partial-process evidence from being mistaken for local
readiness; it does not rewrite the historical public receipts.


## FoT local mastery context

UI audit remains local-only with submit **LOCKED**. Parallel offline hybrid
mastery (MIT arc-icecuber + DSL) on main `db71c28` measured eval **1/172** /
train **298/1076** at `reports/arc_local_20260721T110813Z/` — see
[ARC-AGI-2 live](ARC-Prize-AGI-2-Kaggle-Live). Schema validators **GREEN**;
audit GREEN does not authorize Kaggle submit.

## FoT: `0934a4d8` LOCAL_HYBRID_SOLVER GREEN

Task `0934a4d8` is locally **SOLVED** (train replay **4/4**) by durable rule
engine `llm_llvm_bench/arc/marker8_twin31.py`, hooked as
`LOCAL_HYBRID_SOLVER` in this orchestrator and in
`scripts/arc_local_mastery.py`.

Measured audit run `reports/arc_ui_audit/20260721T111911Z/`:

| Field | Value |
| --- | --- |
| Receipt | **GREEN** |
| Reduction | `LOCAL_HYBRID_SOLVER` / `complete: true` (not `AWAITING_CELL_BRIDGE`) |
| Artifact source | `LOCAL_HYBRID_SOLVER` |
| Train replay | **4/4** |
| Official eval solution match | **true** |
| Submit | **LOCKED** |

Canonical JSON and language-game write-up:
[Language Games — ARC-AGI-2](Language-Games-ARC-AGI-2) §12.

## Related doctrine

- [Language Games — Exam Invariants](Language-Games-Exam-Invariants)
- [Language Games — ARC-AGI-2](Language-Games-ARC-AGI-2)
- [Language Games — ARC-AGI-3](Language-Games-ARC-AGI-3)
- [AGI agent execution](AGI-Agent-Execution)
- [ARC Prize Kaggle Live](ARC-Prize-Kaggle-Live)

Implementation: [`docs/ARC_UI_AUDIT_ORCHESTRATOR.md`](../docs/ARC_UI_AUDIT_ORCHESTRATOR.md).
