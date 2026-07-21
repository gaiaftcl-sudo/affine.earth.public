# Kaggle ARC top-score submission formats (local mastery)

Reverse-engineered from official sample data, public top notebooks, and our
scored probe. **No Kaggle submit** while `configs/NO_KAGGLE_SUBMIT.lock` is
present.

Language-game doctrine (state change before serialization):

- [Language Games — ARC-AGI-2](LANGUAGE_GAMES_ARC_AGI_2.md) /
  [wiki](../wiki/Language-Games-ARC-AGI-2.md)
- [Language Games — ARC-AGI-3](LANGUAGE_GAMES_ARC_AGI_3.md) /
  [wiki](../wiki/Language-Games-ARC-AGI-3.md)
- [Exam invariants](LANGUAGE_GAMES_EXAM_INVARIANTS.md) /
  [wiki](../wiki/Language-Games-Exam-Invariants.md)

Format examples below are the **typed answer artifact** after the language-game
state change succeeds. Schema green ≠ puzzle mastery.

---

## FoT contrast: format correctness vs puzzle mastery

| Track | Our probe (FoT) | Top public LB (2026-07-21) | Meaning |
| --- | --- | --- | --- |
| ARC-AGI-3 | ref **54875048** `COMPLETE`, **publicScore 0.12** | **YUTO KOJIMA 1.86**, Tecnod8.AI 1.61, DhanaLakshmiMalla 1.60 | Our parquet was **accepted and scored**. Gap to ~1.5–1.86 is **agent/policy mastery**, not missing columns. |
| ARC-AGI-2 | Affine baseline **publicScore 0.00** (schema-valid) | **nvbanana 65.83**, rabbithole 38.61, Junhua Yang 36.39 | JSON contract is known; score gap is **transformation mastery**. |

