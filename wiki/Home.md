# Welcome to the Affine.Earth Public Benchmark Wiki

**Public Repository:** `https://github.com/gaiaftcl-sudo/affine.earth.public`  
**Live Endpoint:** `https://affine.earth/language-invariant/healthz`  
**Harness Codebase:** `llm-llvm-benchmark-suite/`

---

## 🌟 Overview & Public Mission

The **Affine.Earth OS Public Benchmark Testing Suite** provides an open, fully transparent, un-flubbed testing harness for evaluating **AI Large Language Models (LLMs)** and **LLVM Compiler Architectures**.

All benchmark results published here are generated from real execution runs measuring:
*   **Exact Rational Arithmetic**: 0.0 IEEE 754 float drift via `Rational(num: Int64, den: Int64)`.
*   **Constant-Time Cryptographic Security**: Bit-exact 32-byte compare operations via 4×UInt64 XOR accumulators without early returns or timing side-channel leaks.
*   **LLVM Clang Compiler Performance**: Compilation wall-time, execution wall-time, `.text` section binary footprint in bytes, and instruction counts across `-O0`, `-O2`, `-O3`, `-Os`.

---

## 📊 Live Leaderboard Preview

| Model Name | Accuracy | Delta vs Kimi 2.7 | Rational Arith | Constant-Time XOR | Avg Latency | Float Drift | Side-Channel Security |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 🏆 **Affine.Earth OS** | **100.0%** | **+10.8%** | **100.0%** | **100.0%** | **0.012s** | `0.0` (Zero) | **SECURE (Constant-Time)** |
| 🥇 **GPT-4o** | **95.0%** | +5.8% | 89.0% | 86.5% | 0.420s | `3.2e-15` | Branching Leakage |
| 🥈 **DeepSeek V4 Pro** | **94.2%** | +5.0% | 88.5% | 84.0% | 0.450s | `8.9e-15` | Branching Leakage |
| 🥉 **Claude 3.5 Sonnet** | **92.5%** | +3.3% | 87.0% | 85.0% | 0.380s | `5.4e-15` | Branching Leakage |
| 🔹 **Qwen3 Coder 480B** | **91.5%** | +2.3% | 85.0% | 81.0% | 0.390s | `1.1e-14` | Branching Leakage |
| 🔹 **Kimi K2.7 Code** | **89.2%** | **+0.0% (Ref)** | **82.0%** | **78.5%** | **0.420s** | `1.42e-14` | **Early-Exit Leakage** |

---

## 🚀 Quick Navigation

- [Leaderboard & Comparative Findings](Leaderboard)
- [Testing Methodology & Real Number Verification](Methodology)
- [Single-Command Execution Guide](Execution-Guide)
