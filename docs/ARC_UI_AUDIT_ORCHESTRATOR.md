# ARC UI Audit Orchestrator

Local, evidence-producing examination protocol for ARC-AGI-2 (pattern for other
exams). Matches wiki doctrine
[ARC-UI-Audit-Orchestrator](https://github.com/gaiaftcl-sudo/affine.earth.public/wiki/ARC-UI-Audit-Orchestrator)
(SHA `185f63f`).

It never submits to Kaggle. `configs/NO_KAGGLE_SUBMIT.lock` is required.

## Entry point

```bash
./bin/run-arc-ui-audit-orchestrator.sh --preflight
./bin/run-arc-ui-audit-orchestrator.sh --task-id 0934a4d8 --wait-seconds 10
```

## macOS permissions (steward checklist)

Without these, AppleScript + AVFoundation/ffmpeg fail silently:

1. **Accessibility** — Terminal (or host) + Cursor
2. **Screen Recording** — Terminal (or host) + Cursor
3. Quit and reopen both apps after granting
4. Cursor open with intended workspace/chat focused
5. `ffmpeg -encoders` lists `h264_videotoolbox`
6. `configs/NO_KAGGLE_SUBMIT.lock` present

`--preflight` fails loud with this checklist when any gate is missing.

## Four-phase flow

1. **Permission + run binding** — preflight, lock assert, run ID, revision,
   challenges checksum, `manifest.json` before any task.
2. **Orchestrator boot** — VideoToolbox capture init, event log, no synthetic
   frames.
3. **Per-task state machine**

   ```text
   TASK_BOUND → CAPTURE_STARTED → CURSOR_PROMPT_INJECTED
             → NINE_CELL_REDUCTION → RESULT_JSON_EXTRACTED
             → TASK_RECORDED → SIGINT_STOPPED
   ```

4. **Artifact validation** — `scripts/validate_arc_prize_submission.py` on
   selected tasks; full-set validation when all challenge IDs are present.

## Nine-cell reduction

Calls a configured real HTTP bridge (`--bridge-url`, `ARC_AUDIT_BRIDGE_URL`, or
`OPENAI_BASE_URL`). If none is configured, writes
`reductions/<task_id>.json` with `AWAITING_CELL_BRIDGE` for each of the nine
cell IDs. No fabricated cell physics.

## Evidence layout

Doctrine run directory:

```text
reports/arc_ui_audit/<run-id>/
  manifest.json
  events.jsonl
  captures/<task-id>.mp4
  extracted/<task-id>.json
  reductions/<task-id>.json
  artifacts/submission.json
  validation.json
  receipt.json
```

Raw scaffold (gitignored MP4/JSON except README/.gitkeep):

```text
affine_audit_logs/task_<ID>.mp4
affine_audit_logs/submission.json
affine_audit_logs/audit-receipts.json
```

## Single-task exam (sibling coordination)

```bash
./bin/run-arc-ui-audit-orchestrator.sh \
  --task-id 0934a4d8 \
  --wait-seconds 10 \
  --response-file-template "/absolute/path/arc-{task_id}.json"
```

Primary answer path is Cursor UI clipboard. Response file is a parallel FoT
path when UI selection is fragile. GREEN is local preflight only — never a
Kaggle score.
