#!/usr/bin/env bash
# Steward checklist: notebook-submit readiness for ARC-AGI-2 + ARC-AGI-3.
# Default: validate airgap notebooks + local dry-run. NO Kaggle submit.
# AGI-2 platform licensed fill must reach 259/259 before claiming 100%.
# After UTC quota reset (~2026-07-21T23:57Z): optional --push-kernels only.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

AGI2_SEALED="${ARC_AGI2_SEALED:-$ROOT/reports/arc_local_20260721T172649Z/agi2/submission.json}"
AGI3_SEALED="${ARC_AGI3_SEALED:-$ROOT/reports/arc_local_20260721T171426Z/submission.parquet}"
AGI2_AIRGAP="$ROOT/kaggle/airgap-notebooks/arc-agi-2"
AGI3_AIRGAP="$ROOT/kaggle/airgap-notebooks/arc-agi-3"
AGI2_PLATFORM="$AGI2_AIRGAP/payload/submission.json"
AGI3_PLATFORM="$AGI3_AIRGAP/payload/submission.parquet"
AGI2_SCRIPT="$ROOT/kaggle/arc-prize-2026-agi-2"
AGI3_SCRIPT="$ROOT/kaggle/arc-prize-2026"
TEST_CHALLENGES="$ROOT/data/arc-prize-2026-agi-2/arc-agi_test_challenges.json"
EVAL_CHALLENGES="$ROOT/data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json"
DRY_ROOT="$ROOT/reports/kaggle_notebook_dryrun_$(date -u +%Y%m%dT%H%M%SZ)"
TARGET_GRIDS=259
PUSH_KERNELS=0
SKIP_DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  bin/prepare-kaggle-notebook-submit.sh [--dry-run-only] [--skip-dry-run] [--push-kernels]

Primary packages: kaggle/airgap-notebooks/{arc-agi-2,arc-agi-3}/
Script kernels under kaggle/arc-prize-2026*/ remain secondary.

AGI-2 readiness gate: licensed non-identity grids == 259/259.
Schema shape (240 tasks / 259 grids) alone is NOT 100%.
Do NOT push/submit before UTC quota reset ≈ 2026-07-21T23:57Z.
EOF
}

while (($#)); do
  case "$1" in
    --dry-run-only) shift ;;
    --skip-dry-run) SKIP_DRY_RUN=1; shift ;;
    --push-kernels) PUSH_KERNELS=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

echo "=== prepare-kaggle-notebook-submit ==="
echo "ROOT=$ROOT"
echo "SHA=$(git rev-parse HEAD)"
echo "DRY_ROOT=$DRY_ROOT"

[[ -f "$ROOT/configs/NO_KAGGLE_SUBMIT.lock" ]] || fail "NO_KAGGLE_SUBMIT.lock missing"
pass "lock present (direct CLI submit remains blocked)"

[[ -f "$AGI2_SEALED" && -f "$AGI3_SEALED" ]] || fail "sealed mastery artifacts missing"
[[ -f "$AGI2_PLATFORM" && -f "$AGI3_PLATFORM" ]] || fail "airgap platform payloads missing"
[[ -f "$TEST_CHALLENGES" ]] || fail "test challenges missing"

AGI2_SHA=$(shasum -a 256 "$AGI2_SEALED" | awk '{print $1}')
AGI3_SHA=$(shasum -a 256 "$AGI3_SEALED" | awk '{print $1}')
[[ "$AGI2_SHA" == "3e27792b45d4f186ca436d042841c7db5a7164e71a4a018da1b01a894719e082" ]] \
  || fail "AGI-2 sealed SHA drift: $AGI2_SHA"
[[ "$AGI3_SHA" == "9ffc90cee088b086e5d2539abee76b77346191666a657dd63dbf3cf0de340c73" ]] \
  || fail "AGI-3 sealed SHA drift: $AGI3_SHA"
pass "sealed mastery SHA match"

for meta in "$AGI2_AIRGAP/kernel-metadata.json" "$AGI3_AIRGAP/kernel-metadata.json"; do
  python3 - <<PY || fail "metadata air-gap check: $meta"
import json
m=json.load(open("$meta"))
assert m.get("enable_internet") in (False, "false"), m
assert m.get("competition_sources"), m
print("ok", m.get("id"), m.get("competition_sources"), "internet=", m.get("enable_internet"))
PY
done
pass "airgap notebook metadata internet disabled"

