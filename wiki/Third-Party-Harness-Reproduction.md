# Third-Party Harness Reproduction (slim)

Full tutorials live **upstream**. This page is a short pointer only.

| Need | Go here |
|:---|:---|
| Upstream manuals (links) | [Upstream frameworks](Upstream-Frameworks) |
| AGI agent commands | [AGI agent execution](AGI-Agent-Execution) |
| Official leaderboard wrappers | `./bin/run-official-leaderboard-harnesses.sh` |
| Pins / env | [`docs/THIRD_PARTY_HARNESSES.md`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/docs/THIRD_PARTY_HARNESSES.md) |
| Identity once | [Create account](Create-Account-Signup) |

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Point at a JSON OpenAI-compatible /v1 — not HTML SPA.
python -m pip install -e ".[harnesses]"
./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
./bin/run-open-agi-harnesses.sh --harness lm-eval-hard
```

Do not invent scores. Retain upstream artifacts under `reports/third_party/`.
