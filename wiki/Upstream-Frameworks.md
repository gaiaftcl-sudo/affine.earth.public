# Upstream frameworks

We do **not** re-teach full third-party harness tutorials here. This wiki focuses on **proof we ran tests** and **how we scored**. For deep docs, use the upstream projects.

Agent commands that wrap these tools: [AGI agent execution](AGI-Agent-Execution).  
Our scoring / provenance rules: [How we tested](How-We-Tested) · [Results & Scores](Results-And-Scores).

---

## Open AGI / hard evaluation

| Framework | Upstream |
|:---|:---|
| Humanity's Last Exam | https://lastexam.ai/ · https://huggingface.co/datasets/cais/hle |
| ARC-AGI / ARC-AGI-2 | https://arcprize.org/ · https://github.com/arcprize/ARC-AGI-2 |
| GPQA | https://arxiv.org/abs/2311.12022 |
| BIG-Bench Hard | https://github.com/suzgunmirac/BIG-Bench-Hard |
| MMLU-Pro | https://github.com/TIGER-AI-Lab/MMLU-Pro |
| GAIA | https://huggingface.co/gaia-benchmark |
| Inspect AI | https://inspect.aisi.org.uk/ · https://github.com/UKGovernmentBEIS/inspect_ai |
| SWE-bench | https://www.swebench.com/ · https://github.com/princeton-nlp/SWE-bench |
| LiveCodeBench | https://livecodebench.github.io/ |
| FrontierMath | https://arxiv.org/abs/2411.04872 |

---

## Classic LLM / coding harnesses

| Framework | Upstream |
|:---|:---|
| EleutherAI lm-evaluation-harness | https://github.com/EleutherAI/lm-evaluation-harness |
| BigCode evaluation harness | https://github.com/bigcode-project/bigcode-evaluation-harness |
| LMSYS FastChat / MT-Bench | https://github.com/lm-sys/FastChat |
| LLVM test-suite | https://github.com/llvm/llvm-test-suite |

---

## Thin local stubs (optional)

Older wiki pages that duplicated upstream tutorials are **slim / deprecated** — prefer this page + the agent launcher:

- [EleutherAI lm-evaluation-harness](EleutherAI-lm-evaluation-harness) (stub)
- [BigCode bigcode-evaluation-harness](BigCode-bigcode-evaluation-harness) (stub)
- [LMSYS FastChat MT-Bench](LMSYS-FastChat-MT-Bench) (stub)
- [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction) (slim)
- Repo: [`docs/THIRD_PARTY_HARNESSES.md`](https://github.com/gaiaftcl-sudo/affine.earth.public/blob/main/docs/THIRD_PARTY_HARNESSES.md)
