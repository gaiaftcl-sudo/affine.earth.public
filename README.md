# LLM & LLVM Benchmark Testing Suite (`llm-llvm-benchmark-suite`)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](pyproject.toml)
[![Tests: 8 Passed](https://img.shields.io/badge/tests-8%20passed-green.svg)](tests/)

A unified, production-grade, standalone real-world domain testing suite for evaluating **AI Large Language Models (LLMs)** and **LLVM Compiler Infrastructures**. Completely decoupled from external OS frameworks.

---

## 🎯 Architecture Overview

```
                          llm-llvm-benchmark-suite/
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 🤖 LLM Evaluation Harness                          ⚙️ LLVM Compiler Harness
 ├── Real-World Code Domain (Python, C, Swift)     ├── Opt Levels (-O0, -O2, -O3, -Os, -Oz)
 ├── Complex Logic & Reasoning (CoT, Math)          ├── Architecture Target (AArch64, x86_64)
 ├── Tool Use & API Schema Extraction               ├── Exec Wall-Time & Compile Time
 ├── Long-Context Retrieval (Needle/Haystack)       ├── .text Section Code Size Analysis
 └── Multi-Provider (OpenAI, Claude, Ollama, Mock)  └── LLVM IR Instruction Breakdown
                                     │
                                     ▼
                   📊 Unified Reporting & Web Dashboard
                   ├── JSON / Markdown Comparison Reports
                   └── Interactive Dark-Mode Web Server (http://127.0.0.1:8888)
```

---

## 🚀 Quickstart

### 1. Installation

```bash
cd llm-llvm-benchmark-suite
pip install -e .
```

### 2. Run LLM Benchmarks

Run evaluations across coding, reasoning, and tool-use domain suites:

```bash
# Run with Mock Provider (offline debug mode)
llm-llvm-bench llm run --models mock-gpt-4o,mock-claude --provider mock --suites code,reasoning,tool_use

# Run with OpenAI or OpenAI-compatible API (vLLM / LM Studio / Ollama / DeepSeek)
export OPENAI_API_KEY="your-api-key"
llm-llvm-bench llm run --models gpt-4o,gpt-4o-mini --provider openai --suites code,reasoning
```

### 3. Run LLVM Compiler Performance Benchmarks

Benchmark local `clang` compilation wall-time, execution speed, `.text` section binary footprint, and LLVM IR instruction metrics:

```bash
llm-llvm-bench llvm run --opt-levels -O0,-O2,-O3,-Os --compiler clang
```

### 4. Launch Interactive Web Dashboard

Launch the built-in dark-mode web application for visual charts, leaderboards, and side-by-side metric comparisons:

```bash
llm-llvm-bench serve --port 8888
```

Open `http://127.0.0.1:8888` in your browser.

---

## 🧪 Testing Suite

Run the automated test suite (`pytest`):

```bash
pytest tests/
```

Expected output: `8 passed in 0.99s`.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