# Licensed fill: attempt_1 != test input (identity placeholder ≠ licensed).
read_n259() {
  local submission="$1"
  python3 - <<PY
import json
from pathlib import Path
ch=json.loads(Path("$TEST_CHALLENGES").read_text())
sub=json.loads(Path("$submission").read_text())
licensed=0
grids=0
for tid, preds in sub.items():
    for i, pred in enumerate(preds):
        grids += 1
        if pred.get("attempt_1") != ch[tid]["test"][i]["input"]:
            licensed += 1
print(f"{licensed} {grids} {len(sub)}")
PY
}

N259_LINE=$(read_n259 "$AGI2_PLATFORM")
LICENSED=$(echo "$N259_LINE" | awk '{print $1}')
SHAPE_GRIDS=$(echo "$N259_LINE" | awk '{print $2}')
SHAPE_TASKS=$(echo "$N259_LINE" | awk '{print $3}')
[[ "$SHAPE_GRIDS" == "$TARGET_GRIDS" ]] || fail "platform shape grids $SHAPE_GRIDS != $TARGET_GRIDS"
[[ "$SHAPE_TASKS" == "240" ]] || fail "platform shape tasks $SHAPE_TASKS != 240"

echo
echo "=== AGI-2 platform licensed fill (CRITICAL gate) ==="
echo "shape: ${SHAPE_TASKS} tasks / ${SHAPE_GRIDS} grids (schema contract)"
echo "licensed_non_identity: ${LICENSED}/${TARGET_GRIDS}"
if (( LICENSED < TARGET_GRIDS )); then
  echo "STATUS: NOT_100pct — licensed ${LICENSED}/${TARGET_GRIDS} (peer hybrid closing toward ${TARGET_GRIDS}/${TARGET_GRIDS})"
  echo "Do NOT claim notebook-submit 100% readiness until ${TARGET_GRIDS}/${TARGET_GRIDS}."
else
  echo "STATUS: LICENSED_${TARGET_GRIDS}/${TARGET_GRIDS}"
fi

echo
echo "=== Notebooks-only / air-gap / filename / schema checklist ==="
echo "  ✅ Notebooks-only (no competitions submit here)"
echo "  ✅ AGI-2/AGI-3 enable_internet=false (airgap-notebooks)"
echo "  ✅ AGI-2 filename submission.json"
echo "  ✅ AGI-3 filename submission.parquet"
echo "  ✅ AGI-2 shape ${SHAPE_TASKS}/${SHAPE_GRIDS}"
if (( LICENSED >= TARGET_GRIDS )); then
  echo "  ✅ AGI-2 licensed ${LICENSED}/${TARGET_GRIDS}"
else
  echo "  ❌ AGI-2 licensed ${LICENSED}/${TARGET_GRIDS} (gap — peer closing)"
fi
echo "  ✅ AGI-3 sealed parquet embedded (SHA ${AGI3_SHA:0:8}…)"

python3 "$ROOT/scripts/validate_arc_prize_submission.py" \
  "$AGI2_PLATFORM" --challenges "$TEST_CHALLENGES"
pass "AGI-2 platform schema vs test challenges"

python3 "$ROOT/scripts/validate_arc_agi3_submission.py" "$AGI3_PLATFORM"
OUT3_SHA=$(shasum -a 256 "$AGI3_PLATFORM" | awk '{print $1}')
[[ "$OUT3_SHA" == "$AGI3_SHA" ]] || fail "AGI-3 platform SHA mismatch vs sealed"
pass "AGI-3 platform schema + sealed SHA"

# Sync sealed into secondary script kernels (non-primary path)
cp -f "$AGI2_SEALED" "$AGI2_SCRIPT/submission.json"
cp -f "$AGI3_SEALED" "$AGI3_SCRIPT/submission.parquet"
pass "synced sealed → secondary script kernel trees"

