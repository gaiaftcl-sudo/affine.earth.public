# Language Games — ARC-AGI-3

Pre-submission specification for [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3). This page describes the agent/parquet track; it does not claim a score.

## 1. Game, moves, and win condition

ARC-AGI-3 is an interactive agent game. The environment opens an episode,
emits an observation, accepts a legal agent action, and returns the next
observation or a terminal state. The agent's answer is an action trajectory,
serialized through the official starter into `submission.parquet`. The win
condition is the official environment/evaluator's episode success criterion,
not a guessed grid or a parquet file that merely exists.

## 2. Input/output state

- Input: the official agent framework, environment assets, observations, and
  episode metadata.
- State: current observation plus complete permitted action/observation
  history for the current episode.
- Output: framework-produced `submission.parquet`.
- Evaluation: Kaggle runs the official evaluator and later issues a result.

The agent owns its action choice. The environment owns the post-action state.

## 3. Affine communication invariants

Episode ID, step index, legal-action set, complete trajectory history,
environment observations, terminal flag, and artifact row provenance must not
drift. The agent cannot infer a successful post-action state in place of the
environment response, and no cross-episode state may enter a trajectory.

## 4. Context-setting protocol

1. Load the current starter's observation/action contracts.
2. Bind episode ID, step, observation, legal actions, and terminal status.
3. Select from actions legal in the present state using the accumulated
   episode history.
4. Send one action and read the environment's returned state before planning
   another move.
5. Serialize only validly terminated trajectories through the official
   pipeline.

## 5. Formal state transition

For state `s_t`, action set `A(s_t)`, policy `π`, and environment `E`:

```text
a_t = π(history_t), where a_t ∈ A(s_t)
s_(t+1), r_t, terminal_t = E.step(s_t, a_t)
history_(t+1) = history_t ⧺ [(s_t, a_t, r_t, s_(t+1))]
```

Only validated terminal trajectories transition to the official parquet
serializer.

## 6. Local drift checks

| Check | Distinguishes |
| --- | --- |
| `make verify-local` | Starter/framework integration drift |
| Asset version/checksum manifest | Stale or substituted official assets |
| Action validator | Illegal current-state action |
| Trace and terminal validator | Missing/reordered turns or unconfirmed completion |
| Parquet schema/provenance validator | Artifact drift |
| Local scorecard and preflight receipt | Local evidence, not public score |

Changed starter APIs, assets, or parquet schema are exam-spec drift. A stable
framework rejecting an action or trajectory is understanding drift.

## 7. Affine UI mapping

- **Linguistic membrane:** preserves the observation and legal action language.
- **Formal:** models episode state, action legality, transition history, and
  terminal predicates.
- **Coding:** invokes the starter framework and validates the parquet artifact.

## 8. Public-submission gate

**No public ARC-AGI-3 submission until `make verify-local`, asset validation,
action/trace/terminal validation, parquet validation, and a preflight receipt
are green.** A pending Kaggle result has no public score until Kaggle returns
one.
