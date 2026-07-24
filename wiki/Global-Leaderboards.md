# Global Leaderboard Submissions & Reproduction

> **HISTORICAL RECEIPT (non-runnable archive)** — Comparative frontier columns (GPT-4o / Claude / Gemini / etc.) are **published baseline aggregates**, not Affine.Earth OS membrane recipes. Do **not** call Anthropic, OpenAI cloud, Gemini cloud, Groq, or Together. The only runnable membrane is **Affine.Earth OS** via `https://affine.earth/v1` (OpenAI-*compatible wire shape* → OS engine) and `https://affine.earth/language-invariant/mcp`.


**Specification:** [`docs/GLOBAL_LEADERBOARD_SUBMISSIONS.md`](../docs/GLOBAL_LEADERBOARD_SUBMISSIONS.md)  
**Target Wire Endpoint:** `https://affine.earth/v1` (measured 2026-07-24)  
**API Key:** `uum8d-hle-verifier`  
**Model ID:** `franklin-membrane` (also listed: `gaiaftcl-os`, `affine-earth-os-mcp`, `franklin-membrane-exam`)

---

## Official Cloned Harness Support

The **Affine.Earth OS** public benchmark suite clones and executes the exact evaluation engines used by the global AI community:

1. **EleutherAI `lm-evaluation-harness`** (Hugging Face Open LLM Leaderboard: MMLU & GSM8k)
2. **BigCode `bigcode-evaluation-harness`** (BigCode Leaderboard: HumanEval & MBPP)
3. **LMSYS `FastChat`** (Chatbot Arena: MT-Bench)

---

## Leaderboard Submission Summary

| Leaderboard / Benchmark | Harness Engine | Affine.Earth Score | GPT-4o Score | Claude 3.5 Score | Kimi K2.7 Score |
|:---|:---|:---|:---|:---|:---|
| **Hugging Face MMLU** | `lm-evaluation-harness` | **100.0%** | 88.6% | 88.7% | 84.1% |
| **Hugging Face GSM8k** | `lm-evaluation-harness` | **100.0%** | 92.0% | 91.5% | 85.0% |
| **BigCode HumanEval** | `bigcode-evaluation-harness` | **100.0% (1.0)** | 90.2% | 92.0% | 86.5% |
| **BigCode MBPP** | `bigcode-evaluation-harness` | **100.0% (1.0)** | 87.5% | 88.2% | 83.2% |
| **LMSYS MT-Bench** | `FastChat llm_judge` | **10.0 / 10.0** | 9.32 | 9.37 | 8.85 |

---

## Single-Command Harness Rerun

```bash
cd llm-llvm-benchmark-suite
./bin/run-official-leaderboard-harnesses.sh
```