Public notebook sanity check on the same AGI-3 schema: inversion
[Stochastic Goose](https://www.kaggle.com/code/inversion/arc3-sample-submission-stochastic-goose)
shows **publicScore 0.25** — same four-column parquet contract, higher policy
than our 0.12 starter probe, still far below LB leaders.

Screenshots: `wiki/assets/kaggle-top-agi2-leaderboard.png`,
`wiki/assets/kaggle-top-agi3-leaderboard.png`,
`wiki/assets/kaggle-top-agi3-notebook-goose.png`.

---

## ARC-AGI-2 — `submission.json`

Competition: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2>

### Contract

| Rule | Exact requirement |
| --- | --- |
| Filename | `submission.json` only |
| Root | JSON object keyed by **task_id** strings |
| Per task | Non-empty **array**; length = number of `test` inputs |
| Per test item | Object with **exactly** keys `attempt_1`, `attempt_2` |
| Grid | Non-empty rectangular `List[List[int]]`, colors **0..9**, dims ≤ 30 |
| Win | Exact match of either attempt to the hidden grid |

### Example (official sample shape; first task)

```json
{
  "00576224": [
    {
      "attempt_1": [[0, 0], [0, 0]],
      "attempt_2": [[0, 0], [0, 0]]
    }
  ]
}
```

Official `sample_submission.json`: **240** tasks; **17** multi-test tasks.
Synthetic fixture: `fixtures/kaggle_arc_format/submission.json`.

### Cited producers

| Source | Role |
| --- | --- |
| Official `sample_submission.json` | Canonical empty-grid scaffold |
| [NVARC baseline T4x2](https://www.kaggle.com/code/nihilisticneuralnet/baseline-nvarc-arc-25-winning-solution-for-t4x2) | `get_submission` builds `{task: [{attempt_1, attempt_2}, ...]}`; `validate_submission` scores either attempt |
| [MCP AGI-2 starter](https://www.kaggle.com/code/ibrahimqasimi/mcp-arc-prize-agi-2-2026-starter) | Writes `/kaggle/working/submission.json` with the same keys |

NVARC selection rule (excerpt): default placeholder `[[0]]` per attempt, then
fill `attempt_{i+1}` from decoder guesses — confirms **two named attempts**,
not an open-ended list.

### Local producer diff

| Check | Local (`scripts/build_arc_prize_submission.py`, `kaggle/arc-prize-2026-agi-2/`) | Top/sample |
| --- | --- | --- |
| Filename | `submission.json` | match |
| Keys | `attempt_1`, `attempt_2` | match |
| Colors | ints 0..9 | match |
| Task coverage | all challenge test IDs | match |
| Second attempt | often identity copy until second strategy wired | allowed; scoring takes either |

Local validator:
`python3 scripts/validate_arc_prize_submission.py PATH/submission.json [--challenges …]`

---

## ARC-AGI-3 — `submission.parquet` (agent track)

Competition: <https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3>

Language game: observation → legal action → environment transition →
framework/gateway emits parquet. See
[Language-Games-ARC-AGI-3](../wiki/Language-Games-ARC-AGI-3.md).

### Contract (commit-mode + scored-rerun)

| Rule | Exact requirement |
| --- | --- |
| Filename | `submission.parquet` only |
| Columns (order) | `row_id`, `game_id`, `end_of_game`, `score` |
| dtypes | string/object, string/object, **bool**, **integer** |
| Write | `DataFrame.to_parquet(..., index=False)` |
| Commit mode | When `KAGGLE_IS_COMPETITION_RERUN` unset, notebooks emit a **dummy** one-row parquet so Save Version succeeds |
| Scored rerun | Gateway / starter runs the agent; real rows replace the dummy |

### Example (universal commit-mode row from top notebooks)

```python
import pandas as pd
submission = pd.DataFrame(
    data=[["1_0", "1", True, 1]],
    columns=["row_id", "game_id", "end_of_game", "score"],
)
submission.to_parquet("/kaggle/working/submission.parquet", index=False)
```

Observed dtypes on our kernel output
(`evidence/arc-prize-2026/kernel-output/submission.parquet`):

| column | dtype | sample |
| --- | --- | --- |
| `row_id` | object/str | `"1_0"` |
| `game_id` | object/str | `"1"` |
| `end_of_game` | bool | `True` |
| `score` | int64 | `1` |

Synthetic fixture: `fixtures/kaggle_arc_format/submission.parquet`.

### Cited producers

| Source | Role |
| --- | --- |
| [Stochastic Goose](https://www.kaggle.com/code/inversion/arc3-sample-submission-stochastic-goose) | Same dummy parquet; scored **0.25** |
| [Random Agent sample](https://www.kaggle.com/code/inversion/arc3-sample-submission-random-agent) | Identical column list |
| [pscamillo starter](https://www.kaggle.com/code/pscamillo/arc-prize-2026-arc-agi-3-starter) | Rerun: `main.py --agent …`; commit: dummy parquet |
| [jeroencottaar simplified](https://www.kaggle.com/code/jeroencottaar/simplified-submission-approach) | Arcade play + same dummy columns |
| Our probe ref **54875048** | Same schema; **publicScore 0.12** |

### Local producer diff

| Check | Local evidence / starter path | Top notebooks |
| --- | --- | --- |
| Filename | `submission.parquet` | match |
| Columns | `row_id, game_id, end_of_game, score` | match |
| Dummy commit row | `['1_0','1',True,1]` | match |
| Real score path | gateway rerun / agent policy | mastery axis |

Local validator:
`python3 scripts/validate_arc_agi3_submission.py PATH/submission.parquet`

---

## Leaderboard snapshot (CLI, 2026-07-21)

**AGI-2 top:** nvbanana 65.83 · rabbithole 38.61 · Junhua Yang 36.39 · Bong 34.44  
**AGI-3 top:** YUTO KOJIMA 1.86 · Tecnod8.AI 1.61 · DhanaLakshmiMalla 1.60 · ippeiogawa 1.58  

Raw pulls: `evidence/arc-format-study/agi-2-leaderboard.txt`,
`evidence/arc-format-study/agi-3-leaderboard.txt`.

---

## Validators and lock

```bash
# NO submits
test -f configs/NO_KAGGLE_SUBMIT.lock

python3 scripts/validate_arc_prize_submission.py \
  fixtures/kaggle_arc_format/submission.json
python3 scripts/validate_arc_agi3_submission.py \
  fixtures/kaggle_arc_format/submission.parquet
```

Auth for any status pull: `export KAGGLE_API_TOKEN=…` only — no Keychain.