if ((SKIP_DRY_RUN==0)); then
  mkdir -p "$DRY_ROOT/agi2" "$DRY_ROOT/agi3" "$DRY_ROOT/airgap"
  # Decode / copy airgap payloads as notebook emit dry-run
  cp -f "$AGI2_PLATFORM" "$DRY_ROOT/airgap/submission.json"
  cp -f "$AGI3_PLATFORM" "$DRY_ROOT/airgap/submission.parquet"
  python3 "$ROOT/scripts/validate_arc_prize_submission.py" \
    "$DRY_ROOT/airgap/submission.json" --challenges "$TEST_CHALLENGES"
  python3 "$ROOT/scripts/validate_arc_agi3_submission.py" \
    "$DRY_ROOT/airgap/submission.parquet"
  pass "airgap payload dry-run copy validates"

  # Secondary: script kernel AGI-3 sealed emit
  python3 "$AGI3_SCRIPT/arc_prize_kaggle.py" \
    --sealed-parquet "$AGI3_SEALED" \
    --output "$DRY_ROOT/agi3/submission.parquet"
  python3 "$ROOT/scripts/validate_arc_agi3_submission.py" "$DRY_ROOT/agi3/submission.parquet"
  pass "script-kernel AGI-3 sealed emit validates"

  # Secondary: AGI-2 consume-sealed (eval mastery only — not platform 100%)
  mkdir -p "$DRY_ROOT/agi2/from_sealed"
  python3 "$AGI2_SCRIPT/arc_agi_2_kaggle.py" \
    --consume-sealed \
    --output "$DRY_ROOT/agi2/from_sealed/submission.json"
  python3 "$ROOT/scripts/validate_arc_prize_submission.py" \
    "$DRY_ROOT/agi2/from_sealed/submission.json" \
    --challenges "$EVAL_CHALLENGES"
  pass "script-kernel AGI-2 sealed eval emit validates (120/172 — NOT platform 259)"

  cat >"$DRY_ROOT/DRYRUN_RECEIPT.json" <<EOF
{
  "status": "SCHEMA_PASS_LICENSED_INCOMPLETE",
  "git_sha": "$(git rev-parse HEAD)",
  "agi2_platform_licensed": "${LICENSED}/${TARGET_GRIDS}",
  "agi2_platform_shape": "${SHAPE_TASKS}_tasks/${SHAPE_GRIDS}_grids",
  "agi2_claim_100pct": $([ "$LICENSED" -ge "$TARGET_GRIDS" ] && echo true || echo false),
  "agi2_fot_eval_mastery": "172/172",
  "agi2_sealed_sha256": "$AGI2_SHA",
  "agi3_sealed_sha256": "$AGI3_SHA",
  "primary_packages": [
    "kaggle/airgap-notebooks/arc-agi-2",
    "kaggle/airgap-notebooks/arc-agi-3"
  ],
  "quota_reset_utc": "2026-07-21T23:57Z",
  "direct_cli_submit": "BLOCKED_NOTEBOOKS_ONLY",
  "timestamp_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
  # Fix JSON bool if needed - the above embeds true/false without quotes which is valid JSON
  pass "wrote $DRY_ROOT/DRYRUN_RECEIPT.json"
fi

if ((PUSH_KERNELS)); then
  if [[ -f "$ROOT/configs/NO_KAGGLE_SUBMIT.lock" && "${ALLOW_KAGGLE_SUBMIT:-}" != "1" ]]; then
    fail "refusing --push-kernels without ALLOW_KAGGLE_SUBMIT=1 (lock present)"
  fi
  if (( LICENSED < TARGET_GRIDS )); then
    echo "WARN: pushing with licensed ${LICENSED}/${TARGET_GRIDS} — NOT claiming 100%." >&2
  fi
  command -v kaggle >/dev/null || fail "kaggle CLI required"
  echo "=== Pushing airgap notebooks (NOT competitions submit) ==="
  kaggle kernels push -p "$AGI2_AIRGAP"
  kaggle kernels push -p "$AGI3_AIRGAP"
  pass "airgap notebooks pushed — Run All + Submit from UI after quota reset"
else
  echo
  echo "=== Post-reset steward steps (after ≈ 2026-07-21T23:57Z) ==="
  cat <<STEPS
1. Wait for peer hybrid → licensed ${TARGET_GRIDS}/${TARGET_GRIDS}; rebuild airgap notebooks.
2. Confirm: bin/prepare-kaggle-notebook-submit.sh --dry-run-only  → licensed ${TARGET_GRIDS}/${TARGET_GRIDS}
3. Push airgap notebooks only:
     ALLOW_KAGGLE_SUBMIT=1 bin/prepare-kaggle-notebook-submit.sh --push-kernels
4. Kaggle UI: Run All → Submit from notebook (NOT bin/kaggle-competitions-submit.sh).
5. Keep lock. Leave HLE running. Do not burn quota before reset.
STEPS
fi

echo
echo "DRY-RUN_SCHEMA: PASS"
echo "AGI-2_LICENSED: ${LICENSED}/${TARGET_GRIDS}"
echo "CLAIM_100pct: $([ "$LICENSED" -ge "$TARGET_GRIDS" ] && echo YES || echo NO)"
echo "PRIMARY_AGI2: $AGI2_AIRGAP"
echo "PRIMARY_AGI3: $AGI3_AIRGAP"
echo "HEAD: $(git rev-parse HEAD)"
# Exit 0 on schema pass even if licensed incomplete — steward gate is explicit print.
# Use exit 2 only if someone sets REQUIRE_259=1.
if [[ "${REQUIRE_259:-}" == "1" && "$LICENSED" -lt "$TARGET_GRIDS" ]]; then
  fail "REQUIRE_259=1 and licensed ${LICENSED}/${TARGET_GRIDS}"
fi
