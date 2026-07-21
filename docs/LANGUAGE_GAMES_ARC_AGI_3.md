# Language Game: ARC Prize 2026 — ARC-AGI-3

This is pre-submission technical doctrine for the public test repository. It
describes the ARC-AGI-3 agent-track contract and the checks required before any
further Kaggle submission. It does not claim a score.

Official competition: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3>

## 1. The game

ARC-AGI-3 is an interactive agent game, not the static
`attempt_1`/`attempt_2` grid game used by ARC-AGI-2. The environment provides
an observation, the agent chooses an action from the official framework's
action space, and the environment returns the next observation and terminal
state. The task is solved through an action trajectory rather than a single
grid prediction.

The turns are:

1. Environment initializes an episode and exposes the permitted observation.
2. Agent reads the current observation and retained episode history.
3. Agent chooses exactly one framework-valid action.
4. Environment applies the action and returns the next observation or a
   terminal result.
5. The agent stops only through the framework's valid terminal pathway.
6. The starter evaluation records the trajectory outcome into the required
   `submission.parquet`.

The win condition is the official evaluator's episode-level success criterion,
encoded by the supplied agent framework and scored by Kaggle. A well-written
natural-language explanation, a guessed grid, or a parquet file that merely
exists is not a win.

## 2. Input, output, and state

| Element | Contract |
| --- | --- |
| Input | The official agent framework, environment assets, observation objects, and episode metadata supplied by the competition. |
| State | Current observation plus the complete permitted action/observation history for the current episode. |
| Action | Only an action representable and accepted by the official environment API. |
| Transition | Environment-owned: `s_(t+1) = step(s_t, a_t)`. The agent does not invent a transition result. |
| Output | `submission.parquet` produced by the official starter pipeline. |
| Evaluation | Kaggle runs the official environment/evaluator and publishes a score when processing completes. |

The parquet is an evidence carrier for the official evaluator, not an arbitrary
table. Its schema, row identity, and action-result provenance must remain
coupled to the episode that generated it.

## 3. Communication invariants for Affine

1. **Episode binding:** every decision is tied to one episode ID and its
   current framework observation.
2. **History integrity:** the agent's answer state contains the complete
   allowed trajectory; no turn is silently dropped, reordered, or imported
   from another episode.
3. **Action validity:** the emitted action is in the environment's declared
   action language before it is sent.
4. **Observation authority:** environment responses are facts of state; the
   agent does not replace them with inferred success.
5. **Termination integrity:** a terminal claim occurs only when the framework
   reports a valid terminal state.
6. **Artifact provenance:** each parquet record is generated from the
   validated trajectory and preserves the official row/schema contract.

## 4. Context-setting protocol

Before an action, the agent must:

1. Read the starter framework's observation and action contracts for the
   current competition version.
2. Bind the current episode ID, step index, observation, legal actions, and
   terminal flags into a durable turn record.
3. Derive a finite set of actions that are legal in the present state.
4. Select an action using the current observation *and* the accumulated
   episode history, not a generic task template.
5. Submit one legal action and read the returned observation before planning
   the next turn.
6. On termination, verify the framework terminal result and serialize the
   official artifact through the supplied pipeline.

Context is established per turn and per episode. Reusing a prior episode's
state or assuming an action succeeded without reading the next observation is
context drift.

## 5. Formal question-to-answer state change

For episode state `s_t`, legal-action set `A(s_t)`, policy `π`, and environment
transition `E`:

```text
a_t = π(history_t)  where a_t ∈ A(s_t)
s_(t+1), r_t, terminal_t = E.step(s_t, a_t)
history_(t+1) = history_t ⧺ [(s_t, a_t, r_t, s_(t+1))]
```

The artifact transition happens only after the official framework identifies
the episode boundary:

```text
validated episode trajectories → official serializer → submission.parquet
```

The agent owns `π`; the environment owns `E`. Treating a predicted
post-action state as if it were an observed state breaks the game.

## 6. Local drift checks

| Check | Detects |
| --- | --- |
| Official starter `make verify-local` | Framework, dependency, and official local-evaluation integration drift. |
| Environment asset manifest and checksum/version record | Stale or substituted competition assets. |
| Per-turn action validator | Actions outside the current legal action space. |
| Episode trace validator | Missing, duplicated, cross-episode, or out-of-order state transitions. |
| Terminal-state validator | Claims of completion without an environment terminal response. |
| Parquet schema and row-provenance validator | Artifact drift between trajectory state and required submission format. |
| Saved local scorecard and preflight receipt | Local evidence only; it is not a public leaderboard score. |

A failure caused by a changed starter API, environment asset, or parquet schema
is **exam-spec drift**. A stable framework that rejects the policy's action,
trace, or goal state is **agent-understanding drift**. Neither condition
licenses a public submission.

## 7. Affine.Earth UI language-game mapping

| UI game | ARC-AGI-3 role |
| --- | --- |
| Linguistic membrane | Binds the current observation to episode identity and makes the legal action language explicit. |
| Formal game | Maintains the state machine, legal-action constraints, transition log, and terminal predicate. |
| Coding game | Calls the starter framework, validates action/artifact schemas, and writes the official parquet through its serializer. |

The UI narrative is secondary to the episode trace. The authoritative answer
state is the action accepted by the environment and its observed transition.

## 8. Submission gate

**No public ARC-AGI-3 Kaggle submission is permitted until local validators are
green.** The minimum green set is `make verify-local`, official asset/version
validation, action and episode-trace validation, terminal-state validation, and
parquet-schema validation with a saved preflight receipt. A pending submission
has no score until Kaggle returns one.

## 9. Format from top scores

After the trajectory state change above, the typed artifact is
`submission.parquet` with columns
`row_id, game_id, end_of_game, score` (bool / int64 on the last two). See
[KAGGLE_ARC_TOP_SCORE_FORMATS.md](KAGGLE_ARC_TOP_SCORE_FORMATS.md) and wiki
[Language-Games-ARC-AGI-3](../wiki/Language-Games-ARC-AGI-3.md) §9.

FoT contrast: our probe ref **54875048** scored **publicScore 0.12** on that
exact schema; LB leaders sit near **1.86**. Format acceptance ≠ agent mastery.
