# Open ARC solvers usable offline (MIT/Apache)

Inventory for local ARC-AGI-2 mastery. No Kaggle submit from this tree.

| Source | License | Local CPU? | Notes |
| --- | --- | --- | --- |
| [victorvikram/ARC-icecuber](https://github.com/victorvikram/ARC-icecuber) (top-quarks ARC-solution) | MIT | Yes (C++17) | **Vendored here.** Depth-2 search; ~129/419 on ARC-1 eval historically. Adapted for macOS + absolute sample dirs. |
| [michaelhodel/arc-dsl](https://github.com/michaelhodel/arc-dsl) | MIT | Yes | Hand-written DSL solvers for ARC-1 training tasks; not an inference searcher for AGI-2. Concepts inform our Python DSL. |
| [TrelisResearch/minimal-arc](https://github.com/TrelisResearch/minimal-arc) | Apache-2.0 | Partial | DSL / LLM-guided search / TTT; heavier deps; not vendored this pass. |
| Kaggle NVARC / MCP AGI-2 notebooks | Notebook terms | GPU / models | Format study only under `evidence/arc-format-study/notebooks/`; not offline CPU ownership. |

**Chosen engine for step-change:** MIT arc-icecuber via `llm_llvm_bench/arc/icecuber_adapter.py`, hybridized with the replay-gated Python DSL in `kaggle/arc-prize-2026-agi-2/arc_agi_2_kaggle.py`.
