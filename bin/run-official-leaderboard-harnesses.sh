#!/usr/bin/env bash
# Thin launcher for upstream third-party harness CLIs.
# Never invents scores. Never writes heredoc result JSON.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEFAULT_ENV_FILE="${ROOT_DIR}/.env.third-party-harnesses"
HARNESS_YAML="${ROOT_DIR}/configs/third-party-harnesses.yaml"

usage() {
    cat <<'USAGE'
Usage: bin/run-official-leaderboard-harnesses.sh [--harness NAME]...

NAMES: lm-eval | bigcode | fastchat

Runs upstream CLIs only. Fails if the selected upstream tool, checkout,
endpoint, or credential is missing. Does not invent scores.

Configuration:
  configs/third-party-harnesses.env.example
  configs/third-party-harnesses.yaml
  docs/THIRD_PARTY_HARNESSES.md

Endpoint aliases (first non-empty wins):
  AFFINE_HARNESS_ENDPOINT | AFFINE_OPENAI_BASE_URL | OPENAI_BASE_URL | AFFINE_BASE_URL

Note: https://affine.earth/v1 currently serves an HTML SPA, not OpenAI JSON.
Point the base URL at a real OpenAI-compatible /v1 (local or remote) that
answers GET /models with JSON before claiming a MEASURED harness result.
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
        echo "See: docs/THIRD_PARTY_HARNESSES.md" >&2
        exit 127
    fi
}

require_directory() {
    local dir="$1"
    local hint="$2"
    [[ -d "$dir" ]] || {
        echo "FATAL: required upstream checkout missing: $dir" >&2
        echo "Install: $hint" >&2
        echo "See: docs/THIRD_PARTY_HARNESSES.md" >&2
        exit 2
    }
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
        echo "Set AFFINE_HARNESS_ENDPOINT / OPENAI_BASE_URL / AFFINE_BASE_URL to a" >&2
        echo "real OpenAI-compatible /v1 that answers /models with JSON." >&2
        echo "Local wiring option (not a third-party score claim):" >&2
        echo "  python3 llm_llvm_bench/server/affine_v1_interceptor.py 8000" >&2
        echo "  export AFFINE_HARNESS_ENDPOINT=http://127.0.0.1:8000/v1" >&2
        rm -f "$tmp"
        exit 2
    fi
    if ! python3 -c 'import json,sys; json.load(open(sys.argv[1]));' "$tmp" 2>/dev/null; then
        echo "FATAL: GET ${base_url}/models returned HTTP 200 but body is not JSON." >&2
        echo "Body (first 400 bytes):" >&2
        head -c 400 "$tmp" >&2 || true
        echo >&2
        echo "An HTML SPA at /v1 is not a valid OpenAI-compatible API." >&2
        rm -f "$tmp"
        exit 2
    fi
    rm -f "$tmp"
}

run_lm_eval() {
    require_command lm_eval \
        'python -m pip install "lm-eval==0.4.7"  # pin from configs/third-party-harnesses.yaml'
    mkdir -p "${LM_EVAL_OUTPUT_PATH:-reports/third_party/lm_eval}"
    lm_eval \
        --model local-chat-completions \
        --model_args "model=${MODEL},base_url=${BASE_URL}/chat/completions,num_concurrent=${LM_EVAL_CONCURRENCY:-1},max_retries=${LM_EVAL_MAX_RETRIES:-3},tokenized_requests=False" \
        --tasks "${LM_EVAL_TASKS:-mmlu,gsm8k}" \
        --num_fewshot "${LM_EVAL_NUM_FEWSHOT:-0}" \
        --batch_size "${LM_EVAL_BATCH_SIZE:-1}" \
        --log_samples \
        --output_path "${LM_EVAL_OUTPUT_PATH:-reports/third_party/lm_eval}"
}

