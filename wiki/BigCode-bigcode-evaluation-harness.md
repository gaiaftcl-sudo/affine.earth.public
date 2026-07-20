# BigCode `bigcode-evaluation-harness`

Upstream: <https://github.com/bigcode-project/bigcode-evaluation-harness>  
**Pin:** git tag `v0.1.0`

```bash
git clone --branch v0.1.0 --depth 1 \
  https://github.com/bigcode-project/bigcode-evaluation-harness.git \
  harnesses/bigcode-evaluation-harness
python -m pip install -e harnesses/bigcode-evaluation-harness

export BIGCODE_LOCAL_MODEL="huggingface-or-local-checkpoint"
./bin/run-official-leaderboard-harnesses.sh --harness bigcode
```

Upstream has no native OpenAI-compatible generation backend. Use
`BIGCODE_GENERATIONS_PATH` only for an existing real generations file.
Output: `reports/third_party/bigcode/results.json`.
See [docs/THIRD_PARTY_HARNESSES.md](../docs/THIRD_PARTY_HARNESSES.md).
