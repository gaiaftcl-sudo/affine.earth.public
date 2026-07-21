# Franklin S¹–S⁴ Projection Language Game

The wrapper supplies evidence, Franklin proposes a typed candidate, the wrapper
runs the task-native validator, and a miss is reinjected with the observed
discrepancy. A dialogue is capped at 29 turns; the cap does not establish that
an unresolved answer is known.

## Why projections may be absent

- **S1 — complete ingestion:** bind identity, revision, full input, modality,
  legal action/answer contract, and (for ARC-AGI-3) trajectory history.
- **S2 — candidate boundary:** retain every transformation, action, or answer
  still compatible with S1 rather than silently selecting one.
- **S3 — discriminating evidence:** request a legal replay, environment probe,
  citation, or consistency check capable of removing candidates.
- **S4 — verified projection:** retain the typed candidate, validator, result,
  and alternatives. `LOCKED` is permitted only after the named task-native
  validator accepts it **and** the Jordan loop bound is closed (zero remainder
  against C4); otherwise emit `REINJECT`. Every play must pull prior CLOSED
  language-game experiences before proposing.

## Track mapping

| Track | S1 | S2 | S3 | S4 |
| --- | --- | --- | --- | --- |
| ARC-AGI-2 | Train pairs and test grid | Demonstration-consistent transforms | Demo replay/output-domain check | Typed grid; labels determine held-out match |
| ARC-AGI-3 | Observation, legal actions, history | Legal next action/policy | `E.step` result | Valid trajectory/parquet and official evaluator |
| HLE | Official record/modality/format | Typed answers with sources | Citation + exact-format check | CAIS artifact and judge receipt |

## Wrapper protocol

1. Emit `WRAPPER_EVIDENCE` containing S1–S3 and the previous gate result.
2. Franklin replies with a typed S4 candidate, named validator, status, and
   unresolved alternatives.
3. The wrapper runs the named validator and records its raw result.
4. On acceptance, serialize the track-native artifact. On a miss, inject the
   failure as the next `WRAPPER_EVIDENCE`; do not replace it silently.

Run a recorded local dialogue:

```bash
python3 scripts/run_franklin_s4_projection_language_game.py --max-turns 29
```

The runner requires a real OpenAI-compatible endpoint from
`FRANKLIN_S4_BASE_URL`, `HLE_LOCAL_BASE_URL`, `OPENAI_BASE_URL`, or
`AFFINE_HARNESS_ENDPOINT`; it does not start the repository interceptor.
# Franklin S¹–S⁴ Projection Language Game

This protocol turns a one-shot benchmark response into a bounded two-way
exchange: the wrapper supplies task evidence, Franklin proposes a typed
candidate, the wrapper runs the track-native validator, and a miss returns to
Franklin with the observed discrepancy. The exchange is capped at 29 turns per
item; a cap is not a score or a claim that the remaining answer is known.

## Why a projection may not be visible

The live Franklin dialogue identified four operational blockers:

1. **S1 — complete ingestion:** ARC needs every demonstration and test grid;
   ARC-AGI-3 additionally needs the current observation, legal actions, and
   episode history; HLE needs the complete official record, modality, and
   answer contract.
2. **S2 — candidate boundary:** a projection cannot be unique while more than
   one transformation, action, or answer remains consistent with S1.
3. **S3 — discriminating evidence:** the wrapper needs a legal replay, probe,
   citation, or consistency test that rules out candidates. For ARC-AGI-3 this
   is an environment action, not an invented state transition.
4. **S4 — verified projection:** the candidate is locked only after the
   correct task-native check accepts it **and** the Jordan loop bound closes
   (zero remainder against C4). A response, model confidence, candidate
   presence, or local transport success does not establish exact-match
   correctness. Pull prior CLOSED experiences every play.

## Track contracts

| Track | S1 ingestion | S2 candidates | S3 discriminator | S4 lock |
| --- | --- | --- | --- | --- |
| ARC-AGI-2 | All train input/output pairs, test grid, grid contract | Transformations replaying every demo | Demonstration replay and output-domain checks | Typed output grid accepted by replay; held-out score only when labels exist |
| ARC-AGI-3 | Current observation, legal actions, full trajectory | Legal next actions/policies | `E.step` observation after a legal action | Framework-valid trajectory serialized to parquet and accepted by the official evaluator |
| HLE | Official question ID/revision, prompt, modality, response instructions | Typed answers with supporting facts | Exact-format and source/consistency checks | CAIS prediction artifact and official judge result |

## Wrapper ↔ Franklin turns

1. The wrapper emits `WRAPPER_EVIDENCE` containing task identity, answer
   contract, S1, S2, S3, and the last gate result.
2. Franklin responds with an S4 object: typed candidate, named validator,
   `LOCKED` or `REINJECT`, and unresolved alternatives.
3. The wrapper invokes the named validator and records its raw result.
4. A pass retains the S4 object and serializes the track-native artifact.
5. A miss is reinjected with the failing evidence and one next discriminating
   observation. The wrapper does not silently replace the candidate.

`LOCKED` means only “accepted by the named local/track-native validator.” An
official score requires the relevant external evaluator receipt.

## Implementation

`llm_llvm_bench.arc.franklin_s4_projection` supplies the shared prompt and
serializable evidence turn. Run a live loopback dialogue with:

```bash
python3 scripts/run_franklin_s4_projection_language_game.py --max-turns 29
```

The runner writes an append-only JSONL transcript and summary under
`reports/franklin_s4_language_game_<timestamp>/`. It requires a real
OpenAI-compatible endpoint through `FRANKLIN_S4_BASE_URL`,
`HLE_LOCAL_BASE_URL`, `OPENAI_BASE_URL`, or `AFFINE_HARNESS_ENDPOINT`; it
does not launch the repository's deterministic interceptor.
