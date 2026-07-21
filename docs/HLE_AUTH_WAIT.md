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
```

## Prove load + official smoke

```bash
harnesses/hle/hle_eval/.venv/bin/python -c "from datasets import load_dataset; ds=load_dataset('cais/hle'); print({k:len(ds[k]) for k in ds})"
HLE_RUN_JUDGE=1 ./bin/run-open-agi-harnesses.sh --harness hle
```

## Re-run wait loop

```bash
./bin/watch-hle-hf-auth.sh
```

`official_hle_accuracy` stays null until CAIS judge output exists.
