# Franklin S¹–S⁴ projection language game

The benchmark wrapper now exchanges evidence with Franklin before emitting an
artifact: `S1–S3 evidence → typed S4 candidate → validator → lock or reinject`.

This applies to ARC-AGI-2 grids, ARC-AGI-3 legal trajectories, and HLE typed
answers. It does not turn a local conversation into an official score; an S4
candidate becomes locked only when its named task-native validator accepts it.

**Exams consume this protocol.** The miss → reinject loop
([Exam Miss Reinjection Loop](Exam-Miss-Reinjection-Loop)) and the ARC-2 /
ARC-3 / HLE mastery stuck paths call the same shared client
(`llm_llvm_bench.exam.s4_client`) and parse the same `LOCKED|REINJECT` JSON
(`llm_llvm_bench.arc.franklin_s4_projection`). Ad-hoc one-shot prompts are not
the exam contract.

See [the full protocol](../docs/FRANKLIN_S4_PROJECTION_LANGUAGE_GAME.md).
