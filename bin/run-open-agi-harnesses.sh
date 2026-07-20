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

NAMES:
  hle | arc-agi | gpqa | gaia | swe-bench | livecodebench

Runs upstream CLIs only when a real runner exists. Exits non-zero if the
selected upstream tool, checkout, dataset access, endpoint, or credential is
missing. NEVER invents scores or writes heredoc result JSON.

NEEDS_UPSTREAM harnesses (swe-bench, livecodebench) always exit 3 with
pointers — there is no fake Pass@k path.

Configuration:
  configs/open-agi-harnesses.yaml
  configs/third-party-harnesses.env.example
  docs/OPEN_AGI_FRAMEWORKS.md
  docs/THIRD_PARTY_HARNESSES.md

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
    echo "FATAL: harness '${name}' status=NEEDS_UPSTREAM" >&2
    echo "No honest Affine OpenAI-compatible thin wrapper is wired yet." >&2
    echo "Upstream: ${upstream}" >&2
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

run_gpqa() {
    require_command lm_eval \
        'python -m pip install "lm-eval==0.4.7"  # pin from configs/open-agi-harnesses.yaml'
    require_endpoint_and_model
    preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    mkdir -p "${GPQA_OUTPUT_PATH:-reports/third_party/open_agi/gpqa}"
    lm_eval \
        --model local-chat-completions \
        --model_args "model=${MODEL},base_url=${BASE_URL}/chat/completions,num_concurrent=${LM_EVAL_CONCURRENCY:-1},max_retries=${LM_EVAL_MAX_RETRIES:-3},tokenized_requests=False" \
        --tasks "${GPQA_TASKS:-gpqa_diamond_zeroshot}" \
        --num_fewshot "${GPQA_NUM_FEWSHOT:-0}" \
        --batch_size "${GPQA_BATCH_SIZE:-1}" \
        --log_samples \
        --output_path "${GPQA_OUTPUT_PATH:-reports/third_party/open_agi/gpqa}"
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
        echo "FATAL: HLE dataset cais/hle is gated on Hugging Face." >&2
        echo "Accept terms at https://huggingface.co/datasets/cais/hle then set HF_TOKEN." >&2
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
    echo "Copy or symlink upstream HLE JSON artifacts into ${out_dir}/ for provenance."
}

run_arc_agi() {
    local dir="${ARC_AGI_HARNESS_DIR:-harnesses/arc-agi-benchmarking}"
    require_directory "$dir" \
        'git clone --depth 1 https://github.com/arcprize/arc-agi-benchmarking.git harnesses/arc-agi-benchmarking && (cd harnesses/arc-agi-benchmarking && uv sync)'
    : "${ARC_AGI_CONFIG:?FATAL: set ARC_AGI_CONFIG to a models.yml config name from the ARC Prize checkout (not a fake score).}"
    local data_dir="${ARC_AGI_DATA_DIR:-}"
    if [[ -z "$data_dir" ]]; then
        if [[ -d "$dir/data/sample/tasks" ]]; then
            data_dir="$dir/data/sample/tasks"
            echo "WARN: ARC_AGI_DATA_DIR unset; using bundled sample tasks only (not full ARC-AGI)." >&2
        else
            echo "FATAL: set ARC_AGI_DATA_DIR to a folder of ARC task .json files." >&2
            echo "ARC-AGI-1: git clone https://github.com/fchollet/ARC-AGI.git data/arc-agi" >&2
            echo "ARC-AGI-2: git clone https://github.com/arcprize/ARC-AGI-2.git data/arc-agi" >&2
            exit 2
        fi
    fi
    [[ -d "$data_dir" ]] || {
        echo "FATAL: ARC_AGI_DATA_DIR is not a directory: $data_dir" >&2
        exit 2
    }
    require_endpoint_and_model
    # ARC Prize adapters typically use provider keys; OpenAI-compatible base URL
    # must be configured inside upstream models.yml / adapter — we still require
    # a JSON /models preflight when ARC_AGI_PREFLIGHT_OPENAI=1 (default).
    if [[ "${ARC_AGI_PREFLIGHT_OPENAI:-1}" == "1" ]]; then
        preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
    fi
    local save_dir="${ARC_AGI_SUBMISSION_DIR:-reports/third_party/open_agi/arc_agi/submissions}"
    mkdir -p "$save_dir"
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
    echo "ARC-AGI submissions under ${save_dir}. Score with upstream scoring.py (see docs/OPEN_AGI_FRAMEWORKS.md)."
}

run_gaia() {
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
    mkdir -p "${GAIA_LOG_DIR:-reports/third_party/open_agi/gaia}"
    # Inspect model string: openai/<model_id>; base URL via OPENAI_BASE_URL.
    local inspect_model="${GAIA_INSPECT_MODEL:-openai/${MODEL}}"
    local task="${GAIA_TASK:-inspect_evals/gaia}"
    if [[ "${GAIA_REQUIRE_DOCKER:-1}" == "1" ]] && ! command -v docker >/dev/null 2>&1; then
        echo "FATAL: GAIA Inspect eval typically needs Docker Engine for tool sandboxes." >&2
        echo "Install Docker, or set GAIA_REQUIRE_DOCKER=0 only if you know your solver needs none." >&2
        exit 2
    fi
    inspect eval "$task" \
        --model "$inspect_model" \
        --log-dir "${GAIA_LOG_DIR:-reports/third_party/open_agi/gaia}"
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
    echo "FATAL: select at least one harness with --harness hle|arc-agi|gpqa|gaia|swe-bench|livecodebench" >&2
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
        hle) run_hle ;;
        arc-agi) run_arc_agi ;;
        gaia) run_gaia ;;
        swe-bench)
            fail_needs_upstream "swe-bench" "https://github.com/SWE-bench/SWE-bench"
            ;;
        livecodebench)
            fail_needs_upstream "livecodebench" "https://github.com/LiveCodeBench/LiveCodeBench"
            ;;
        "") ;;
        *)
            echo "FATAL: unknown open-AGI harness: $harness" >&2
            usage >&2
            exit 2
            ;;
    esac
done

echo "Open-AGI harness command(s) finished (or exited NEEDS_UPSTREAM)."
echo "Artifacts under reports/third_party/open_agi/ when upstream produced them."
echo "Provenance registry: configs/open-agi-harnesses.yaml"
