#!/usr/bin/env python3
"""Run locally installed ARC-AGI-3 environments as recorded language games.

This is a local-only harness. It does not import Kaggle tooling, invoke a
competition endpoint, or remove ``configs/NO_KAGGLE_SUBMIT.lock``. Each
episode is driven through the official ``arc_agi`` environment, with every
accepted action and returned observation recorded before the next action is
selected.

Root cause previously sealing MISSING_GRAMMAR with empty frames: pydantic
``model_dump()`` on ``FrameDataRaw`` omits the numpy ``frame`` field. This
harness reads ``frame`` via attribute access and ``tolist()`` only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "configs" / "NO_KAGGLE_SUBMIT.lock"
DEFAULT_ENVIRONMENTS = ROOT / "data" / "arc-prize-2026" / "environment_files"
DEFAULT_CAPTURE_DIR = ROOT / "affine_audit_logs" / "arc_agi3"
EXPECTED_COLUMNS = ["row_id", "game_id", "end_of_game", "score"]
CLOSURE_TURN_TARGET = 29


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_franklin_prompt() -> str:
    sys.path.insert(0, str(ROOT))
    from llm_llvm_bench.arc.franklin_uum8d_system_prompt import (  # noqa: PLC0415
        franklin_uum8d_game_comprehension_system_prompt,
    )

    return franklin_uum8d_game_comprehension_system_prompt()


def public_game_ids(environment_root: Path) -> list[str]:
    return sorted(
        path.name
        for path in environment_root.iterdir()
        if path.is_dir() and any(path.glob("*/metadata.json"))
    )


def layers_to_lists(frame_layers: Any) -> list[list[list[int]]]:
    """Convert official FrameDataRaw.frame layers to plain int grids."""
    if frame_layers is None:
        return []
    layers: list[list[list[int]]] = []
    for layer in frame_layers:
        if hasattr(layer, "tolist"):
            layer = layer.tolist()
        if not isinstance(layer, list):
            continue
        layers.append([[int(cell) for cell in row] for row in layer])
    return layers


def frame_summary(layers: list[list[list[int]]]) -> dict[str, Any]:
    if not layers:
        return {"layer_count": 0, "shape": [0, 0], "nonzero": 0, "palette": []}
    height = len(layers[0])
    width = len(layers[0][0]) if height else 0
    palette: set[int] = set()
    nonzero = 0
    for layer in layers:
        for row in layer:
            for cell in row:
                palette.add(int(cell))
                nonzero += int(cell != 0)
    return {
        "layer_count": len(layers),
        "shape": [height, width],
        "nonzero": nonzero,
        "palette": sorted(palette),
    }


def frame_view(raw: Any) -> dict[str, Any]:
    """Extract observation state. Never trust model_dump() for frame grids."""
    if raw is None:
        raise RuntimeError("Environment returned empty observation.")

    # Attribute path is authoritative — FrameDataRaw.model_dump() omits frame.
    layers = layers_to_lists(getattr(raw, "frame", None))
    state_obj = getattr(raw, "state", "")
    if hasattr(state_obj, "name"):
        state = str(state_obj.name)
    else:
        state = str(state_obj)

    available = getattr(raw, "available_actions", None)
    if available is None and hasattr(raw, "model_dump"):
        available = raw.model_dump().get("available_actions", [])

    view = {
        "game_id": str(getattr(raw, "game_id", "") or ""),
        "frame": layers,
        "frame_sha256": digest(layers),
        "frame_summary": frame_summary(layers),
        "state": state,
        "levels_completed": int(
            getattr(raw, "levels_completed", getattr(raw, "score", 0)) or 0
        ),
        "win_levels": int(getattr(raw, "win_levels", getattr(raw, "win_score", 0)) or 0),
        "guid": str(getattr(raw, "guid", "") or ""),
        "full_reset": bool(getattr(raw, "full_reset", False)),
        "available_actions": list(available or []),
    }
    return view


def compact_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Log-sized observation: sha + summary, never the full 64×64 grid."""
    return {
        "game_id": observation.get("game_id", ""),
        "frame_sha256": observation.get("frame_sha256", ""),
        "frame_summary": observation.get("frame_summary", {}),
        "state": observation.get("state", ""),
        "levels_completed": observation.get("levels_completed", 0),
        "win_levels": observation.get("win_levels", 0),
        "guid": observation.get("guid", ""),
        "full_reset": observation.get("full_reset", False),
        "available_actions": observation.get("available_actions", []),
    }


