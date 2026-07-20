#!/usr/bin/env bash
# Thin launcher for hardest / open-AGI upstream CLIs.
# Never invents scores. Never writes heredoc result JSON.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEFAULT_ENV_FILE="${ROOT_DIR}/.env.third-party-harnesses"
OPEN_AGI_YAML="${ROOT_DIR}/configs/open-agi-harnesses.yaml"
HARNESS_YAML="${ROOT_DIR}/configs/third-party-harnesses.yaml"

usage() {
    cat <<'USAGE'
Usage: bin/run-open-agi-harnesses.sh [--harness NAME]...

NAMES (real upstream CLI or loud fail):
  hle | arc-agi | arc-agi-2
  gpqa | bbh | mmlu-pro | lm-eval-hard
  gaia | inspect-gpqa | inspect
  livecodebench | swe-bench
  frontiermath   (always exit 3 — no public full suite)

Runs upstream CLIs only. Exits non-zero if the selected upstream tool,
checkout, dataset access, endpoint, predictions file, or credential is
missing. NEVER invents scores or writes heredoc result JSON.

Configuration:
  configs/open-agi-harnesses.yaml
  configs/third-party-harnesses.env.example
  docs/OPEN_AGI_FRAMEWORKS.md

Endpoint aliases (first non-empty wins):
  AFFINE_HARNESS_ENDPOINT | AFFINE_OPENAI_BASE_URL | OPENAI_BASE_URL | AFFINE_BASE_URL

Note: https://affine.earth/v1 currently serves an HTML SPA, not OpenAI JSON.
USAGE
}

load_env_file() {
    local env_file="${AFFINE_HARNESS_ENV_FILE:-}"
    if [[ -z "$env_file" && -f "$DEFAULT_ENV_FILE" ]]; then
        env_file="$DEFAULT_ENV_FILE"
    fi
    if [[ -n "$env_file" ]]; then
        [[ -f "$env_file" ]] || {
            echo "Configured env file does not exist: $env_file" >&2
            exit 2
        }
        # shellcheck disable=SC1090
        set -a
        source "$env_file"
        set +a
    fi
}

require_command() {
    local cmd="$1"
    local install_hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "FATAL: required command not found: $cmd" >&2
        echo "Install: $install_hint" >&2
        echo "See: docs/OPEN_AGI_FRAMEWORKS.md" >&2
        exit 127
    fi
}

require_directory() {
    local dir="$1"
    local hint="$2"
    [[ -d "$dir" ]] || {
        echo "FATAL: required upstream checkout missing: $dir" >&2
        echo "Install: $hint" >&2
        echo "See: docs/OPEN_AGI_FRAMEWORKS.md" >&2
        exit 2
    }
}

require_file() {
    local path="$1"
    local hint="$2"
    [[ -f "$path" ]] || {
        echo "FATAL: required file missing: $path" >&2
        echo "Install: $hint" >&2
        exit 2
    }
}

fail_needs_upstream() {
    local name="$1"
    local upstream="$2"
    local detail="${3:-}"
    echo "FATAL: harness '${name}' status=NEEDS_UPSTREAM" >&2
    echo "Upstream: ${upstream}" >&2
    if [[ -n "$detail" ]]; then
        echo "$detail" >&2
    fi
    echo "This launcher refuses to invent scores or write heredoc receipts." >&2
    echo "See: configs/open-agi-harnesses.yaml and docs/OPEN_AGI_FRAMEWORKS.md" >&2
    exit 3
}

resolve_base_url() {
    local candidate
    for candidate in \
        "${AFFINE_HARNESS_ENDPOINT:-}" \
        "${AFFINE_OPENAI_BASE_URL:-}" \
        "${OPENAI_BASE_URL:-}" \
        "${AFFINE_BASE_URL:-}"
    do
        if [[ -n "$candidate" ]]; then
            printf '%s' "${candidate%/}"
            return 0
        fi
    done
    return 1
}

resolve_model() {
    local candidate
    for candidate in \
        "${AFFINE_HARNESS_MODEL:-}" \
        "${AFFINE_MODEL:-}" \
        "${OPENAI_MODEL:-}"
    do
        if [[ -n "$candidate" ]]; then
            printf '%s' "$candidate"
            return 0
        fi
    done
    return 1
}

