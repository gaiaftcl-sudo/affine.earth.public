# ARC UI Audit Orchestrator

This is the production ARC exam path: **local task ownership with a raw video
audit for every task**. It is not a Kaggle submission path. The repository
retains `configs/NO_KAGGLE_SUBMIT.lock`, and the orchestrator has no command
that submits to Kaggle.

## Required macOS consent

Grant **Accessibility** and **Screen Recording** to both Terminal and Cursor in
**System Settings → Privacy & Security**, then quit and reopen both apps.
Accessibility permits the documented AppleScript focus/paste/copy UI turn.
Screen Recording permits AVFoundation/ffmpeg to record the primary display.
Without either permission, stop at the loud preflight check:

```bash
./bin/run-arc-ui-audit-orchestrator.sh --preflight
```

## Per-task evidence loop

1. Start async `h264_videotoolbox` display capture at
   `affine_audit_logs/task_<ID>.mp4`.
2. Inject full ARC train/test state into Cursor as language-game context.
3. Call the configured local `/v1/chat/completions` bridge when available; if
   none is configured, record `AWAITING_CELL_BRIDGE` without inventing an
   answer.
4. Make the primary response acquisition through the Cursor UI and clipboard.
   A configured response file is a parallel evidence path when UI selection is
   unreliable.
5. Validate the exact `attempt_1` / `attempt_2` artifact for that task and
   append it to local `submission.json`.
6. Send ffmpeg SIGINT to finalize the MP4.

Each receipt reports its actual bridge status, UI-copy result, artifact source,
and schema verdict. Raw MP4 and JSON artifacts stay local in
`affine_audit_logs/`.

## Language-game binding

The injected context preserves the full task ID, demonstrations, test inputs,
coordinate system, and color symbols. It requires demonstration replay before
a response and permits only the exact task-scoped JSON answer language. This
operationalizes the shared [Exam language-game invariants](Language-Games-Exam-Invariants)
and the [ARC-AGI-2 language game](Language-Games-ARC-AGI-2).

Implementation and commands: [`docs/ARC_UI_AUDIT_ORCHESTRATOR.md`](../docs/ARC_UI_AUDIT_ORCHESTRATOR.md).
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

`configs/NO_KAGGLE_SUBMIT.lock` remains present during audit and ordinary local
work. It blocks competition and kernel submission paths unless the steward
deliberately supplies `ALLOW_KAGGLE_SUBMIT=1`. A local audit never removes the
lock or authorizes a submission.

## Required macOS permissions

- **Accessibility:** enable the terminal or host process used by `osascript` in
  **System Settings → Privacy & Security → Accessibility** so it can control
  Cursor.
- **Screen Recording:** enable the terminal/host process and capture tool in
  **Screen Recording & System Audio Recording** so the Cursor window can be
  recorded.
- **Cursor session:** Cursor is open, the intended workspace is active, and
  editor focus is observable to the operator.
- **VideoToolbox:** `ffmpeg` must list the selected `*_videotoolbox` encoder.
- **No bypass:** denied permissions, absent focus, missing encoder, or missing
  source assets fail the audit; they cannot be labelled GREEN.

## Four-phase flow

### Phase 1 — permission and run binding

1. Confirm the macOS checklist.
2. Bind run ID, UTC start time, repository revision, selected ARC track,
   official input revision/checksum, output directory, and active workspace.
3. Assert `configs/NO_KAGGLE_SUBMIT.lock` exists.
4. Write the run manifest before task execution.
5. Refuse a run without required identity, permission, lock, or path.

### Phase 2 — orchestrator boot

`bin/affine_audit_logs` is the coordinator:

```text
preflight → initialize ffmpeg VideoToolbox capture → per-task state machine
         → retain events / timestamps / command outcomes → close capture
         → validate artifact and receipt
```

The capture is a recording of the actual local audit window. It must not
synthesize frames, reuse an unrelated recording, or present a placeholder as a
run. Until a dry-run asset exists, documentation uses this state diagram:

```text
[bound] → [capturing] → [task active] → [reduced] → [validated] → [stopped]
                    ↘ failure / incomplete evidence ↗
```

### Phase 3 — per-task state machine

```text
TASK_BOUND → CAPTURE_STARTED → CURSOR_PROMPT_INJECTED
          → NINE_CELL_REDUCTION → RESULT_JSON_EXTRACTED
          → TASK_RECORDED → SIGINT_STOPPED
```

1. **`TASK_BOUND`:** retain task/episode ID, official input revision, and
   target artifact location.
2. **`CAPTURE_STARTED`:** start `ffmpeg` with VideoToolbox and record command,
   encoder, target, PID, capture path, and timestamps.
3. **`CURSOR_PROMPT_INJECTED`:** use `osascript` to inject the task-bound
   prompt into active Cursor; retain prompt digest and command outcome.
4. **`NINE_CELL_REDUCTION`:** retain nine cell identities, ordering,
   individual outcomes, reduction rule, and reduced state. Missing, duplicate,
   or cross-task cells make the task incomplete.
5. **`RESULT_JSON_EXTRACTED`:** parse structured response JSON, bind it to
   the task ID, and retain raw/canonical digests. Parsing is not validation.
6. **`TASK_RECORDED`:** append `complete`, `failed`, or `incomplete` evidence
   to the run manifest; do not infer a Kaggle result.
7. **`SIGINT_STOPPED`:** stop capture with `SIGINT`, record bounded graceful
   exit, and mark any missing clean stop as incomplete evidence.

Task state, JSON, cells, and capture identity cannot carry to another task.

### Phase 4 — artifact and submission validation

| Track | Artifact contract |
| --- | --- |
| ARC-AGI-2 | `submission.json` has every official task/test entry, exactly `attempt_1` and `attempt_2`, rectangular permitted integer grids, and task-bound provenance. |
| ARC-AGI-3 | Official `submission.parquet` has episode provenance, legal trace/terminal state, and the native schema. |

For `submission.json`, reject unknown/missing/duplicate IDs, test-item count
mismatch, missing/extra attempt keys, malformed or out-of-range grids,
task/artifact ID mismatch, and a canonical digest mismatch.

GREEN requires complete clean-stop evidence for every task, task-bound
nine-cell reductions and JSON, a GREEN native artifact validator, agreement
between manifest/capture/artifact digests, and continued presence of the lock.
It is a local preflight condition—not Kaggle acceptance, score, or hidden-task
success.

## Evidence layout

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

Only Kaggle can issue an official score receipt after an intentionally
authorized submission.

## Why the earlier public probes differ

The ARC-AGI-2 **0.00** and ARC-AGI-3 **0.12** records are prior Kaggle process
probes: a particular artifact was accepted and scored. They are not proof that
this local audit is GREEN or that puzzle mastery exists. The UI audit adds
task-bound capture, injection provenance, nine-cell reduction, extracted JSON
validation, and clean capture termination; it does not rewrite historical
public receipts.

## Related doctrine

- [Language Games — Exam Invariants](Language-Games-Exam-Invariants)
- [Language Games — ARC-AGI-2](Language-Games-ARC-AGI-2)
- [Language Games — ARC-AGI-3](Language-Games-ARC-AGI-3)
- [AGI agent execution](AGI-Agent-Execution)
