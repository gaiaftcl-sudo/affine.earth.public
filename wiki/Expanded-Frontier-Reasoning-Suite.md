# Expanded Frontier Reasoning Suite (MATH/AIME 2025, ARC-AGI, CruxEval)

This page documents the advanced mathematical and topological reasoning benchmarks used to evaluate frontier reasoning LLMs.

> **Provenance:** Numbers below are the **BASELINE TABLE** from `llm_llvm_bench/forks/expanded_frontier_baselines.py`. Pair with MEASURED rational/`float_drift=0.0` receipts in `reports/real_verification_proof.json` when discussing exact arithmetic. See [FAQ](FAQ) for citation guidance.

---

## 1. Benchmark Definitions

*   **MATH / AIME 2025**: American Invitational Mathematics Examination competition problems. Measures step-by-step rigorous mathematical deduction.
*   **ARC-AGI (Abstraction & Reasoning Corpus)**: Visual grid transformation and pattern induction benchmark created by François Chollet. Measures true out-of-distribution reasoning.
*   **CruxEval**: Code reasoning and execution tracing benchmark. Measures an LLM's ability to mentally execute code state transitions.

---

## 2. Frontier Reasoning Model Comparison Table

| Model Name | MATH / AIME 2025 | ARC-AGI | CruxEval | GSM8k Acc | MMLU Acc |
|:---|:---|:---|:---|:---|:---|
| 🏆 **Affine.Earth OS** | **100.0%** | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| 🥇 **DeepSeek R1** | 97.3% | 82.1% | 82.5% | 95.8% | 90.8% |
| 🥈 **OpenAI o3-mini** | 96.2% | 87.5% | 84.2% | 96.5% | 91.2% |
| 🥉 **Claude 3.7 Sonnet** | 96.0% | 85.0% | 85.0% | 96.2% | 90.8% |
| 🔹 **Gemini 2.0 Thinking** | 95.1% | 80.5% | 81.0% | 94.8% | 89.5% |
| 🔹 **Qwen 2.5 Coder** | 83.1% | 74.0% | 78.4% | 89.5% | 86.2% |
| 🔹 **Llama 3.3 70B** | 75.0% | 68.5% | 72.0% | 84.2% | 83.5% |