preflight_openai_json() {
    local base_url="$1"
    local api_key="$2"
    local tmp
    tmp="$(mktemp)"
    local http_code
    http_code="$(
        curl --silent --show-error --connect-timeout 10 \
            -H "Authorization: Bearer ${api_key}" \
            -H "Accept: application/json" \
            -o "$tmp" \
            -w '%{http_code}' \
            "${base_url}/models" || true
    )"
    if [[ "$http_code" != "200" ]]; then
        echo "FATAL: GET ${base_url}/models returned HTTP ${http_code:-curl-failed}" >&2
        echo "Body (first 400 bytes):" >&2
        head -c 400 "$tmp" >&2 || true
        echo >&2
        echo "https://affine.earth/v1 currently returns an HTML SPA, not OpenAI JSON." >&2
        echo "Set AFFINE_HARNESS_ENDPOINT / OPENAI_BASE_URL to a real OpenAI-compatible /v1." >&2
        rm -f "$tmp"
        exit 2
    fi
    if ! python3 -c 'import json,sys; json.load(open(sys.argv[1]));' "$tmp" 2>/dev/null; then
        echo "FATAL: GET ${base_url}/models returned HTTP 200 but body is not JSON." >&2
        echo "Body (first 400 bytes):" >&2
        head -c 400 "$tmp" >&2 || true
        echo >&2
        rm -f "$tmp"
        exit 2
    fi
    rm -f "$tmp"
}

require_endpoint_and_model() {
    BASE_URL="$(resolve_base_url)" || {
        echo "FATAL: set AFFINE_HARNESS_ENDPOINT, AFFINE_OPENAI_BASE_URL, OPENAI_BASE_URL, or AFFINE_BASE_URL" >&2
        echo "Copy: cp configs/third-party-harnesses.env.example .env.third-party-harnesses" >&2
        exit 2
    }
    MODEL="$(resolve_model)" || {
        echo "FATAL: set AFFINE_HARNESS_MODEL, AFFINE_MODEL, or OPENAI_MODEL" >&2
        exit 2
    }
    OPENAI_API_KEY="${OPENAI_API_KEY:-${AFFINE_HARNESS_API_KEY:-}}"
    : "${OPENAI_API_KEY:?FATAL: set OPENAI_API_KEY or AFFINE_HARNESS_API_KEY}"
    export OPENAI_API_KEY
    export OPENAI_BASE_URL="$BASE_URL"
    export AFFINE_BASE_URL="$BASE_URL"
}

run_lm_eval_tasks() {
    local label="$1"
    local tasks="$2"
    local out_path="$3"
    require_command lm_eval \
        'python -m pip install "lm-eval==0.4.7"  # pin from configs/open-agi-harnesses.yaml'
    require_endpoint_and_model
    preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    mkdir -p "$out_path"
    echo "Running lm-eval hard tasks (${label}): ${tasks}"
    lm_eval \
        --model local-chat-completions \
        --model_args "model=${MODEL},base_url=${BASE_URL}/chat/completions,num_concurrent=${LM_EVAL_CONCURRENCY:-1},max_retries=${LM_EVAL_MAX_RETRIES:-3},tokenized_requests=False" \
        --tasks "$tasks" \
        --num_fewshot "${LM_EVAL_NUM_FEWSHOT:-0}" \
        --batch_size "${LM_EVAL_BATCH_SIZE:-1}" \
        --log_samples \
        --output_path "$out_path"
}

run_gpqa() {
    run_lm_eval_tasks "gpqa" \
        "${GPQA_TASKS:-gpqa_diamond_cot_zeroshot}" \
        "${GPQA_OUTPUT_PATH:-reports/third_party/open_agi/gpqa}"
}

run_bbh() {
    run_lm_eval_tasks "bbh" \
        "${BBH_TASKS:-bbh_cot_fewshot}" \
        "${BBH_OUTPUT_PATH:-reports/third_party/open_agi/bbh}"
}

run_mmlu_pro() {
    run_lm_eval_tasks "mmlu-pro" \
        "${MMLU_PRO_TASKS:-mmlu_pro}" \
        "${MMLU_PRO_OUTPUT_PATH:-reports/third_party/open_agi/mmlu_pro}"
}