run_bigcode() {
    local dir="${BIGCODE_HARNESS_DIR:-harnesses/bigcode-evaluation-harness}"
    require_directory "$dir" \
        'git clone --branch v0.1.0 --depth 1 https://github.com/bigcode-project/bigcode-evaluation-harness.git harnesses/bigcode-evaluation-harness && python -m pip install -e harnesses/bigcode-evaluation-harness'
    [[ -f "$dir/main.py" ]] || {
        echo "FATAL: BigCode checkout missing main.py: $dir" >&2
        exit 2
    }
    mkdir -p "$(dirname "${BIGCODE_METRIC_OUTPUT_PATH:-reports/third_party/bigcode/results.json}")"
    if [[ -n "${BIGCODE_GENERATIONS_PATH:-}" ]]; then
        [[ -f "$BIGCODE_GENERATIONS_PATH" ]] || {
            echo "FATAL: BIGCODE_GENERATIONS_PATH does not exist: $BIGCODE_GENERATIONS_PATH" >&2
            exit 2
        }
        python3 "$dir/main.py" \
            --model "${BIGCODE_MODEL_LABEL:-$MODEL}" \
            --tasks "${BIGCODE_TASKS:-humaneval,mbpp}" \
            --load_generations_path "$BIGCODE_GENERATIONS_PATH" \
            --allow_code_execution \
            --metric_output_path "${BIGCODE_METRIC_OUTPUT_PATH:-reports/third_party/bigcode/results.json}"
    else
        : "${BIGCODE_LOCAL_MODEL:?FATAL: Set BIGCODE_LOCAL_MODEL (HF checkpoint/path) or BIGCODE_GENERATIONS_PATH. Upstream BigCode v0.1.0 has no native OpenAI-compatible generation backend.}"
        python3 "$dir/main.py" \
            --model "$BIGCODE_LOCAL_MODEL" \
            --tasks "${BIGCODE_TASKS:-humaneval,mbpp}" \
            --temperature "${BIGCODE_TEMPERATURE:-0.2}" \
            --n_samples "${BIGCODE_N_SAMPLES:-20}" \
            --batch_size "${BIGCODE_BATCH_SIZE:-1}" \
            --allow_code_execution \
            --save_generations \
            --metric_output_path "${BIGCODE_METRIC_OUTPUT_PATH:-reports/third_party/bigcode/results.json}"
    fi
}

run_fastchat() {
    python3 -c 'import fastchat.llm_judge.gen_api_answer' 2>/dev/null || {
        echo "FATAL: FastChat llm_judge is unavailable." >&2
        echo 'Install: python -m pip install "fschat==0.2.36"' >&2
        echo "Or clone: git clone --branch v0.2.36 --depth 1 https://github.com/lm-sys/FastChat.git harnesses/FastChat && python -m pip install -e \"harnesses/FastChat[model_worker,llm_judge]\"" >&2
        echo "See: docs/THIRD_PARTY_HARNESSES.md" >&2
        exit 127
    }
    mkdir -p "$(dirname "${FASTCHAT_ANSWER_FILE:-reports/third_party/fastchat/mt-bench-answers.jsonl}")"
    python3 -m fastchat.llm_judge.gen_api_answer \
        --model "$MODEL" \
        --bench-name "${FASTCHAT_BENCH:-mt_bench}" \
        --openai-api-base "$BASE_URL" \
        --parallel "${FASTCHAT_PARALLEL:-1}" \
        --answer-file "${FASTCHAT_ANSWER_FILE:-reports/third_party/fastchat/mt-bench-answers.jsonl}"
    if [[ "${MTBENCH_RUN_JUDGE:-0}" == "1" ]]; then
        python3 -m fastchat.llm_judge.gen_judgment \
            --bench-name "${FASTCHAT_BENCH:-mt_bench}" \
            --model-list "$MODEL" \
            --parallel "${MTBENCH_JUDGE_PARALLEL:-1}"
    else
        echo "MT-Bench answers written. Judging not run (set MTBENCH_RUN_JUDGE=1 with judge credentials)."
    fi
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
    echo "FATAL: select at least one harness with --harness lm-eval|bigcode|fastchat" >&2
    usage >&2
    exit 2
fi

[[ -f "$HARNESS_YAML" ]] || {
    echo "FATAL: missing packaging config: $HARNESS_YAML" >&2
    exit 2
}

BASE_URL="$(resolve_base_url)" || {
    echo "FATAL: set AFFINE_HARNESS_ENDPOINT, AFFINE_OPENAI_BASE_URL, OPENAI_BASE_URL, or AFFINE_BASE_URL" >&2
    echo "Example: export OPENAI_BASE_URL=http://127.0.0.1:8000/v1" >&2
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

require_command curl "install curl from your OS package manager"
require_command python3 "install Python 3.9+"

needs_openai_preflight=0
for harness in "${SELECTED[@]}"; do
    case "$harness" in
        lm-eval|fastchat) needs_openai_preflight=1 ;;
    esac
done
if [[ "$needs_openai_preflight" -eq 1 ]]; then
    preflight_openai_json "$BASE_URL" "$OPENAI_API_KEY"
fi

mkdir -p reports/third_party

for harness in "${SELECTED[@]}"; do
    case "$harness" in
        lm-eval) run_lm_eval ;;
        bigcode) run_bigcode ;;
        fastchat) run_fastchat ;;
        "") ;;
        *)
            echo "FATAL: unknown harness: $harness" >&2
            exit 2
            ;;
    esac
done

echo "Upstream harness command(s) finished. Artifacts under reports/third_party/ (if produced)."
echo "Provenance config reference: configs/third-party-harnesses.yaml"
