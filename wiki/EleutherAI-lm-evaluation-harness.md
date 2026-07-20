# EleutherAI `lm-evaluation-harness`

Upstream: <https://github.com/EleutherAI/lm-evaluation-harness>  
**Pin:** `lm-eval==0.4.7` (`configs/third-party-harnesses.yaml`)

```bash
python3 -m venv .venv/lm-eval
. .venv/lm-eval/bin/activate
python -m pip install "lm-eval==0.4.7"

cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Set AFFINE_HARNESS_ENDPOINT / OPENAI_BASE_URL to a JSON OpenAI-compatible /v1
./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
```

Output: `reports/third_party/lm_eval/`. Missing `lm_eval` → exit 127 with pin.
See [docs/THIRD_PARTY_HARNESSES.md](../docs/THIRD_PARTY_HARNESSES.md).