run_lm_eval_hard() {
    run_lm_eval_tasks "lm-eval-hard" \
        "${LM_EVAL_HARD_TASKS:-gpqa_diamond_cot_zeroshot,bbh_cot_fewshot,mmlu_pro}" \
        "${LM_EVAL_HARD_OUTPUT_PATH:-reports/third_party/open_agi/lm_eval_hard}"
}

run_hle() {
    local dir="${HLE_HARNESS_DIR:-harnesses/hle}"
    require_directory "$dir" \
        'git clone --depth 1 https://github.com/centerforaisafety/hle.git harnesses/hle && python -m pip install -r harnesses/hle/requirements.txt'
    require_file "$dir/hle_eval/run_model_predictions.py" \
        'Ensure checkout is centerforaisafety/hle with hle_eval/ scripts'
    require_endpoint_and_model
    preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    if [[ -z "${HF_TOKEN:-${HUGGING_FACE_HUB_TOKEN:-}}" ]]; then
        echo "FATAL: HLE dataset cais/hle typically requires Hugging Face auth." >&2
        echo "Accept terms at https://huggingface.co/datasets/cais/hle then set HF_TOKEN." >&2
        echo "Do not redistribute prompts/images/answers per dataset notice." >&2
        exit 2
    fi
    export HF_TOKEN="${HF_TOKEN:-${HUGGING_FACE_HUB_TOKEN}}"
    mkdir -p "${HLE_OUTPUT_DIR:-reports/third_party/open_agi/hle}"
    local out_dir="${HLE_OUTPUT_DIR:-reports/third_party/open_agi/hle}"
    local max_tokens="${HLE_MAX_COMPLETION_TOKENS:-8192}"
    local workers="${HLE_NUM_WORKERS:-4}"
    local dataset="${HLE_DATASET:-cais/hle}"
    local pred_args=(
        --dataset "$dataset"
        --model "$MODEL"
        --max_completion_tokens "$max_tokens"
        --num_workers "$workers"
    )
    if [[ -n "${HLE_MAX_SAMPLES:-}" ]]; then
        pred_args+=(--max_samples "$HLE_MAX_SAMPLES")
    fi
    (
        cd "$dir/hle_eval"
        python3 run_model_predictions.py "${pred_args[@]}"
        if [[ "${HLE_RUN_JUDGE:-0}" == "1" ]]; then
            python3 run_judge_results.py \
                --dataset "$dataset" \
                --predictions "hle_${MODEL}.json" \
                --num_workers "$workers"
        else
            echo "HLE predictions finished under $dir/hle_eval/."
            echo "Judging not run (set HLE_RUN_JUDGE=1 to invoke run_judge_results.py)."
        fi
    )
    echo "Retain upstream HLE JSON under ${out_dir}/ for provenance. No score invented here."
}

run_arc_agi_common() {
    local label="$1"
    local data_dir="$2"
    local save_dir="$3"
    local dir="${ARC_AGI_HARNESS_DIR:-harnesses/arc-agi-benchmarking}"
    require_directory "$dir" \
        'git clone --depth 1 https://github.com/arcprize/arc-agi-benchmarking.git harnesses/arc-agi-benchmarking && (cd harnesses/arc-agi-benchmarking && uv sync)'
    : "${ARC_AGI_CONFIG:?FATAL: set ARC_AGI_CONFIG to a models.yml config name from the ARC Prize checkout (not a fake score).}"
    [[ -d "$data_dir" ]] || {
        echo "FATAL: ARC task data directory missing: $data_dir" >&2
        exit 2
    }
    require_endpoint_and_model
    if [[ "${ARC_AGI_PREFLIGHT_OPENAI:-1}" == "1" ]]; then
        preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    fi
    mkdir -p "$save_dir"
    echo "Running ARC Prize benchmarking (${label}) data_dir=${data_dir}"
    if command -v uv >/dev/null 2>&1; then
        (
            cd "$dir"
            uv run cli/run_all.py \
                --config "$ARC_AGI_CONFIG" \
                --data_dir "$data_dir" \
                --save_submission_dir "$save_dir" \
                --log-level "${ARC_AGI_LOG_LEVEL:-INFO}"
        )
    else
        require_file "$dir/cli/run_all.py" "Install uv (https://docs.astral.sh/uv/) or ensure checkout is complete"
        (
            cd "$dir"
            python3 cli/run_all.py \
                --config "$ARC_AGI_CONFIG" \
                --data_dir "$data_dir" \
                --save_submission_dir "$save_dir" \
                --log-level "${ARC_AGI_LOG_LEVEL:-INFO}"
        )
    fi
    echo "ARC submissions under ${save_dir}. Score with upstream scoring.py. No score invented here."
}

