# Third-Party Harness Reproduction

Use the packaging launcher. It invokes upstream CLIs only and fails if tools,
checkouts, or a JSON OpenAI-compatible `/models` response are missing.

**Do not** use heredoc receipts. **Do not** treat the local interceptor as a
public third-party score.

Full pins and outsider commands: [`docs/THIRD_PARTY_HARNESSES.md`](../docs/THIRD_PARTY_HARNESSES.md).

## Quick start

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
$EDITOR .env.third-party-harnesses

# Until https://affine.earth/v1 returns OpenAI JSON, point at a real /v1:
# export OPENAI_BASE_URL=http://127.0.0.1:8000/v1   # local wiring only
# or your provider's OpenAI-compatible base URL.

python -m pip install -e ".[harnesses]"   # lm-eval==0.4.7, fschat==0.2.36
./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
./bin/run-official-leaderboard-harnesses.sh --harness fastchat
```

BigCode (`v0.1.0`) needs a local HF checkpoint or existing generations file:

```bash
git clone --branch v0.1.0 --depth 1 \
  https://github.com/bigcode-project/bigcode-evaluation-harness.git \
  harnesses/bigcode-evaluation-harness
python -m pip install -e harnesses/bigcode-evaluation-harness
export BIGCODE_LOCAL_MODEL="your-hf-or-local-checkpoint"
./bin/run-official-leaderboard-harnesses.sh --harness bigcode
```

Artifacts: `reports/third_party/`.

## Related

- [EleutherAI lm-evaluation-harness](EleutherAI-lm-evaluation-harness)
- [BigCode bigcode-evaluation-harness](BigCode-bigcode-evaluation-harness)
- [LMSYS FastChat MT-Bench](LMSYS-FastChat-MT-Bench)
