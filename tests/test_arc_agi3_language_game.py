"""Unit coverage for the local ARC-AGI-3 language-game harness."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts" / "arc_agi3_language_game.py"


class _ArrayLike:
    """Stand-in for numpy.ndarray with tolist() only."""

    def __init__(self, rows):
        self._rows = rows

    def tolist(self):
        return self._rows


def load_harness():
    spec = importlib.util.spec_from_file_location("arc_agi3_language_game", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_action_ids_accept_only_official_action_grammar():
    harness = load_harness()
    frame = {
        "available_actions": [
            {"id": {"value": 1}},
            {"id": 4},
            {"id": 7},
            {"id": 99},
            {"id": 1},
        ]
    }
    assert harness.action_ids(frame) == [1, 4, 7]


def test_frame_view_reads_numpy_frame_not_model_dump():
    harness = load_harness()
    rows = [[0, 0, 0, 0], [0, 0, 9, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    class FakeRaw:
        game_id = "ar25-test"
        frame = [_ArrayLike(rows)]
        state = SimpleNamespace(name="NOT_FINISHED")
        levels_completed = 0
        win_levels = 8
        guid = "g"
        full_reset = True
        available_actions = [1, 2, 3, 4, 5, 6, 7]

        def model_dump(self):
            # Official FrameDataRaw omits frame from model_dump.
            return {
                "game_id": self.game_id,
                "state": self.state.name,
                "levels_completed": self.levels_completed,
                "available_actions": self.available_actions,
            }

    view = harness.frame_view(FakeRaw())
    assert view["frame"]
    assert view["frame"][0][1][2] == 9
    assert view["frame_summary"]["nonzero"] == 1
    assert view["frame_sha256"]


def test_theory_requires_reproduced_observation_for_c4_boundary():
    harness = load_harness()
    before = {
        "frame": [[[0, 1]]],
        "frame_sha256": "a",
        "state": "PLAYING",
        "levels_completed": 0,
        "available_actions": [1, 2],
    }
    after = {
        **before,
        "frame": [[[0, 2]]],
        "frame_sha256": "b",
        "levels_completed": 1,
    }
    theory = harness.DeterministicTheory()
    theory.update(1, before, after, {})
    # One productive use is not yet a multi-use qualitative lock.
    assert theory.snapshot()["grammar_status"] == "PARTIAL_GRAMMAR"
    theory.update(1, before, after, {})
    snapshot = theory.snapshot()
    assert snapshot["grammar_status"] == "C4_BOUND"
    assert snapshot["conditioned_repro_trials"] == 1
    assert snapshot["conditioned_repro_hits"] == 1


def test_wrapper_turns_binds_prompt_observation_and_legal_action():
    harness = load_harness()
    observation = {
        "state": "PLAYING",
        "frame": [[[1]]],
        "frame_sha256": "abc",
        "frame_summary": {"nonzero": 1},
        "levels_completed": 0,
        "win_levels": 1,
        "guid": "g",
        "full_reset": False,
        "available_actions": [1, 2, 3],
        "game_id": "ar25",
    }
    theory = {
        "grammar_status": "MISSING_GRAMMAR",
        "reproducibility": 0.0,
        "grammar_class": "no_observed_effects",
    }
    turns = harness.wrapper_turns("FRANKLIN", "ar25", theory, observation, 3, {}, 0, "hist")
    assert [turn["role"] for turn in turns] == ["system", "user", "assistant"]
    assert turns[0]["content"] == "FRANKLIN"
    assert '"legal_action_selected":3' in turns[1]["content"]
    assert '"selected_action":3' in turns[2]["content"]
    assert "S1" in turns[1]["content"]
