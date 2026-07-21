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

Source: offline Arcade + owned policies (`--max-actions 500`) under
`reports/exam_reinjection/grammar/arc3/`.

| Metric | Value | Honest read |
| --- | --- | --- |
| Games played | 3 (`bp35`, `ar25`, `ls20`) | Official offline envs |
| WIN terminals | **3** | All three public games sealed |
| Levels cleared | **bp35 9/9**; **ar25 8/8**; **ls20 7/7** | Full suite WIN |
| `bp35` grammar | `C4_BOUND_OWNED` + WIN | L9 underfloor walk LOCKED |
| `ar25` grammar | `C4_BOUND_OWNED` + WIN | `Ar25Policy` + `AR25_SOLUTIONS` |
| `ls20` grammar | `C4_BOUND_OWNED` + WIN | `Ls20Policy` + `LS20_SOLUTIONS` |
| Captures | `…/bp35/20260721T171435Z/bp35.mp4`, `…/ar25/20260721T171636Z/ar25.mp4`, `…/ls20/20260721T171724Z/ls20.mp4` | Re-verify WIN trails |
| Parquet | `reports/arc_local_20260721T171426Z/submission.parquet` | Schema-valid; scores 9/8/7 |
| Public probe | **0.12** (ref 54875048) | Process probe only; NO Kaggle |
| Submit lock | `configs/NO_KAGGLE_SUBMIT.lock` **PRESENT** | No Kaggle |

**Owned bp35 C4 grammar:**

1. ACTION3/4 horizontal move; inverted gravity falls toward decreasing y when gUP.
2. ACTION6 on `qclfkhjnaac` / `yuuqpmlxorv` / `oonshderxef` / `lrpkmzabbfa`; Y-block `etlsaqqtjvn` force-click spreads into empty neighbors (source cell consumed).
3. Off-viewport pads: ACTION6 via `grid*6 − camera`; harness restores true `x/y` after clamp.
4. Gem `fjlzdjxhant` → `next_level()` / WIN; spike / 128-action L9 budget → GAME_OVER → RESET.
5. L7: soft ladder → `(8,6)` gUP → floor `(8,8)` → col9 gDN safe-drop → gem `(3,25)` (`L7_OPS`).
6. L8: Y-bridge → col8 → soft1 chamber → stand-on-(7,17) clear-(8,17) → `G(5,2)` DN → gem `(9,19)` (`_choose_l8`).
7. L9: defer breach; Y gap/cover/landing; col9 climb; col0; strip shaft grav pads; DN freefall; never R at y38; R at y39+ → gem `(2,40)` (`_choose_l9`) → **WIN**.

Evidence: `bp35_L7_soft1_shaft_col9_safe_drop.json`,
`bp35_L8_ybridge_col8_chamber_gDN_gem.json`,
`bp35_L9_col0_underfloor_y39_gem_walk.json` (LOCKED).
Module: `llm_llvm_bench/arc/agi3_platformer_policy.py`.

### FoT note — agi3 suite CLOSED (2026-07-21)

Meta miss `arc3:agi3-trajectory-gap` sealed **CLOSED / C4_BOUND_OWNED**. Public
games: bp35 **9/9 WIN**, ar25 **8/8 WIN** (`Ar25Policy` / reflection cover),
ls20 **7/7 WIN** (`Ls20Policy` / waypoint shape-color-rotation).

**Independent re-verify** (`reports/arc_local_20260721T171426Z`): one harness pass
`--games bp35 ar25 ls20 --max-actions 500` → `win_terminals=3`,
`levels_by_game={bp35:9,ar25:8,ls20:7}`, `game_over_events=0`,
`submission_blocked=true`, lock intact. Validated
`reports/arc_local_20260721T171426Z/submission.parquet` (3 rows;
`row_id,game_id,end_of_game,score`; scores 9/8/7). Captures:
`…/bp35/20260721T171435Z/bp35.mp4`, `…/ar25/20260721T171636Z/ar25.mp4`,
`…/ls20/20260721T171724Z/ls20.mp4`. No Kaggle submit.

ARC-2 coordination: eval **172/172 COMPLETE** already on `main` (`21b2924`);
agi3 re-verify does not block that land.

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

### Direct CLI submit — BLOCKED (Notebooks-only)

`configs/NO_KAGGLE_SUBMIT.lock` stays on disk. Agents must not remove it.
`bin/kaggle-competitions-submit.sh` is **BLOCKED** for this competition (steward
unlock 2026-07-21T17:39Z → HTTP 400 Notebooks-only + daily quota).

Steward path after UTC quota reset: air-gapped kernel `kaggle/arc-prize-2026/`
→ `ALLOW_KAGGLE_SUBMIT=1 bin/run-arc-prize-kaggle.sh --push-notebook` → Notebook
UI **Submit**. See `docs/ARC_LOCAL_100_SUBMIT_READY.md`.
