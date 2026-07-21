# HLE HF auth wait

`cais/hle` Agree/permissions may be granted, but this host still needs a
**process-usable** Hugging Face token.

## Probe (no Keychain; do not echo token)

```bash
printenv HF_TOKEN >/dev/null && echo env=present || echo env=absent
test -s ~/.cache/huggingface/token && echo cache=present || echo cache=absent
hf auth whoami
```

## Steward auth

```bash
hf auth login
# or:
export HF_TOKEN='hf_…'
export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"
```

Never commit the token. Prefer rotating any token pasted into chat after the exam run.

## Prove load + official smoke / full judge

```bash
harnesses/hle/hle_eval/.venv/bin/python -c "from datasets import load_dataset; ds=load_dataset('cais/hle'); print({k:len(ds[k]) for k in ds})"
# expect: {'test': 2500}

# Smoke (predict only):
export HLE_MAX_SAMPLES=3 HLE_RUN_JUDGE=0
./bin/run-open-agi-harnesses.sh --harness hle

# Full judged run (n=2500; omit HLE_MAX_SAMPLES):
unset HLE_MAX_SAMPLES
export HLE_RUN_JUDGE=1
export HLE_JUDGE_MODEL="${OPENAI_MODEL:-qwen/qwen3.6-35b-a3b}"
./bin/run-open-agi-harnesses.sh --harness hle
```

Tracked local overrides for thinking endpoints / incremental save live under
`scripts/hle_eval/` (the `harnesses/*` checkout is gitignored).

## Re-run wait loop (auto-kick on auth)

```bash
nohup env HLE_AUTH_POLL_MAX_SECONDS=0 HLE_AUTH_AUTO_KICK=1 \
  ./bin/watch-hle-hf-auth.sh >>reports/hle_auth_watch.log 2>&1 &
echo $!
tail -f reports/hle_auth_watch.log
```

`official_hle_accuracy` stays null until judged JSON exists and
`scripts/finalize_hle_official_receipt.py` writes the receipt.
