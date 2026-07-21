# Language Games — ARC-AGI-3

Pre-submission specification for [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3). This page describes the agent/parquet track; it does not claim a score.

**Franklin root baseline:**
[UUM-8D game comprehension & bond resolution](../docs/FRANKLIN_UUM8D_GAME_COMPREHENSION_SYSTEM_PROMPT.md)
— Phase I interactive probe (actions 1–7) → C4 invariant → Jordan bond → verified JSON.

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

The ARC local preflight also follows the
[ARC UI Audit Orchestrator](ARC-UI-Audit-Orchestrator): macOS permission
checks, VideoToolbox capture, task-bound Cursor injection, per-episode
nine-cell reduction, extracted JSON validation, and a recorded `SIGINT` stop.
The audit validates local evidence and the native `submission.parquet`
contract. `configs/NO_KAGGLE_SUBMIT.lock` remains in place until an explicit
steward-authorized submit; an audit GREEN result is not authorization.

### Live FoT local protocol

The local executable is `scripts/arc_agi3_language_game.py`. It plays the
downloaded official environment, not a static grid surrogate:

- bind one `game_id` to its observation and action language (0–7; RESET on GAME_OVER);
- choose one declared action; ACTION6 carries deterministic `(x,y)` probe data;
- call the environment transition and retain its returned observation;
- persist three Franklin UUM-8D wrapper messages per turn (system / user / assistant)
  with S1–S4 phase tags toward a 29-turn closure budget;
- build grammar from observed transitions; C4 requires reproduced productive effects
  (state-conditioned `after_sha` or perfect qualitative productivity);
- accept WIN / GAME_OVER / score only as returned by the environment;
- write per-turn PNGs and an MP4 (PNG sequence → `h264_videotoolbox`) under
  `affine_audit_logs/arc_agi3/<game_id>/<stamp>/`;
- emit `reports/arc_local_*/agi3/` for exam reinjection; cluster misses by grammar class.

`NO_KAGGLE_SUBMIT.lock` remains a hard requirement. Schema-valid parquet ≠ submit.

### Live FoT metrics (local, 2026-07-21)

Source: `reports/arc_agi3_language_game_levels_3/summary.json`.

| Metric | Value | Honest read |
| --- | --- | --- |
| Games played | 3 (`bp35`, `ar25`, `ls20`) × 120 turns | Official offline envs |
| WIN terminals | **0** | Full WIN not yet sealed |
| Levels cleared | **bp35 1/9**; ar25 0; ls20 0 | Documented level-clear progress |
| GAME_OVER events | 2 | Spike-aware RESET continue |
| Mean confidence | **0.888** | bp35 conf 1.0 |
| High-confidence WIN | **0** | Submit still blocked |
| `bp35` grammar | `C4_BOUND` / `level_clear_motion_click_grammar` | Motion replay verified |
| `ar25` / `ls20` | `PARTIAL_GRAMMAR` / `unreproduced_productive_delta` | Still open |
| Captures | MP4 + PNG under `affine_audit_logs/arc_agi3/` | UI trail kept |
| Public probe | **0.12** (ref 54875048) | Process probe only |

**Owned grammar (closes prior `unreproduced_productive_delta` on bp35):**

1. Relative avatar motion — ACTION3/4 horizontal Δ; replay-verified after fresh env.
2. ACTION6 on `qclfkhjnaac` — remove block / open shaft (official click targets; restore `GRAPH_BUILDER`).
3. Land on gem `fjlzdjxhant` → world `win()` → `nkuphphdgrp` → `next_level()`.
4. Spike / action-budget lose → GAME_OVER → RESET continue.

Evidence:
`reports/exam_reinjection/grammar/arc3/unreproduced_productive_delta/evidence.json`.
Reinjection consumes `reports/arc_local_20260721T134200Z/agi3/`.

### FoT note — agi3-trajectory-gap CLOSED (2026-07-21)

Meta miss `arc3:agi3-trajectory-gap` sealed **CLOSED / C4_BOUND_OWNED**. Franklin
center-click / dominant-component REINJECT candidates discarded (failed
`environment_step`). Locked C4 = harness `PlatformerPolicy` /
`level_clear_motion_click_grammar` (bp35 L1 motion replay verified, **1/9**,
WIN=0). Remaining heal under game ids: bp35 L2+ spikes, ar25/ls20
`unreproduced_productive_delta`. Loader skips re-queue of the meta gap while
evidence status is `OWNED_ON_BP35`. No Kaggle submit.

## 9. Format from top scores

Typed artifact after the language-game state change (full detail:
[Kaggle-ARC-Top-Score-Formats](Kaggle-ARC-Top-Score-Formats),
[`docs/KAGGLE_ARC_TOP_SCORE_FORMATS.md`](../docs/KAGGLE_ARC_TOP_SCORE_FORMATS.md)):

| Column | dtype | Commit-mode example |
| --- | --- | --- |
| `row_id` | string | `"1_0"` |
| `game_id` | string | `"1"` |
| `end_of_game` | bool | `True` |
| `score` | int64 | `1` |

Filename: `submission.parquet`. Cited from inversion Stochastic Goose,
pscamillo starter, jeroencottaar simplified (same four columns).

### FoT: our 0.12 vs LB leaders

| Artifact | publicScore | Reads as |
| --- | --- | --- |
| Our probe ref **54875048** | **0.12** | Format accepted + scored ([live record](ARC-Prize-Kaggle-Live)) |
| Goose sample notebook | 0.25 | Same schema; better policy |
| LB #1 YUTO KOJIMA | **1.86** | Puzzle/agent mastery on the same parquet language |

Schema green is serialization integrity. Closing 0.12 → ~1.8 is policy mastery,
not a new column list. Local check:
`python3 scripts/validate_arc_agi3_submission.py …/submission.parquet`.