run_arc_agi() {
    local data_dir="${ARC_AGI_DATA_DIR:-}"
    local dir="${ARC_AGI_HARNESS_DIR:-harnesses/arc-agi-benchmarking}"
    if [[ -z "$data_dir" ]]; then
        if [[ -d "$dir/data/sample/tasks" ]]; then
            data_dir="$dir/data/sample/tasks"
            echo "WARN: ARC_AGI_DATA_DIR unset; using bundled sample tasks only (not full ARC-AGI / ARC-AGI-2)." >&2
        else
            echo "FATAL: set ARC_AGI_DATA_DIR to a folder of ARC task .json files." >&2
            echo "ARC-AGI-1: git clone https://github.com/fchollet/ARC-AGI.git harnesses/ARC-AGI" >&2
            echo "ARC-AGI-2: use --harness arc-agi-2 after cloning ARC-AGI-2" >&2
            exit 2
        fi
    fi
    run_arc_agi_common "arc-agi" "$data_dir" \
        "${ARC_AGI_SUBMISSION_DIR:-reports/third_party/open_agi/arc_agi/submissions}"
}

run_arc_agi_2() {
    local data_root="${ARC_AGI_2_DIR:-harnesses/ARC-AGI-2}"
    require_directory "$data_root" \
        'git clone --depth 1 https://github.com/arcprize/ARC-AGI-2.git harnesses/ARC-AGI-2'
    local data_dir="${ARC_AGI_DATA_DIR:-${data_root}/data/evaluation}"
    [[ -d "$data_dir" ]] || {
        echo "FATAL: ARC-AGI-2 evaluation tasks missing at: $data_dir" >&2
        echo "Expected public evaluation JSON under harnesses/ARC-AGI-2/data/evaluation/" >&2
        exit 2
    }
    # Refuse silent sample-task substitution for the ARC-AGI-2 harness key.
    if [[ "$data_dir" == *"/data/sample/"* ]]; then
        echo "FATAL: arc-agi-2 refuses sample tasks; point at ARC-AGI-2 data/evaluation." >&2
        exit 2
    fi
    run_arc_agi_common "arc-agi-2" "$data_dir" \
        "${ARC_AGI_2_SUBMISSION_DIR:-reports/third_party/open_agi/arc_agi_2/submissions}"
}

run_inspect_eval() {
    local label="$1"
    local task="$2"
    local log_dir="$3"
    local require_docker="${4:-0}"
    require_command inspect \
        'python -m pip install "inspect-ai" "inspect-evals"  # UK AISI Inspect + Inspect Evals'
    require_endpoint_and_model
    preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    if ! python3 -c 'import inspect_evals' 2>/dev/null; then
        echo "FATAL: Python package inspect_evals is not importable." >&2
        echo 'Install: python -m pip install "inspect-evals"' >&2
        echo "Or clone: https://github.com/UKGovernmentBEIS/inspect_evals" >&2
        exit 127
    fi
    mkdir -p "$log_dir"
    local inspect_model="${INSPECT_MODEL:-${GAIA_INSPECT_MODEL:-openai-api/${MODEL}}}"
    # Prefer openai-api/ per Inspect docs; allow openai/ override via INSPECT_MODEL.
    if [[ "$require_docker" == "1" ]] && [[ "${INSPECT_REQUIRE_DOCKER:-1}" == "1" ]] \
        && ! command -v docker >/dev/null 2>&1; then
        echo "FATAL: Inspect task '${task}' typically needs Docker Engine for tool sandboxes." >&2
        echo "Install Docker, or set INSPECT_REQUIRE_DOCKER=0 only if you know sandboxes are unused." >&2
        exit 2
    fi
    echo "Running Inspect eval (${label}): ${task} model=${inspect_model}"
    local inspect_args=(eval "$task" --model "$inspect_model" --log-dir "$log_dir")
    if [[ -n "${INSPECT_MODEL_BASE_URL:-}" ]]; then
        inspect_args+=(--model-base-url "$INSPECT_MODEL_BASE_URL")
    else
        inspect_args+=(--model-base-url "$BASE_URL")
    fi
    inspect "${inspect_args[@]}"
}

