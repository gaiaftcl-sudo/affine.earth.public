# Local ARC UI audit evidence scaffold

`bin/run-arc-ui-audit-orchestrator.sh` mirrors raw per-task captures here:

- `task_<ID>.mp4` — raw primary-display capture for one ARC task
- `audit-receipts.json` — mirror of the latest run receipt
- `submission.json` — mirror of the local attempt artifact

Doctrine evidence (manifest, events, reductions, validation) lives under
`reports/arc_ui_audit/<run-id>/`. See `docs/ARC_UI_AUDIT_ORCHESTRATOR.md`.

MP4s and generated JSON are gitignored. Grant **Accessibility** and
**Screen Recording** to Terminal and Cursor before capture.
