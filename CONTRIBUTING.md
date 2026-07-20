# Contributing

## Before opening a change

Run the local verification rig:

```bash
python -m pip install -e ".[dev]"
./bin/verify-rig.sh
```

Do not require private credentials or a reachable live endpoint for unit tests
or CI. Live measurement is opt-in and must use configuration outside git.

## Reporting results

Commit code and configuration templates, never API keys or generated reports.
Store new artifacts in `reports/receipts_<UTCSTAMP>/` locally or in the chosen
external artifact store. A public claim must include:

- commit SHA and command;
- model/provider/endpoint identifier (excluding secrets);
- suite, sampling, and harness version;
- raw output or a durable link to it; and
- **MEASURED**, **BASELINE**, or **UNAVAILABLE** provenance.

Do not replace an unavailable run with a pre-filled score, an interceptor
response, or a manually created result file.

## Third-party harnesses

The `harnesses/` directory is intentionally ignored. Clone and install each
upstream project locally, then use `bin/run-official-leaderboard-harnesses.sh`.
Changes to its commands must preserve native upstream output and must not add
synthetic result generation.