def action_ids(frame: dict[str, Any]) -> list[int]:
    found: list[int] = []
    for item in frame.get("available_actions", []):
        if isinstance(item, int):
            candidate = item
        elif isinstance(item, dict):
            candidate = item.get("id", item.get("action_id"))
            if isinstance(candidate, dict):
                candidate = candidate.get("value", candidate.get("id"))
        else:
            candidate = getattr(item, "id", item)
            candidate = getattr(candidate, "value", candidate)
        if isinstance(candidate, int) and 0 <= candidate <= 7 and candidate not in found:
            found.append(candidate)
    return found


def grid_delta(before: Any, after: Any) -> dict[str, int]:
    before_layers = before if isinstance(before, list) else []
    after_layers = after if isinstance(after, list) else []
    changed = cells = 0
    first_change: Optional[Tuple[int, int, int]] = None
    for layer_index in range(min(len(before_layers), len(after_layers))):
        left, right = before_layers[layer_index], after_layers[layer_index]
        if not isinstance(left, list) or not isinstance(right, list):
            continue
        for row_index in range(min(len(left), len(right))):
            left_row, right_row = left[row_index], right[row_index]
            if not isinstance(left_row, list) or not isinstance(right_row, list):
                continue
            for column_index in range(min(len(left_row), len(right_row))):
                cells += 1
                if left_row[column_index] != right_row[column_index]:
                    changed += 1
                    if first_change is None:
                        first_change = (layer_index, row_index, column_index)
    payload = {"compared_cells": cells, "changed_cells": changed}
    if first_change is not None:
        payload["first_change_lrc"] = list(first_change)
    return payload