run_gaia() {
    run_inspect_eval "gaia" \
        "${GAIA_TASK:-inspect_evals/gaia}" \
        "${GAIA_LOG_DIR:-reports/third_party/open_agi/gaia}" \
        1
}

run_inspect_gpqa() {
    run_inspect_eval "inspect-gpqa" \
        "${INSPECT_GPQA_TASK:-inspect_evals/gpqa_diamond}" \
        "${INSPECT_GPQA_LOG_DIR:-reports/third_party/open_agi/inspect_gpqa}" \
        0
}

run_inspect_generic() {
    : "${INSPECT_TASK:?FATAL: set INSPECT_TASK (e.g. inspect_evals/gaia_level1 or inspect_evals/gpqa_diamond).}"
    run_inspect_eval "inspect" \
        "$INSPECT_TASK" \
        "${INSPECT_LOG_DIR:-reports/third_party/open_agi/inspect}" \
        "${INSPECT_REQUIRE_DOCKER:-0}"
}

run_livecodebench() {
    local dir="${LCB_HARNESS_DIR:-harnesses/LiveCodeBench}"
    require_directory "$dir" \
        'git clone --depth 1 https://github.com/LiveCodeBench/LiveCodeBench.git harnesses/LiveCodeBench && python -m pip install -e harnesses/LiveCodeBench'
    require_endpoint_and_model
    preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    if ! (
        cd "$dir"
        python3 -c 'import lcb_runner.runner.main' 2>/dev/null
    ); then
        echo "FATAL: lcb_runner is not importable from checkout: $dir" >&2
        echo "Install: python -m pip install -e $dir" >&2
        exit 127
    fi
    mkdir -p "${LCB_OUTPUT_DIR:-reports/third_party/open_agi/livecodebench}"
    local release="${LCB_RELEASE_VERSION:-release_v6}"
    local scenario="${LCB_SCENARIO:-codegeneration}"
    local lcb_args=(
        -m lcb_runner.runner.main
        --model "$MODEL"
        --scenario "$scenario"
        --release_version "$release"
    )
    if [[ "${LCB_EVALUATE:-1}" == "1" ]]; then
        lcb_args+=(--evaluate)
    fi
    # OPENAI_BASE_URL is exported. Pass --base-url only when upstream parser lists it.
    local help_txt=""
    help_txt="$(
        cd "$dir"
        PYTHONPATH="${dir}${PYTHONPATH:+:$PYTHONPATH}" \
            python3 -m lcb_runner.runner.main --help 2>&1 || true
    )"
    if [[ "${LCB_PASS_BASE_URL:-auto}" == "1" ]] \
        || { [[ "${LCB_PASS_BASE_URL:-auto}" == "auto" ]] && grep -q -- '--base-url' <<<"$help_txt"; }; then
        lcb_args+=(--base-url "$BASE_URL")
    elif [[ "${LCB_PASS_BASE_URL:-auto}" == "auto" ]]; then
        echo "WARN: LiveCodeBench --help has no --base-url; relying on OPENAI_BASE_URL=${BASE_URL}" >&2
        echo "WARN: model must be registered in upstream lm_styles.py or accepted as OpenAI-compatible." >&2
    fi
    if [[ -n "${LCB_EXTRA_ARGS:-}" ]]; then
        # shellcheck disable=SC2206
        lcb_args+=($LCB_EXTRA_ARGS)
    fi
    echo "Running LiveCodeBench scenario=${scenario} release=${release}"
    (
        cd "$dir"
        PYTHONPATH="${dir}${PYTHONPATH:+:$PYTHONPATH}" \
            python3 "${lcb_args[@]}"
    )
    echo "Retain LiveCodeBench outputs under ${LCB_OUTPUT_DIR:-reports/third_party/open_agi/livecodebench}/. No Pass@k invented here."
}

