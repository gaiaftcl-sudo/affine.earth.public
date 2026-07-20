# Third-party benchmark and leaderboard submissions

This repository does not ship submission-ready scores. Submit only after a
successful upstream harness run against the exact model endpoint or checkpoint
being claimed, with retained native artifacts.

## Required evidence

1. upstream pin/revision (`lm-eval==0.4.7`, BigCode `v0.1.0`, `fschat==0.2.36`);
2. exact tasks, sample counts, model id;
3. OpenAI-compatible base URL class (no secrets) that returns JSON from `/models`;
4. raw upstream artifact under `reports/third_party/`;
5. host/GPU/dataset notes;
6. exact command line.

`language-invariant/healthz` proves liveness only. An HTML SPA at `/v1` is not
an OpenAI-compatible API. Local interceptor output is wiring evidence only.

## Commands

```bash
cp configs/third-party-harnesses.env.example .env.third-party-harnesses
./bin/run-official-leaderboard-harnesses.sh --harness lm-eval
./bin/run-official-leaderboard-harnesses.sh --harness bigcode
./bin/run-official-leaderboard-harnesses.sh --harness fastchat
```

See [THIRD_PARTY_HARNESSES.md](THIRD_PARTY_HARNESSES.md).