def interesting_points(layers: list[list[list[int]]], limit: int = 16) -> list[Tuple[int, int]]:
    """Deterministic ACTION6 click candidates from non-border / rare colors."""
    if not layers:
        return [(32, 32)]
    grid = layers[-1]
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height == 0 or width == 0:
        return [(32, 32)]
    counts: Counter[int] = Counter(cell for row in grid for cell in row)
    rare = {color for color, _ in counts.most_common()[:-1]} if len(counts) > 1 else set(counts)
    # Prefer uncommon colors; fall back to center cross.
    points: list[Tuple[int, int]] = []
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell in rare and cell != counts.most_common(1)[0][0]:
                points.append((x, y))
            if len(points) >= limit:
                return points
    if not points:
        points = [
            (width // 2, height // 2),
            (width // 4, height // 4),
            (3 * width // 4, 3 * height // 4),
            (width // 2, height // 4),
            (width // 4, height // 2),
        ]
    return points[:limit]


@dataclass
class Turn:
    turn_index: int
    action_id: int
    action_data: dict[str, Any]
    observation_before_sha256: str
    observation_after_sha256: str
    observation_before: dict[str, Any]
    observation_after: dict[str, Any]
    transition: dict[str, int]
    theory_before: dict[str, Any]
    wrapper_turns: list[dict[str, str]]
    s_phase: str
    png_path: str = ""
    at: str = field(default_factory=utc_now)


class DeterministicTheory:
    """Replayable grammar built solely from observed action effects.

    Exact cell-count signatures shift as the agent moves, so C4 uses
    state-conditioned reproduction: same ``(frame_sha, action[, data])``
    must yield the same ``after_sha`` when re-observed. Qualitative
    productivity (cells change / levels rise) is tracked separately.
    """

    def __init__(self) -> None:
        self.effects: dict[int, Counter[str]] = defaultdict(Counter)
        self.action_uses: Counter[int] = Counter()
        self.visited: set[tuple[str, int]] = set()
        self.click_index = 0
        self.productive_actions: Counter[int] = Counter()
        self.level_gain_actions: Counter[int] = Counter()
        # (before_sha, action_id, data_key) -> Counter[after_sha]
        self.conditioned: dict[tuple[str, int, str], Counter[str]] = defaultdict(Counter)
        self.conditioned_repro_hits = 0
        self.conditioned_repro_trials = 0

    def update(
        self,
        action_id: int,
        before: dict[str, Any],
        after: dict[str, Any],
        action_data: Optional[dict[str, Any]] = None,
    ) -> None:
        transition = grid_delta(before["frame"], after["frame"])
        signature = canonical(
            {
                "changed_cells": transition["changed_cells"],
                "levels_delta": after["levels_completed"] - before["levels_completed"],
                "state": after["state"],
                "frame_sha_changed": before["frame_sha256"] != after["frame_sha256"],
            }
        )
        self.effects[action_id][signature] += 1
        self.action_uses[action_id] += 1
        if transition["changed_cells"] > 0 or after["levels_completed"] > before["levels_completed"]:
            self.productive_actions[action_id] += 1
        if after["levels_completed"] > before["levels_completed"]:
            self.level_gain_actions[action_id] += 1
        data_key = canonical(action_data or {})
        cond_key = (before["frame_sha256"], action_id, data_key)
        after_sha = after["frame_sha256"]
        prior = self.conditioned[cond_key]
        if sum(prior.values()) > 0:
            self.conditioned_repro_trials += 1
            if after_sha in prior:
                self.conditioned_repro_hits += 1
        prior[after_sha] += 1
        self.visited.add((before["frame_sha256"], action_id))

    def snapshot(self) -> dict[str, Any]:
        action_rules: dict[str, Any] = {}
        for action_id in sorted(aid for aid, effects in self.effects.items() if effects):
            total = sum(self.effects[action_id].values())
            signature, repeat_count = self.effects[action_id].most_common(1)[0]
            action_rules[str(action_id)] = {
                "observed_uses": total,
                "dominant_effect": json.loads(signature),
                "reproducibility": repeat_count / total,
                "productive_uses": int(self.productive_actions[action_id]),
                "level_gain_uses": int(self.level_gain_actions[action_id]),
            }
        # Qualitative productivity reliability across actions with ≥2 uses.
        qualitative = []
        for entry in action_rules.values():
            if entry["observed_uses"] < 2:
                continue
            productive_rate = entry["productive_uses"] / entry["observed_uses"]
            qualitative.append(productive_rate)
        conditioned_rate = (
            self.conditioned_repro_hits / self.conditioned_repro_trials
            if self.conditioned_repro_trials
            else 0.0
        )
        productive = sum(1 for entry in action_rules.values() if entry["productive_uses"] > 0)
        grammar = "MISSING_GRAMMAR"
        # C4: productive grammar + either perfect conditioned replay or
        # perfect qualitative productivity on every multi-use action.
        if productive > 0 and (
            (self.conditioned_repro_trials > 0 and conditioned_rate == 1.0)
            or (qualitative and min(qualitative) == 1.0)
        ):
            grammar = "C4_BOUND"
        elif productive > 0:
            grammar = "PARTIAL_GRAMMAR"
        repro = conditioned_rate if self.conditioned_repro_trials else (
            sum(qualitative) / len(qualitative) if qualitative else 0.0
        )
        return {
            "action_rules": action_rules,
            "reproducibility": repro,
            "conditioned_repro_hits": self.conditioned_repro_hits,
            "conditioned_repro_trials": self.conditioned_repro_trials,
            "productive_action_count": productive,
            "grammar_status": grammar,
            "grammar_class": self.grammar_class(action_rules, grammar),
        }

    def grammar_class(self, action_rules: dict[str, Any], grammar: str) -> str:
        if grammar == "C4_BOUND":
            return "reproduced_productive_transitions"
        if not action_rules:
            return "no_observed_effects"
        empty_frames = all(
            (entry.get("dominant_effect") or {}).get("changed_cells", 0) == 0
            and not (entry.get("dominant_effect") or {}).get("frame_sha_changed", False)
            for entry in action_rules.values()
        )
        if empty_frames:
            return "empty_or_static_frame_observation"
        if any(entry.get("level_gain_uses", 0) > 0 for entry in action_rules.values()):
            return "level_gain_seen_unreproduced"
        if grammar == "PARTIAL_GRAMMAR":
            return "unreproduced_productive_delta"
        return "unreproduced_static_delta"

    def choose(
        self, observation: dict[str, Any], legal: list[int]
    ) -> Tuple[int, dict[str, Any]]:
        if not legal:
            raise RuntimeError("Environment exposed no legal actions.")
        state = str(observation.get("state", "")).upper()
        # Official GAME_OVER → RESET when present, else lowest legal action.
        if state.endswith("GAME_OVER") or state == "GAME_OVER":
            if 0 in legal:
                return 0, {}
            # Some frames omit RESET from available_actions; still attempt it.
            return 0, {}

        observation_key = observation["frame_sha256"]
        untried = [action for action in legal if (observation_key, action) not in self.visited]
        if untried:
            action_id = min(untried)
        elif self.level_gain_actions:
            action_id = max(
                legal,
                key=lambda action: (
                    self.level_gain_actions[action],
                    self.productive_actions[action],
                    -self.action_uses[action],
                ),
            )
        elif self.productive_actions:
            action_id = max(
                legal,
                key=lambda action: (
                    self.productive_actions[action],
                    -self.action_uses[action],
                    -action,
                ),
            )
        else:
            action_id = min(legal, key=lambda action: (self.action_uses[action], action))

        data: dict[str, Any] = {}
        if action_id == 6:
            points = interesting_points(observation.get("frame") or [])
            x, y = points[self.click_index % len(points)]
            self.click_index += 1
            data = {"x": int(x), "y": int(y)}
        return action_id, data


def is_terminal(frame: dict[str, Any], *, win_only: bool = False) -> bool:
    state = str(frame.get("state", "")).upper()
    if win_only:
        return state.endswith("WIN") or state == "WIN"
    return state.endswith("WIN") or state.endswith("GAME_OVER") or state in {"WIN", "GAME_OVER"}


def is_game_over(frame: dict[str, Any]) -> bool:
    state = str(frame.get("state", "")).upper()
    return state.endswith("GAME_OVER") or state == "GAME_OVER"


def s_phase_for_turn(turn_index: int, theory: dict[str, Any], terminal: bool) -> str:
    if terminal and theory.get("grammar_status") == "C4_BOUND":
        return "C4"
    if turn_index < 4:
        return f"S{turn_index + 1}"
    if theory.get("grammar_status") == "C4_BOUND":
        return "C4"
    # Map mid-episode progress toward Aristotelian 29-turn closure.
    return f"S{(turn_index % 4) + 1}->C4"


def wrapper_turns(
    prompt: str,
    game_id: str,
    theory: dict[str, Any],
    observation: dict[str, Any],
    action_id: int,
    action_data: dict[str, Any],
    turn_index: int,
    history_digest: str,
) -> list[dict[str, str]]:
    phase = s_phase_for_turn(turn_index, theory, False)
    user = {
        "game_id": game_id,
        "turn_index": turn_index,
        "closure_turn_target": CLOSURE_TURN_TARGET,
        "s_phase": phase,
        "history_digest": history_digest,
        "observation": compact_observation(observation),
        "theory": theory,
        "legal_action_selected": action_id,
        "action_data": action_data,
        "instruction": (
            "Phase I interactive probe (actions 1-7). Observe the grid, retain "
            "history, deduce grammar. Do not treat this as NP-hard search. "
            "S1-S4 bind observation/action/history/terminal predicate; lock C4 "
            "only when the rule is reproduced."
        ),
    }
    assistant = {
        "game_id": game_id,
        "turn_index": turn_index,
        "s_phase": phase,
        "selected_action": action_id,
        "action_data": action_data,
        "theory_status": theory["grammar_status"],
        "grammar_class": theory.get("grammar_class"),
        "confidence": theory["reproducibility"],
    }
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": canonical(user)},
        {"role": "assistant", "content": canonical(assistant)},
    ]


def make_action(
    game_action: Any, action_id: int, data: dict[str, Any], reasoning: dict[str, Any]
) -> Any:
    action = game_action.from_id(action_id)
    if data and hasattr(action, "set_data"):
        action.set_data(data)
    if hasattr(action, "reasoning"):
        action.reasoning = reasoning
    return action


def step(environment: Any, action: Any, reasoning: dict[str, Any]) -> Any:
    data = action.action_data.model_dump() if hasattr(action, "action_data") else {}
    return environment.step(action, data=data, reasoning=reasoning)


def save_frame_png(layers: list[list[list[int]]], path: Path) -> str:
    """Write an actual PNG of the observed grid. Never invent pixels."""
    if not layers:
        return ""
    try:
        from PIL import Image
    except ImportError:
        return ""
    # Official 16-color palette (matches starter ReasoningAgent).
    colors = {
        0: (255, 255, 255),
        1: (204, 204, 204),
        2: (153, 153, 153),
        3: (102, 102, 102),
        4: (51, 51, 51),
        5: (0, 0, 0),
        6: (229, 58, 163),
        7: (255, 123, 204),
        8: (249, 60, 49),
        9: (30, 147, 255),
        10: (136, 216, 241),
        11: (255, 220, 0),
        12: (255, 133, 27),
        13: (146, 18, 49),
        14: (79, 204, 48),
        15: (163, 86, 214),
    }
    grid = layers[-1]
    height = len(grid)
    width = len(grid[0]) if height else 0
    if height == 0 or width == 0:
        return ""
    scale = 4
    image = Image.new("RGB", (width * scale, height * scale))
    pixels = image.load()
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            rgb = colors.get(int(cell), (136, 136, 136))
            for dy in range(scale):
                for dx in range(scale):
                    pixels[x * scale + dx, y * scale + dy] = rgb
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return str(path.relative_to(ROOT)) if path.is_file() else ""


def encode_png_sequence_to_mp4(png_paths: List[Path], mp4_path: Path) -> dict[str, Any]:
    """Build MP4 from written PNGs — no avfoundation, no SIGINT death."""
    if not png_paths or shutil.which("ffmpeg") is None:
        return {"ok": False, "path": "", "detail": "no_pngs_or_ffmpeg"}
    list_file = mp4_path.with_suffix(".ffconcat.txt")
    lines = ["ffconcat version 1.0"]
    for png in png_paths:
        lines.append(f"file {png.resolve()}")
        lines.append("duration 0.25")
    # Repeat last frame for muxers that need a trailing file entry.
    lines.append(f"file {png_paths[-1].resolve()}")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vsync",
        "vfr",
        "-c:v",
        "h264_videotoolbox",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(mp4_path),
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    ok = result.returncode == 0 and mp4_path.is_file() and mp4_path.stat().st_size > 0
    return {
        "ok": ok,
        "path": str(mp4_path.relative_to(ROOT)) if ok else "",
        "returncode": result.returncode,
        "stderr": (result.stderr or "")[-500:],
        "command": command,
    }


def run_episode(
    arcade: Any,
    game_action: Any,
    game_id: str,
    prompt: str,
    capture_dir: Path,
    max_actions: int,
) -> dict[str, Any]:
    environment = arcade.make(game_id)
    current = frame_view(environment.observation_space)
    if not current["frame"]:
        raise RuntimeError(
            f"{game_id}: empty frame after environment reset — observation API broken."
        )
    theory = DeterministicTheory()
    turns: list[Turn] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    episode_capture = capture_dir / game_id / stamp
    episode_capture.mkdir(parents=True, exist_ok=True)
    png_paths: list[Path] = []
    history_bits: list[str] = []

    # Initial observation PNG (turn 000).
    initial_png = episode_capture / "frame_0000.png"
    initial_rel = save_frame_png(current["frame"], initial_png)
    if initial_rel:
        png_paths.append(initial_png)

    win_seen = False
    game_over_count = 0
    for turn_index in range(max_actions):
        if is_terminal(current, win_only=True):
            win_seen = True
            break
        legal = action_ids(current)
        # GAME_OVER: attempt RESET even if omitted from available_actions.
        if is_game_over(current):
            game_over_count += 1
            legal = sorted(set(legal) | {0})
        if not legal:
            raise RuntimeError(f"{game_id}: no official legal actions in observation.")
        theory_before = theory.snapshot()
        action_id, action_data = theory.choose(current, legal)
        history_digest = digest(history_bits)
        messages = wrapper_turns(
            prompt,
            game_id,
            theory_before,
            current,
            action_id,
            action_data,
            turn_index,
            history_digest,
        )
        action = make_action(
            game_action,
            action_id,
            action_data,
            {
                "language_game": "ARC-AGI-3",
                "theory": theory_before,
                "turn": turn_index,
                "s_phase": s_phase_for_turn(turn_index, theory_before, False),
            },
        )
        raw_after = step(environment, action, {"wrapper_turns": messages})
        if raw_after is None:
            raise RuntimeError(f"{game_id}: environment.step returned None for action {action_id}.")
        after = frame_view(raw_after)
        if not after["frame"]:
            raise RuntimeError(f"{game_id}: empty frame after action {action_id}.")
        transition = grid_delta(current["frame"], after["frame"])
        png_path = episode_capture / f"frame_{turn_index + 1:04d}.png"
        png_rel = save_frame_png(after["frame"], png_path)
        if png_rel:
            png_paths.append(png_path)
        phase = s_phase_for_turn(
            turn_index, theory_before, is_terminal(after, win_only=True)
        )
        turns.append(
            Turn(
                turn_index=turn_index,
                action_id=action_id,
                action_data=action_data,
                observation_before_sha256=current["frame_sha256"],
                observation_after_sha256=after["frame_sha256"],
                observation_before=compact_observation(current),
                observation_after=compact_observation(after),
                transition=transition,
                theory_before=theory_before,
                wrapper_turns=messages,
                s_phase=phase,
                png_path=png_rel,
            )
        )
        history_bits.append(
            canonical(
                {
                    "t": turn_index,
                    "a": action_id,
                    "d": action_data,
                    "before": current["frame_sha256"],
                    "after": after["frame_sha256"],
                    "delta": transition,
                }
            )
        )
        theory.update(action_id, current, after, action_data)
        current = after
        if is_terminal(current, win_only=True):
            win_seen = True
            break

    mp4 = encode_png_sequence_to_mp4(png_paths, episode_capture / f"{game_id}.mp4")
    final_theory = theory.snapshot()
    win_terminal = win_seen or is_terminal(current, win_only=True)
    any_terminal = win_terminal or is_game_over(current) or game_over_count > 0
    confidence = float(final_theory["reproducibility"])
    # Submit gate: WIN + C4 + reproduced productive grammar only.
    submit_confidence = (
        1.0
        if win_terminal and final_theory["grammar_status"] == "C4_BOUND" and confidence == 1.0
        else confidence
    )
    return {
        "game_id": game_id,
        "finished_at": utc_now(),
        "turns": [asdict(turn) for turn in turns],
        "turn_count": len(turns),
        "closure_turn_target": CLOSURE_TURN_TARGET,
        "terminal_observation": compact_observation(current),
        "terminal_reported_by_environment": any_terminal,
        "win_terminal": win_terminal,
        "game_over_count": game_over_count,
        "theory": final_theory,
        "confidence": submit_confidence,
        "score": int(current["levels_completed"]),
        "capture": {
            "dir": str(episode_capture.relative_to(ROOT)),
            "png_count": len(png_paths),
            "initial_png": initial_rel,
            "mp4": mp4,
        },
        "diagnosis": {
            "empty_frame_bug_fixed": True,
            "grammar_class": final_theory.get("grammar_class"),
            "productive_action_count": final_theory.get("productive_action_count"),
        },
    }


def write_parquet(rows: list[dict[str, Any]], destination: Path) -> None:
    try:
        import pandas as pd
    except ImportError:
        pd = None
    if pd is not None:
        frame = pd.DataFrame(rows, columns=EXPECTED_COLUMNS)
        frame = frame.astype(
            {"row_id": "string", "game_id": "string", "end_of_game": "bool", "score": "int64"}
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(destination, index=False)
        return

    converter = os.environ.get("ARC_AGI3_PARQUET_PYTHON", "python3")
    converter_env = dict(os.environ)
    virtual_env = converter_env.get("VIRTUAL_ENV")
    if "ARC_AGI3_PARQUET_PYTHON" not in os.environ and virtual_env:
        virtual_bin = str(Path(virtual_env) / "bin")
        converter_env["PATH"] = os.pathsep.join(
            entry
            for entry in converter_env.get("PATH", "").split(os.pathsep)
            if entry != virtual_bin
        )
    writer = (
        "import json,sys,pandas as pd; "
        "rows=json.load(sys.stdin); "
        "frame=pd.DataFrame(rows,columns=['row_id','game_id','end_of_game','score']); "
        "frame=frame.astype({'row_id':'string','game_id':'string','end_of_game':'bool','score':'int64'}); "
        "frame.to_parquet(sys.argv[1],index=False)"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [converter, "-c", writer, str(destination)],
        input=json.dumps(rows),
        text=True,
        capture_output=True,
        check=False,
        env=converter_env,
    )
    if result.returncode:
        raise RuntimeError(
            "Unable to write submission.parquet using the local parquet interpreter: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )


def emit_arc_local_report(report_dir: Path, episodes: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    """Write reinjection-consumable AGI-3 slice under reports/arc_local_*/agi3/."""
    agi3 = report_dir / "agi3"
    agi3.mkdir(parents=True, exist_ok=True)
    traces = agi3 / "episode-language-games.jsonl"
    with traces.open("w", encoding="utf-8") as stream:
        for episode in episodes:
            terminal = bool(episode.get("win_terminal"))
            grammar = episode["theory"]["grammar_status"]
            traj_ok = episode["turn_count"] > 0 and all(
                turn["transition"]["compared_cells"] > 0 for turn in episode["turns"][:1]
            )
            status = "PASS" if terminal and grammar == "C4_BOUND" else "FAIL"
            row = {
                "game_id": episode["game_id"],
                "status": status,
                "protocol": {
                    "bind": {
                        "episode_or_game_id": episode["game_id"],
                        "version": episode["terminal_observation"].get("game_id", ""),
                    },
                    "parse": {
                        "turn_count": episode["turn_count"],
                        "frame_summary": episode["terminal_observation"].get("frame_summary"),
                    },
                    "constrain": {
                        "action_language": "ACTION1..ACTION7",
                        "grammar_status": grammar,
                        "grammar_class": episode["theory"].get("grammar_class"),
                    },
                    "state_change": {
                        "transition": "a_t ∈ A(s_t); s_(t+1)=E.step(s_t,a_t)",
                        "trajectory_available": traj_ok,
                        "turn_count": episode["turn_count"],
                        "closure_turn_target": CLOSURE_TURN_TARGET,
                    },
                    "validate_locally": {
                        "terminal_reported_by_environment": terminal,
                        "confidence": episode["confidence"],
                        "capture_png_count": episode["capture"].get("png_count", 0),
                        "capture_mp4": episode["capture"].get("mp4", {}).get("path", ""),
                    },
                    "drift": {
                        "drift_kind": (
                            "none"
                            if status == "PASS"
                            else "understanding drift"
                        ),
                        "drift_note": (
                            f"grammar={grammar}; class={episode['theory'].get('grammar_class')}; "
                            f"terminals={int(terminal)}; confidence={episode['confidence']}"
                        ),
                    },
                },
            }
            stream.write(json.dumps(row, sort_keys=True) + "\n")

    local_summary = {
        "track": "ARC-AGI-3",
        "status": "GREEN" if summary["environment_terminals"] > 0 else "RED",
        "trajectory_replay": (
            f"RAN:{summary['games']} games, "
            f"terminals={summary['environment_terminals']}, "
            f"mean_confidence={summary['mean_confidence']:.4f}, "
            f"miss_clusters={summary['miss_clusters']}"
        ),
        "environment_games": summary["games"],
        "public_probe": summary["public_probe"],
        "leaderboard_contrast": {
            "our_publicScore": 0.12,
            "top_public_lb_approx": 1.86,
            "meaning": "format≠mastery — local trajectory still incomplete for submit",
        },
        "submission_blocked": True,
        "language_game_summary": summary,
        "task_trace": str(traces.relative_to(ROOT)),
    }
    write_json(agi3 / "summary.json", local_summary)
    write_json(report_dir / "summary.json", {
        "generated_at": utc_now(),
        "mode": "LOCAL_ONLY",
        "arc_agi_3": local_summary,
        "submission_blocked": True,
        "no_kaggle_submit_lock": True,
    })


def run(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", nargs="+", help="Official game IDs; default: first N local games.")
    parser.add_argument("--max-games", type=int, default=3, help="Cap when --games omitted.")
    parser.add_argument("--max-actions", type=int, default=29)
    parser.add_argument("--environment-root", type=Path, default=DEFAULT_ENVIRONMENTS)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--capture-dir", type=Path, default=DEFAULT_CAPTURE_DIR)
    parser.add_argument(
        "--emit-arc-local-report",
        type=Path,
        help="Also write reports/arc_local_*/agi3 for exam reinjection.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not LOCK_PATH.is_file():
        raise RuntimeError("configs/NO_KAGGLE_SUBMIT.lock is required.")
    if args.max_actions < 1:
        raise ValueError("--max-actions must be positive.")
    environment_root = args.environment_root.resolve()
    available = public_game_ids(environment_root)
    game_ids = args.games or available[: max(1, args.max_games)]
    missing = sorted(set(game_ids) - set(available))
    if missing:
        raise ValueError(f"Games absent from local official environment files: {missing}")

    try:
        from arc_agi import Arcade, OperationMode  # noqa: PLC0415
        from arcengine import GameAction  # noqa: PLC0415
    except ImportError as exc:
        raise RuntimeError(
            "ARC-AGI-3 runtime is unavailable. Install dependencies in "
            "data/arc-prize-2026/ARC-AGI-3-Agents before running."
        ) from exc

    prompt = load_franklin_prompt()
    arcade = Arcade(
        operation_mode=OperationMode.OFFLINE,
        environments_dir=str(environment_root),
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    episodes = [
        run_episode(
            arcade,
            GameAction,
            game_id,
            prompt,
            args.capture_dir.resolve(),
            args.max_actions,
        )
        for game_id in game_ids
    ]
    rows = [
        {
            "row_id": f"{index}_0",
            "game_id": episode["game_id"],
            "end_of_game": bool(episode["terminal_reported_by_environment"]),
            "score": int(episode["score"]),
        }
        for index, episode in enumerate(episodes)
    ]
    parquet = output_dir / "submission.parquet"
    write_parquet(rows, parquet)
    misses = [
        episode
        for episode in episodes
        if not episode.get("win_terminal") or episode["confidence"] < 1.0
    ]
    clusters = Counter(
        episode["theory"].get("grammar_class")
        or episode["theory"]["grammar_status"]
        for episode in misses
    )
    write_json(output_dir / "episodes.json", episodes)
    write_json(
        output_dir / "miss-clusters.json",
        {
            "clusters": dict(clusters),
            "episode_ids": [item["game_id"] for item in misses],
            "next_grammar_class": (
                clusters.most_common(1)[0][0] if clusters else "none"
            ),
        },
    )
    summary = {
        "mode": "LOCAL_ONLY",
        "submission_blocked": True,
        "no_kaggle_submit_lock": True,
        "games": len(episodes),
        "game_ids": [episode["game_id"] for episode in episodes],
        "environment_terminals": sum(
            item["terminal_reported_by_environment"] for item in episodes
        ),
        "win_terminals": sum(1 for item in episodes if item.get("win_terminal")),
        "game_over_events": sum(int(item.get("game_over_count") or 0) for item in episodes),
        "mean_confidence": (
            sum(item["confidence"] for item in episodes) / len(episodes) if episodes else 0.0
        ),
        "high_confidence_terminals": sum(
            item.get("win_terminal") and item["confidence"] == 1.0 for item in episodes
        ),
        "mean_turn_count": (
            sum(item["turn_count"] for item in episodes) / len(episodes) if episodes else 0.0
        ),
        "miss_clusters": dict(clusters),
        "next_grammar_class": clusters.most_common(1)[0][0] if clusters else "none",
        "parquet": str(parquet.relative_to(ROOT)),
        "episodes": str((output_dir / "episodes.json").relative_to(ROOT)),
        "captures": str(args.capture_dir.resolve().relative_to(ROOT)),
        "capture_mp4s": [
            episode["capture"].get("mp4", {}).get("path", "")
            for episode in episodes
            if episode["capture"].get("mp4", {}).get("path")
        ],
        "public_probe": {
            "submission_ref": "54875048",
            "publicScore": 0.12,
            "label": "PROCESS_PROBE",
        },
        "diagnosis": {
            "prior_missing_grammar_cause": (
                "FrameDataRaw.model_dump() omitted numpy frame → empty grids → "
                "zero compared_cells → unreproduced theory at max_actions=2"
            ),
            "fix": (
                "attribute-path frame tolist + 29-turn probes + PNG→MP4 capture + "
                "GAME_OVER→RESET continue + state-conditioned C4"
            ),
        },
    }
    write_json(output_dir / "summary.json", summary)

    arc_local = args.emit_arc_local_report
    if arc_local is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        arc_local = ROOT / f"reports/arc_local_{stamp}"
    emit_arc_local_report(arc_local.resolve(), episodes, summary)
    summary["arc_local_report"] = str(arc_local.resolve().relative_to(ROOT))
    write_json(output_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