run_swe_bench() {
    # Official scorer path — does not generate patches. Requires real predictions JSONL or gold.
    if ! python3 -c 'import swebench.harness.run_evaluation' 2>/dev/null; then
        echo "FATAL: swebench package / harness not importable." >&2
        echo "Install: pip install swebench   # or: git clone https://github.com/SWE-bench/SWE-bench.git harnesses/SWE-bench && pip install -e harnesses/SWE-bench" >&2
        echo "See: docs/OPEN_AGI_FRAMEWORKS.md" >&2
        exit 127
    fi
    local preds="${SWE_BENCH_PREDICTIONS_PATH:-}"
    if [[ -z "$preds" ]]; then
        echo "FATAL: set SWE_BENCH_PREDICTIONS_PATH to a real predictions JSONL," >&2
        echo "  or SWE_BENCH_PREDICTIONS_PATH=gold to validate the harness with gold patches." >&2
        echo "This wrapper does not invent model_patch fields or Pass rates." >&2
        echo "JSONL fields: instance_id, model_name_or_path, model_patch" >&2
        exit 2
    fi
    if [[ "$preds" != "gold" ]]; then
        require_file "$preds" "Provide a real agent predictions JSONL (instance_id, model_name_or_path, model_patch)"
    fi
    if [[ "${SWE_BENCH_REQUIRE_DOCKER:-1}" == "1" ]] && ! command -v docker >/dev/null 2>&1; then
        echo "FATAL: SWE-bench harness typically needs Docker Engine." >&2
        echo "Install Docker, or set SWE_BENCH_REQUIRE_DOCKER=0 only for Modal/cloud paths you control." >&2
        exit 2
    fi
    local dataset="${SWE_BENCH_DATASET:-SWE-bench/SWE-bench_Verified}"
    local run_id="${SWE_BENCH_RUN_ID:-affine-$(date -u +%Y%m%dT%H%M%SZ)}"
    local max_workers="${SWE_BENCH_MAX_WORKERS:-4}"
    mkdir -p "${SWE_BENCH_OUTPUT_DIR:-reports/third_party/open_agi/swe_bench}"
    echo "Running swebench.harness.run_evaluation dataset=${dataset} predictions=${preds}"
    local sb_args=(
        -m swebench.harness.run_evaluation
        --dataset_name "$dataset"
        --predictions_path "$preds"
        --max_workers "$max_workers"
        --run_id "$run_id"
    )
    if [[ -n "${SWE_BENCH_INSTANCE_IDS:-}" ]]; then
        # shellcheck disable=SC2206
        sb_args+=(--instance_ids ${SWE_BENCH_INSTANCE_IDS})
    fi
    python3 "${sb_args[@]}"
    echo "Retain SWE-bench harness reports for run_id=${run_id}. No resolved-% invented here."
}

load_env_file

SELECTED=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --harness|--harnesses)
            IFS=',' read -r -a parts <<< "${2:?missing harness name}"
            SELECTED+=("${parts[@]}")
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ ${#SELECTED[@]} -eq 0 ]]; then
    echo "FATAL: select at least one harness (see --help)" >&2
    usage >&2
    exit 2
fi

[[ -f "$OPEN_AGI_YAML" ]] || {
    echo "FATAL: missing packaging config: $OPEN_AGI_YAML" >&2
    exit 2
}
[[ -f "$HARNESS_YAML" ]] || {
    echo "FATAL: missing packaging config: $HARNESS_YAML" >&2
    exit 2
}

require_command curl "install curl from your OS package manager"
require_command python3 "install Python 3.9+"

mkdir -p reports/third_party/open_agi

for harness in "${SELECTED[@]}"; do
    case "$harness" in
        gpqa) run_gpqa ;;
        bbh) run_bbh ;;
        mmlu-pro) run_mmlu_pro ;;
        lm-eval-hard) run_lm_eval_hard ;;
        hle) run_hle ;;
        arc-agi) run_arc_agi ;;
        arc-agi-2) run_arc_agi_2 ;;
        gaia) run_gaia ;;
        inspect-gpqa) run_inspect_gpqa ;;
        inspect) run_inspect_generic ;;
        livecodebench) run_livecodebench ;;
        swe-bench) run_swe_bench ;;
        frontiermath)
            fail_needs_upstream "frontiermath" "https://epoch.ai/frontiermath" \
                "No public full-suite runner. Epoch keeps core data private; request access via math_evals@epoch.ai."
            ;;
        "") ;;
        *)
            echo "FATAL: unknown open-AGI harness: $harness" >&2
            usage >&2
            exit 2
            ;;
    esac
done

echo "Open-AGI harness command(s) finished."
echo "Artifacts under reports/third_party/open_agi/ when upstream produced them."
echo "Provenance registry: configs/open-agi-harnesses.yaml"
