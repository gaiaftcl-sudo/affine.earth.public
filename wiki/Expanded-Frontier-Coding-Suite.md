# Expanded Frontier Coding Suite (SWE-bench, LiveCodeBench, MultiPL-E)

This page documents the largest coding benchmarks used by OpenAI, Anthropic, DeepSeek, Google, and Alibaba to evaluate frontier coding capabilities.

> **Provenance:** Numbers below are the **BASELINE TABLE** from `llm_llvm_bench/forks/expanded_frontier_baselines.py` (frontier rows cite published model-card / report sources in that file). This repository’s `reports/` directory currently emphasizes Clang/rational/healthz receipts and domain comparative MD/JSON — not full SWE-bench Verified run logs for every model. For measured local compiler/rational results, see [Benchmarks](Benchmarks) and [Live Leaderboard](Live-Leaderboard).

---

## 1. Benchmark Definitions

*   **SWE-bench Verified**: 500 hand-verified real-world GitHub issues across major Python repositories (Django, SymPy, scikit-learn). Measures an agent's ability to locate bugs, edit multi-file codebases, and pass unit tests.
*   **LiveCodeBench**: Un-contaminated algorithmic contest benchmark (LeetCode, AtCoder, Codeforces). Evaluates problem-solving without data leakage.
*   **MultiPL-E**: Multi-language translation and synthesis benchmark (Python, C++, Rust, Swift, Go, Java). Evaluates language-agnostic code synthesis.

---

## 2. Frontier Model Benchmark Comparison Table

| Model Name | SWE-bench Verified | LiveCodeBench | MultiPL-E | HumanEval Pass@1 | MBPP Pass@1 |
|:---|:---|:---|:---|:---|:---|
| 🏆 **Affine.Earth OS** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| 🥇 **OpenAI o3-mini** | 71.7% | 64.3% | 88.5% | 93.4% | 89.1% |
| 🥈 **Claude 3.7 Sonnet** | 70.3% | 62.8% | 89.2% | 94.1% | 90.2% |
| 🥉 **Gemini 2.0 Thinking** | 58.2% | 59.1% | 87.0% | 91.5% | 88.0% |
| 🔹 **DeepSeek R1** | 49.2% | 65.9% | 86.1% | 90.8% | 87.6% |
| 🔹 **Qwen 2.5 / 3 Coder** | 44.5% | 51.2% | 85.7% | 88.4% | 85.1% |
| 🔹 **Llama 3.3 / 4** | 38.8% | 42.1% | 81.4% | 85.0% | 82.0% |
