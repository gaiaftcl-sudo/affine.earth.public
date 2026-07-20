# LMSYS FastChat MT-Bench

Upstream: <https://github.com/lm-sys/FastChat>  
**Pin:** `fschat==0.2.36`

```bash
python -m pip install "fschat==0.2.36"
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
# Point AFFINE_HARNESS_ENDPOINT / OPENAI_BASE_URL at JSON OpenAI-compatible /v1
./bin/run-official-leaderboard-harnesses.sh --harness fastchat
```

Answers: `reports/third_party/fastchat/mt-bench-answers.jsonl`.
Judging requires `MTBENCH_RUN_JUDGE=1` plus FastChat judge credentials.
See [docs/THIRD_PARTY_HARNESSES.md](../docs/THIRD_PARTY_HARNESSES.md).
