"""Local hybrid ARC solver: 8-marker readout + replay-gated DSL + icecuber.

FoT path label: LOCAL_HYBRID_SOLVER. Never emits [[0]] placeholders or
unvalidated guesses. Train-replay must pass before attempts are accepted.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

Grid = List[List[int]]


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_placeholder(grid: Any) -> bool:
    return grid == [[0]] or grid == [[]]


def _valid_grid(grid: Any) -> bool:
    if not isinstance(grid, list) or not grid or len(grid) > 30:
        return False
    width = None
    for row in grid:
        if not isinstance(row, list) or not row or len(row) > 30:
            return False
        if width is None:
            width = len(row)
        elif len(row) != width:
            return False
        for cell in row:
            if type(cell) is not int or cell < 0 or cell > 9:
                return False
    return not _is_placeholder(grid)


def _dsl_train_replay(solver: Any, train: List[Dict[str, Any]]) -> Dict[str, Any]:
    exact = solver.exact_candidates(train)
    if not exact:
        return {
            "engine": "replay_gated_dsl",
            "ok": False,
            "train_replay": f"0/{len(train)}",
            "train_replay_pass": 0,
            "train_replay_total": len(train),
            "licensed_transforms": [],
        }
    name, transform = exact[0]
    failures = [
        i for i, ex in enumerate(train) if transform(ex["input"]) != ex["output"]
    ]
    passes = len(train) - len(failures)
    return {
        "engine": "replay_gated_dsl",
        "ok": not failures and bool(exact),
        "train_replay": f"{passes}/{len(train)}",
        "train_replay_pass": passes,
        "train_replay_total": len(train),
        "licensed_transforms": [n for n, _ in exact],
        "primary_transform": name,
        "failed_demo_indices": failures,
    }


def _icecuber_train_replay(
    adapter: Any, repo_root: Path, task_id: str, task: Dict[str, Any]
) -> Tuple[Optional[List[Dict[str, Grid]]], Dict[str, Any]]:
    """Icecuber only when every training demonstration is exact-matched."""
    train = task["train"]
    if not train:
        return None, {"engine": "arc-icecuber", "ok": False, "train_replay": "0/0"}
    pseudo = {
        task_id: {
            "train": train,
            "test": [{"input": ex["input"]} for ex in train],
        }
    }
    solutions = {task_id: [ex["output"] for ex in train]}
    try:
        result = adapter.solve_challenge_set(
            repo_root, pseudo, solutions, depth=2, workers=1
        )
    except Exception as exc:
        return None, {
            "engine": "arc-icecuber",
            "ok": False,
            "train_replay": f"0/{len(train)}",
            "error": str(exc),
        }
    preds = result["predictions"][task_id]
    hits = 0
    for index, expected in enumerate(solutions[task_id]):
        pair = preds[index]
        if pair.get("attempt_1") == expected or pair.get("attempt_2") == expected:
            hits += 1
    meta = {
        "engine": "arc-icecuber",
        "ok": hits == len(train),
        "train_replay": f"{hits}/{len(train)}",
        "train_replay_pass": hits,
        "train_replay_total": len(train),
        "verdicts": result.get("verdicts"),
    }
    if hits != len(train):
        return None, meta
    real = adapter.predictions_for_task(repo_root, task_id, task, depth=2)
    return real, meta


def solve_task(
    repo_root: Path, task_id: str, task: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Return ({task_id: [attempts...]}, receipt) or (None, receipt) if unlicensed."""
    arc_dir = Path(__file__).resolve().parent
    receipt: Dict[str, Any] = {
        "task_id": task_id,
        "path_label": "LOCAL_HYBRID_SOLVER",
        "engines_tried": [],
        "accepted_engine": None,
        "train_replay": None,
        "ok": False,
    }

    # 1) 8-marker twin-S readout (0934a4d8; icecuber fails train-replay here).
    twin = _load_module(arc_dir / "marker8_twin31.py", "marker8_twin31")
    twin_replay = twin.train_replay(task)
    twin_fragment = twin.submission_fragment(task_id, task)
    receipt["engines_tried"].append(twin_replay)
    if (
        twin_fragment is not None
        and twin_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in twin_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "marker8_twin31"
        receipt["train_replay"] = twin_replay["train_replay"]
        receipt["ok"] = True
        receipt["marker_meta"] = twin_replay
        return twin_fragment, receipt

    marker = _load_module(arc_dir / "eight_marker_extractor.py", "eight_marker_extractor")
    marker_attempts, marker_meta = marker.predictions_for_task(task)
    receipt["engines_tried"].append(marker_meta)
    if marker_attempts is not None and all(
        _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
        for p in marker_attempts
    ):
        receipt["accepted_engine"] = marker_meta["engine"]
        receipt["train_replay"] = marker_meta["train_replay"]
        receipt["ok"] = True
        receipt["marker_meta"] = marker_meta
        return {task_id: marker_attempts}, receipt

    # 1b) S1 dimension projection (hollow/solid object pack; 2ba387bc).
    s1 = _load_module(arc_dir / "s1_dimension_projection.py", "s1_dimension_projection")
    s1_replay = s1.train_replay(task)
    s1_fragment = s1.submission_fragment(task_id, task)
    receipt["engines_tried"].append(s1_replay)
    if (
        s1_fragment is not None
        and s1_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in s1_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_dimension_projection"
        receipt["train_replay"] = s1_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_meta"] = s1_replay
        return s1_fragment, receipt

    # 1b2) S1 digit-separator snake pack (136b0064).
    s1snake = _load_module(
        arc_dir / "s1_digit_separator_snake.py", "s1_digit_separator_snake"
    )
    snake_replay = s1snake.train_replay(task)
    snake_fragment = s1snake.submission_fragment(task_id, task)
    receipt["engines_tried"].append(snake_replay)
    if (
        snake_fragment is not None
        and snake_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in snake_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_digit_separator_snake"
        receipt["train_replay"] = snake_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_snake_meta"] = snake_replay
        return snake_fragment, receipt

    # 1b3) S1 seven-tab merge (20270e3b).
    s1tab = _load_module(arc_dir / "s1_seven_tab_merge.py", "s1_seven_tab_merge")
    tab_replay = s1tab.train_replay(task)
    tab_fragment = s1tab.submission_fragment(task_id, task)
    receipt["engines_tried"].append(tab_replay)
    if (
        tab_fragment is not None
        and tab_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in tab_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_seven_tab_merge"
        receipt["train_replay"] = tab_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_tab_meta"] = tab_replay
        return tab_fragment, receipt

    # 1b4) S1 panel odd-one-out (38007db0).
    s1panel = _load_module(arc_dir / "s1_panel_odd_one_out.py", "s1_panel_odd_one_out")
    panel_replay = s1panel.train_replay(task)
    panel_fragment = s1panel.submission_fragment(task_id, task)
    receipt["engines_tried"].append(panel_replay)
    if (
        panel_fragment is not None
        and panel_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in panel_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_panel_odd_one_out"
        receipt["train_replay"] = panel_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_panel_meta"] = panel_replay
        return panel_fragment, receipt

    # 1b5) S1 marker-frame motif extrapolate (20a9e565).
    s1motif = _load_module(arc_dir / "s1_marker_frame_motif.py", "s1_marker_frame_motif")
    motif_replay = s1motif.train_replay(task)
    motif_fragment = s1motif.submission_fragment(task_id, task)
    receipt["engines_tried"].append(motif_replay)
    if (
        motif_fragment is not None
        and motif_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in motif_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_marker_frame_motif"
        receipt["train_replay"] = motif_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_motif_meta"] = motif_replay
        return motif_fragment, receipt

    # 1b6) S1 fixed-canvas template crop (269e22fb).
    s1canvas = _load_module(
        arc_dir / "s1_fixed_canvas_template.py", "s1_fixed_canvas_template"
    )
    canvas_replay = s1canvas.train_replay(task)
    canvas_fragment = s1canvas.submission_fragment(task_id, task)
    receipt["engines_tried"].append(canvas_replay)
    if (
        canvas_fragment is not None
        and canvas_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in canvas_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_fixed_canvas_template"
        receipt["train_replay"] = canvas_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_canvas_meta"] = canvas_replay
        return canvas_fragment, receipt

    # 1b7) S1 wall-tree nested frames (13e47133).
    s1frames = _load_module(
        arc_dir / "s1_wall_tree_nested_frames.py", "s1_wall_tree_nested_frames"
    )
    frames_replay = s1frames.train_replay(task)
    frames_fragment = s1frames.submission_fragment(task_id, task)
    receipt["engines_tried"].append(frames_replay)
    if (
        frames_fragment is not None
        and frames_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in frames_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_wall_tree_nested_frames"
        receipt["train_replay"] = frames_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_frames_meta"] = frames_replay
        return frames_fragment, receipt

    # 1b8) S1 laser-mirror diagonal beams (142ca369).
    s1laser = _load_module(
        arc_dir / "s1_laser_mirror_beams.py", "s1_laser_mirror_beams"
    )
    laser_replay = s1laser.train_replay(task)
    laser_fragment = s1laser.submission_fragment(task_id, task)
    receipt["engines_tried"].append(laser_replay)
    if (
        laser_fragment is not None
        and laser_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in laser_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_laser_mirror_beams"
        receipt["train_replay"] = laser_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_laser_meta"] = laser_replay
        return laser_fragment, receipt

    # 1b9) S1 oriented block pack (291dc1e1).
    s1pack = _load_module(
        arc_dir / "s1_oriented_block_pack.py", "s1_oriented_block_pack"
    )
    pack_replay = s1pack.train_replay(task)
    pack_fragment = s1pack.submission_fragment(task_id, task)
    receipt["engines_tried"].append(pack_replay)
    if (
        pack_fragment is not None
        and pack_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in pack_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_oriented_block_pack"
        receipt["train_replay"] = pack_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_pack_meta"] = pack_replay
        return pack_fragment, receipt

    # 1b10) S1 topology schematic (2d0172a1).
    s1topo = _load_module(
        arc_dir / "s1_topology_schematic.py", "s1_topology_schematic"
    )
    topo_replay = s1topo.train_replay(task)
    topo_fragment = s1topo.submission_fragment(task_id, task)
    receipt["engines_tried"].append(topo_replay)
    if (
        topo_fragment is not None
        and topo_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in topo_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_topology_schematic"
        receipt["train_replay"] = topo_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_topo_meta"] = topo_replay
        return topo_fragment, receipt

    # 1b11) S1 hollow accent-fill (3a25b0d8).
    s1hollow = _load_module(
        arc_dir / "s1_hollow_accent_fill.py", "s1_hollow_accent_fill"
    )
    hollow_replay = s1hollow.train_replay(task)
    hollow_fragment = s1hollow.submission_fragment(task_id, task)
    receipt["engines_tried"].append(hollow_replay)
    if (
        hollow_fragment is not None
        and hollow_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in hollow_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_hollow_accent_fill"
        receipt["train_replay"] = hollow_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_hollow_meta"] = hollow_replay
        return hollow_fragment, receipt

    # 1b12) S3 separator gap-stack (16b78196).
    s3gap = _load_module(
        arc_dir / "s3_separator_gap_stack.py", "s3_separator_gap_stack"
    )
    gap_replay = s3gap.train_replay(task)
    gap_fragment = s3gap.submission_fragment(task_id, task)
    receipt["engines_tried"].append(gap_replay)
    if (
        gap_fragment is not None
        and gap_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in gap_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_separator_gap_stack"
        receipt["train_replay"] = gap_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_gap_meta"] = gap_replay
        return gap_fragment, receipt

    # 1b13) S1 panel-motif projection (4c7dc4dd).
    s1panel = _load_module(
        arc_dir / "s1_panel_motif_projection.py", "s1_panel_motif_projection"
    )
    panel_replay = s1panel.train_replay(task)
    panel_fragment = s1panel.submission_fragment(task_id, task)
    receipt["engines_tried"].append(panel_replay)
    if (
        panel_fragment is not None
        and panel_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in panel_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_panel_motif_projection"
        receipt["train_replay"] = panel_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_panel_motif_meta"] = panel_replay
        return panel_fragment, receipt

    # 1b14) S1 motif-stamp jigsaw (4e34c42c).
    s1jigsaw = _load_module(
        arc_dir / "s1_motif_stamp_jigsaw.py", "s1_motif_stamp_jigsaw"
    )
    jigsaw_replay = s1jigsaw.train_replay(task)
    jigsaw_fragment = s1jigsaw.submission_fragment(task_id, task)
    receipt["engines_tried"].append(jigsaw_replay)
    if (
        jigsaw_fragment is not None
        and jigsaw_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in jigsaw_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_motif_stamp_jigsaw"
        receipt["train_replay"] = jigsaw_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_motif_jigsaw_meta"] = jigsaw_replay
        return jigsaw_fragment, receipt

    # 1b15) S1 legend-motif tally (58490d8a).
    s1legend = _load_module(
        arc_dir / "s1_legend_motif_tally.py", "s1_legend_motif_tally"
    )
    legend_replay = s1legend.train_replay(task)
    legend_fragment = s1legend.submission_fragment(task_id, task)
    receipt["engines_tried"].append(legend_replay)
    if (
        legend_fragment is not None
        and legend_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in legend_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_legend_motif_tally"
        receipt["train_replay"] = legend_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_legend_tally_meta"] = legend_replay
        return legend_fragment, receipt

    # 1b16) S1 solid-motif carve (58f5dbd5).
    s1carve = _load_module(
        arc_dir / "s1_solid_motif_carve.py", "s1_solid_motif_carve"
    )
    carve_replay = s1carve.train_replay(task)
    carve_fragment = s1carve.submission_fragment(task_id, task)
    receipt["engines_tried"].append(carve_replay)
    if (
        carve_fragment is not None
        and carve_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in carve_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_solid_motif_carve"
        receipt["train_replay"] = carve_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_solid_motif_carve_meta"] = carve_replay
        return carve_fragment, receipt

    # 1b17) S2 plus-stamp recolor (1818057f).
    s2plus = _load_module(
        arc_dir / "s2_plus_stamp_recolor.py", "s2_plus_stamp_recolor"
    )
    plus_replay = s2plus.train_replay(task)
    plus_fragment = s2plus.submission_fragment(task_id, task)
    receipt["engines_tried"].append(plus_replay)
    if (
        plus_fragment is not None
        and plus_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in plus_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_plus_stamp_recolor"
        receipt["train_replay"] = plus_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_plus_stamp_meta"] = plus_replay
        return plus_fragment, receipt

    # 1b18) S1 path-column unroll (7b5033c1).
    s1path = _load_module(
        arc_dir / "s1_path_column_unroll.py", "s1_path_column_unroll"
    )
    path_replay = s1path.train_replay(task)
    path_fragment = s1path.submission_fragment(task_id, task)
    receipt["engines_tried"].append(path_replay)
    if (
        path_fragment is not None
        and path_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in path_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_path_column_unroll"
        receipt["train_replay"] = path_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_path_column_unroll_meta"] = path_replay
        return path_fragment, receipt

    # 1b19) S1 ones-stamp period fill (53fb4810).
    s1ones = _load_module(
        arc_dir / "s1_ones_stamp_period_fill.py", "s1_ones_stamp_period_fill"
    )
    ones_replay = s1ones.train_replay(task)
    ones_fragment = s1ones.submission_fragment(task_id, task)
    receipt["engines_tried"].append(ones_replay)
    if (
        ones_fragment is not None
        and ones_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ones_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_ones_stamp_period_fill"
        receipt["train_replay"] = ones_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_ones_stamp_period_fill_meta"] = ones_replay
        return ones_fragment, receipt

    # 1b20) S1 canvas-hole sprite fill (67e490f4).
    s1hole = _load_module(
        arc_dir / "s1_canvas_hole_sprite_fill.py", "s1_canvas_hole_sprite_fill"
    )
    hole_replay = s1hole.train_replay(task)
    hole_fragment = s1hole.submission_fragment(task_id, task)
    receipt["engines_tried"].append(hole_replay)
    if (
        hole_fragment is not None
        and hole_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in hole_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_canvas_hole_sprite_fill"
        receipt["train_replay"] = hole_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_canvas_hole_sprite_fill_meta"] = hole_replay
        return hole_fragment, receipt

    # 1b21) S1 panel-motif nest pack (8698868d).
    s1nest = _load_module(
        arc_dir / "s1_panel_motif_nest_pack.py", "s1_panel_motif_nest_pack"
    )
    nest_replay = s1nest.train_replay(task)
    nest_fragment = s1nest.submission_fragment(task_id, task)
    receipt["engines_tried"].append(nest_replay)
    if (
        nest_fragment is not None
        and nest_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in nest_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_panel_motif_nest_pack"
        receipt["train_replay"] = nest_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_panel_motif_nest_pack_meta"] = nest_replay
        return nest_fragment, receipt

    # 1b22) S1 separator-block unroll (78332cb0).
    s1unroll = _load_module(
        arc_dir / "s1_separator_block_unroll.py", "s1_separator_block_unroll"
    )
    unroll_replay = s1unroll.train_replay(task)
    unroll_fragment = s1unroll.submission_fragment(task_id, task)
    receipt["engines_tried"].append(unroll_replay)
    if (
        unroll_fragment is not None
        and unroll_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in unroll_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_separator_block_unroll"
        receipt["train_replay"] = unroll_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_separator_block_unroll_meta"] = unroll_replay
        return unroll_fragment, receipt

    # 1b23) S1 separator-row extent sort (31f7f899).
    s1ext = _load_module(
        arc_dir / "s1_sep_row_extent_sort.py", "s1_sep_row_extent_sort"
    )
    ext_replay = s1ext.train_replay(task)
    ext_fragment = s1ext.submission_fragment(task_id, task)
    receipt["engines_tried"].append(ext_replay)
    if (
        ext_fragment is not None
        and ext_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ext_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_sep_row_extent_sort"
        receipt["train_replay"] = ext_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_sep_row_extent_sort_meta"] = ext_replay
        return ext_fragment, receipt

    # 1b24) S1 frame-chamber staircase (89565ca0).
    s1ch = _load_module(
        arc_dir / "s1_frame_chamber_staircase.py", "s1_frame_chamber_staircase"
    )
    ch_replay = s1ch.train_replay(task)
    ch_fragment = s1ch.submission_fragment(task_id, task)
    receipt["engines_tried"].append(ch_replay)
    if (
        ch_fragment is not None
        and ch_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ch_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_frame_chamber_staircase"
        receipt["train_replay"] = ch_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_frame_chamber_staircase_meta"] = ch_replay
        return ch_fragment, receipt

    # 1b25) S1 header-bracket fill (97d7923e).
    s1hb = _load_module(
        arc_dir / "s1_header_bracket_fill.py", "s1_header_bracket_fill"
    )
    hb_replay = s1hb.train_replay(task)
    hb_fragment = s1hb.submission_fragment(task_id, task)
    receipt["engines_tried"].append(hb_replay)
    if (
        hb_fragment is not None
        and hb_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in hb_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_header_bracket_fill"
        receipt["train_replay"] = hb_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_header_bracket_fill_meta"] = hb_replay
        return hb_fragment, receipt

    # 1b26) S2 arrow-room recolor (21897d95).
    s2ar = _load_module(
        arc_dir / "s2_arrow_room_recolor.py", "s2_arrow_room_recolor"
    )
    ar_replay = s2ar.train_replay(task)
    ar_fragment = s2ar.submission_fragment(task_id, task)
    receipt["engines_tried"].append(ar_replay)
    if (
        ar_fragment is not None
        and ar_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ar_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_arrow_room_recolor"
        receipt["train_replay"] = ar_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_arrow_room_recolor_meta"] = ar_replay
        return ar_fragment, receipt

    # 1b27) S2 marker-stripe lattice (221dfab4).
    s2ms = _load_module(
        arc_dir / "s2_marker_stripe_lattice.py", "s2_marker_stripe_lattice"
    )
    ms_replay = s2ms.train_replay(task)
    ms_fragment = s2ms.submission_fragment(task_id, task)
    receipt["engines_tried"].append(ms_replay)
    if (
        ms_fragment is not None
        and ms_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ms_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_marker_stripe_lattice"
        receipt["train_replay"] = ms_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_marker_stripe_lattice_meta"] = ms_replay
        return ms_fragment, receipt

    # 1b28) S2 axis-glyph stamp (247ef758).
    s2ag = _load_module(
        arc_dir / "s2_axis_glyph_stamp.py", "s2_axis_glyph_stamp"
    )
    ag_replay = s2ag.train_replay(task)
    ag_fragment = s2ag.submission_fragment(task_id, task)
    receipt["engines_tried"].append(ag_replay)
    if (
        ag_fragment is not None
        and ag_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ag_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_axis_glyph_stamp"
        receipt["train_replay"] = ag_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_axis_glyph_stamp_meta"] = ag_replay
        return ag_fragment, receipt

    # 1b29) S3 box-slide rail-fill (271d71e2).
    s3box = _load_module(
        arc_dir / "s3_box_slide_rail_fill.py", "s3_box_slide_rail_fill"
    )
    box_replay = s3box.train_replay(task)
    box_fragment = s3box.submission_fragment(task_id, task)
    receipt["engines_tried"].append(box_replay)
    if (
        box_fragment is not None
        and box_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in box_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_box_slide_rail_fill"
        receipt["train_replay"] = box_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_box_slide_rail_fill_meta"] = box_replay
        return box_fragment, receipt

    # 1b30) S3 staircase interior fill (28a6681f).
    s3stair = _load_module(
        arc_dir / "s3_staircase_interior_fill.py", "s3_staircase_interior_fill"
    )
    stair_replay = s3stair.train_replay(task)
    stair_fragment = s3stair.submission_fragment(task_id, task)
    receipt["engines_tried"].append(stair_replay)
    if (
        stair_fragment is not None
        and stair_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in stair_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_staircase_interior_fill"
        receipt["train_replay"] = stair_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_staircase_interior_fill_meta"] = stair_replay
        return stair_fragment, receipt

    # 1b31) S2 seven-triplet rail palette (2b83f449).
    s2trip = _load_module(
        arc_dir / "s2_seven_triplet_rail.py", "s2_seven_triplet_rail"
    )
    trip_replay = s2trip.train_replay(task)
    trip_fragment = s2trip.submission_fragment(task_id, task)
    receipt["engines_tried"].append(trip_replay)
    if (
        trip_fragment is not None
        and trip_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in trip_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_seven_triplet_rail"
        receipt["train_replay"] = trip_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_seven_triplet_rail_meta"] = trip_replay
        return trip_fragment, receipt

    # 1b32) S3 cross-arm shape dock (2c181942).
    s3cross = _load_module(
        arc_dir / "s3_cross_arm_shape_dock.py", "s3_cross_arm_shape_dock"
    )
    cross_replay = s3cross.train_replay(task)
    cross_fragment = s3cross.submission_fragment(task_id, task)
    receipt["engines_tried"].append(cross_replay)
    if (
        cross_fragment is not None
        and cross_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in cross_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_cross_arm_shape_dock"
        receipt["train_replay"] = cross_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_cross_arm_shape_dock_meta"] = cross_replay
        return cross_fragment, receipt

    # 1b33) S3 primary hull shift (35ab12c3).
    s3hull = _load_module(
        arc_dir / "s3_primary_hull_shift.py", "s3_primary_hull_shift"
    )
    hull_replay = s3hull.train_replay(task)
    hull_fragment = s3hull.submission_fragment(task_id, task)
    receipt["engines_tried"].append(hull_replay)
    if (
        hull_fragment is not None
        and hull_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in hull_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_primary_hull_shift"
        receipt["train_replay"] = hull_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_primary_hull_shift_meta"] = hull_replay
        return hull_fragment, receipt

    # 1b34) S2 black-block path slide (332f06d7).
    s2black = _load_module(
        arc_dir / "s2_black_block_path_slide.py", "s2_black_block_path_slide"
    )
    black_replay = s2black.train_replay(task)
    black_fragment = s2black.submission_fragment(task_id, task)
    receipt["engines_tried"].append(black_replay)
    if (
        black_fragment is not None
        and black_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in black_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_black_block_path_slide"
        receipt["train_replay"] = black_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_black_block_path_slide_meta"] = black_replay
        return black_fragment, receipt

    # 1b35) S3 purple bar-bracket extend (36a08778).
    s3purp = _load_module(
        arc_dir / "s3_purple_bar_bracket_extend.py", "s3_purple_bar_bracket_extend"
    )
    purp_replay = s3purp.train_replay(task)
    purp_fragment = s3purp.submission_fragment(task_id, task)
    receipt["engines_tried"].append(purp_replay)
    if (
        purp_fragment is not None
        and purp_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in purp_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_purple_bar_bracket_extend"
        receipt["train_replay"] = purp_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_purple_bar_bracket_extend_meta"] = purp_replay
        return purp_fragment, receipt



    # 1b35) s2_diagonal_component_fill (7666fa5d).
    s2diag = _load_module(
        arc_dir / "s2_diagonal_component_fill.py", "s2_diagonal_component_fill"
    )
    s2diag_replay = s2diag.train_replay(task)
    s2diag_fragment = s2diag.submission_fragment(task_id, task)
    receipt["engines_tried"].append(s2diag_replay)
    if (
        s2diag_fragment is not None
        and s2diag_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in s2diag_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_diagonal_component_fill"
        receipt["train_replay"] = s2diag_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_diagonal_component_fill_meta"] = s2diag_replay
        return s2diag_fragment, receipt

    # 1b36) s3_period_tile_stamp (3e6067c3).
    s3per = _load_module(
        arc_dir / "s3_period_tile_stamp.py", "s3_period_tile_stamp"
    )
    s3per_replay = s3per.train_replay(task)
    s3per_fragment = s3per.submission_fragment(task_id, task)
    receipt["engines_tried"].append(s3per_replay)
    if (
        s3per_fragment is not None
        and s3per_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in s3per_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_period_tile_stamp"
        receipt["train_replay"] = s3per_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_period_tile_stamp_meta"] = s3per_replay
        return s3per_fragment, receipt

    # 1b37) s3_border_path_fill (7c66cb00).
    s3bord = _load_module(
        arc_dir / "s3_border_path_fill.py", "s3_border_path_fill"
    )
    s3bord_replay = s3bord.train_replay(task)
    s3bord_fragment = s3bord.submission_fragment(task_id, task)
    receipt["engines_tried"].append(s3bord_replay)
    if (
        s3bord_fragment is not None
        and s3bord_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in s3bord_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_border_path_fill"
        receipt["train_replay"] = s3bord_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_border_path_fill_meta"] = s3bord_replay
        return s3bord_fragment, receipt


    # 1b38) s1_anchor_crop_expand (898e7135).
    e0 = _load_module(
        arc_dir / "s1_anchor_crop_expand.py", "s1_anchor_crop_expand"
    )
    e0_replay = e0.train_replay(task)
    e0_fragment = e0.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e0_replay)
    if (
        e0_fragment is not None
        and e0_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e0_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_anchor_crop_expand"
        receipt["train_replay"] = e0_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_anchor_crop_expand_meta"] = e0_replay
        return e0_fragment, receipt

    # 1b39) s2_marker_recolor_lattice (8f3a5a89).
    e1 = _load_module(
        arc_dir / "s2_marker_recolor_lattice.py", "s2_marker_recolor_lattice"
    )
    e1_replay = e1.train_replay(task)
    e1_fragment = e1.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e1_replay)
    if (
        e1_fragment is not None
        and e1_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e1_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_marker_recolor_lattice"
        receipt["train_replay"] = e1_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_marker_recolor_lattice_meta"] = e1_replay
        return e1_fragment, receipt

    # 1b40) s2_color_gate_rewrite (9aaea919).
    e2 = _load_module(
        arc_dir / "s2_color_gate_rewrite.py", "s2_color_gate_rewrite"
    )
    e2_replay = e2.train_replay(task)
    e2_fragment = e2.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e2_replay)
    if (
        e2_fragment is not None
        and e2_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e2_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_color_gate_rewrite"
        receipt["train_replay"] = e2_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_color_gate_rewrite_meta"] = e2_replay
        return e2_fragment, receipt

    # 1b41) s2_pair_swap_recolor (aa4ec2a5).
    e3 = _load_module(
        arc_dir / "s2_pair_swap_recolor.py", "s2_pair_swap_recolor"
    )
    e3_replay = e3.train_replay(task)
    e3_fragment = e3.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e3_replay)
    if (
        e3_fragment is not None
        and e3_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e3_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_pair_swap_recolor"
        receipt["train_replay"] = e3_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_pair_swap_recolor_meta"] = e3_replay
        return e3_fragment, receipt

    # 1b42) s1_panel_scale_project (b0039139).
    e4 = _load_module(
        arc_dir / "s1_panel_scale_project.py", "s1_panel_scale_project"
    )
    e4_replay = e4.train_replay(task)
    e4_fragment = e4.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e4_replay)
    if (
        e4_fragment is not None
        and e4_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e4_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_panel_scale_project"
        receipt["train_replay"] = e4_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_panel_scale_project_meta"] = e4_replay
        return e4_fragment, receipt

    # 1b43) s3_object_align_shift (b99e7126).
    e5 = _load_module(
        arc_dir / "s3_object_align_shift.py", "s3_object_align_shift"
    )
    e5_replay = e5.train_replay(task)
    e5_fragment = e5.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e5_replay)
    if (
        e5_fragment is not None
        and e5_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e5_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_object_align_shift"
        receipt["train_replay"] = e5_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_object_align_shift_meta"] = e5_replay
        return e5_fragment, receipt

    # 1b44) s1_frame_extract_project (bf45cf4b).
    e6 = _load_module(
        arc_dir / "s1_frame_extract_project.py", "s1_frame_extract_project"
    )
    e6_replay = e6.train_replay(task)
    e6_fragment = e6.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e6_replay)
    if (
        e6_fragment is not None
        and e6_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e6_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_frame_extract_project"
        receipt["train_replay"] = e6_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_frame_extract_project_meta"] = e6_replay
        return e6_fragment, receipt

    # 1b45) s3_mirror_fold_fill (db0c5428).
    e7 = _load_module(
        arc_dir / "s3_mirror_fold_fill.py", "s3_mirror_fold_fill"
    )
    e7_replay = e7.train_replay(task)
    e7_fragment = e7.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e7_replay)
    if (
        e7_fragment is not None
        and e7_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e7_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_mirror_fold_fill"
        receipt["train_replay"] = e7_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_mirror_fold_fill_meta"] = e7_replay
        return e7_fragment, receipt

    # 1b46) s3_contact_grow_fill (db695cfb).
    e8 = _load_module(
        arc_dir / "s3_contact_grow_fill.py", "s3_contact_grow_fill"
    )
    e8_replay = e8.train_replay(task)
    e8_fragment = e8.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e8_replay)
    if (
        e8_fragment is not None
        and e8_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e8_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_contact_grow_fill"
        receipt["train_replay"] = e8_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_contact_grow_fill_meta"] = e8_replay
        return e8_fragment, receipt

    # 1b47) s1_strip_stack_project (e8686506).
    e9 = _load_module(
        arc_dir / "s1_strip_stack_project.py", "s1_strip_stack_project"
    )
    e9_replay = e9.train_replay(task)
    e9_fragment = e9.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e9_replay)
    if (
        e9_fragment is not None
        and e9_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e9_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_strip_stack_project"
        receipt["train_replay"] = e9_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_strip_stack_project_meta"] = e9_replay
        return e9_fragment, receipt

    # 1b48) s3_triomino_tip_ray (409aa875).
    e10 = _load_module(
        arc_dir / "s3_triomino_tip_ray.py", "s3_triomino_tip_ray"
    )
    e10_replay = e10.train_replay(task)
    e10_fragment = e10.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e10_replay)
    if (
        e10_fragment is not None
        and e10_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e10_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_triomino_tip_ray"
        receipt["train_replay"] = e10_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_triomino_tip_ray_meta"] = e10_replay
        return e10_fragment, receipt

    # 1b49) S3 marker tip-beam (3dc255db).
    s3beam = _load_module(
        arc_dir / "s3_marker_tip_beam.py", "s3_marker_tip_beam"
    )
    beam_replay = s3beam.train_replay(task)
    beam_fragment = s3beam.submission_fragment(task_id, task)
    receipt["engines_tried"].append(beam_replay)
    if (
        beam_fragment is not None
        and beam_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in beam_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_marker_tip_beam"
        receipt["train_replay"] = beam_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_marker_tip_beam_meta"] = beam_replay
        return beam_fragment, receipt

    # 1b50) S2 tagged-shape border pack (446ef5d2).
    s2pack = _load_module(
        arc_dir / "s2_tagged_shape_border_pack.py", "s2_tagged_shape_border_pack"
    )
    pack_replay = s2pack.train_replay(task)
    pack_fragment = s2pack.submission_fragment(task_id, task)
    receipt["engines_tried"].append(pack_replay)
    if (
        pack_fragment is not None
        and pack_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in pack_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_tagged_shape_border_pack"
        receipt["train_replay"] = pack_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_tagged_shape_border_pack_meta"] = pack_replay
        return pack_fragment, receipt


    # 1b51) s2_palette_partition_recolor (4a21e3da).
    e51 = _load_module(
        arc_dir / "s2_palette_partition_recolor.py", "s2_palette_partition_recolor"
    )
    e51_replay = e51.train_replay(task)
    e51_fragment = e51.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e51_replay)
    if (
        e51_fragment is not None
        and e51_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e51_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_palette_partition_recolor"
        receipt["train_replay"] = e51_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_palette_partition_recolor_meta"] = e51_replay
        return e51_fragment, receipt

    # 1b52) s3_lattice_seed_grow (4c3d4a41).
    e52 = _load_module(
        arc_dir / "s3_lattice_seed_grow.py", "s3_lattice_seed_grow"
    )
    e52_replay = e52.train_replay(task)
    e52_fragment = e52.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e52_replay)
    if (
        e52_fragment is not None
        and e52_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e52_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_lattice_seed_grow"
        receipt["train_replay"] = e52_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_lattice_seed_grow_meta"] = e52_replay
        return e52_fragment, receipt

    # 1b53) s3_template_marker_expand (4c416de3).
    e53 = _load_module(
        arc_dir / "s3_template_marker_expand.py", "s3_template_marker_expand"
    )
    e53_replay = e53.train_replay(task)
    e53_fragment = e53.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e53_replay)
    if (
        e53_fragment is not None
        and e53_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e53_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_template_marker_expand"
        receipt["train_replay"] = e53_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_template_marker_expand_meta"] = e53_replay
        return e53_fragment, receipt

    # 1b54) s3_object_gravity_stack (5545f144).
    e54 = _load_module(
        arc_dir / "s3_object_gravity_stack.py", "s3_object_gravity_stack"
    )
    e54_replay = e54.train_replay(task)
    e54_fragment = e54.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e54_replay)
    if (
        e54_fragment is not None
        and e54_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e54_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_object_gravity_stack"
        receipt["train_replay"] = e54_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_object_gravity_stack_meta"] = e54_replay
        return e54_fragment, receipt

    # 1b55) s2_dual_palette_rewrite (581f7754).
    e55 = _load_module(
        arc_dir / "s2_dual_palette_rewrite.py", "s2_dual_palette_rewrite"
    )
    e55_replay = e55.train_replay(task)
    e55_fragment = e55.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e55_replay)
    if (
        e55_fragment is not None
        and e55_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e55_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_dual_palette_rewrite"
        receipt["train_replay"] = e55_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_dual_palette_rewrite_meta"] = e55_replay
        return e55_fragment, receipt

    # 1b56) s3_corridor_fill (5961cc34).
    e56 = _load_module(
        arc_dir / "s3_corridor_fill.py", "s3_corridor_fill"
    )
    e56_replay = e56.train_replay(task)
    e56_fragment = e56.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e56_replay)
    if (
        e56_fragment is not None
        and e56_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e56_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_corridor_fill"
        receipt["train_replay"] = e56_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_corridor_fill_meta"] = e56_replay
        return e56_fragment, receipt

    # 1b57) s3_sprite_align_compose (5dbc8537).
    e57 = _load_module(
        arc_dir / "s3_sprite_align_compose.py", "s3_sprite_align_compose"
    )
    e57_replay = e57.train_replay(task)
    e57_fragment = e57.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e57_replay)
    if (
        e57_fragment is not None
        and e57_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e57_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_sprite_align_compose"
        receipt["train_replay"] = e57_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_sprite_align_compose_meta"] = e57_replay
        return e57_fragment, receipt

    # 1b58) s2_marker_gate_recolor (62593bfd).
    e58 = _load_module(
        arc_dir / "s2_marker_gate_recolor.py", "s2_marker_gate_recolor"
    )
    e58_replay = e58.train_replay(task)
    e58_fragment = e58.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e58_replay)
    if (
        e58_fragment is not None
        and e58_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e58_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_marker_gate_recolor"
        receipt["train_replay"] = e58_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_marker_gate_recolor_meta"] = e58_replay
        return e58_fragment, receipt

    # 1b59) s3_period_motif_tile (64efde09).
    e59 = _load_module(
        arc_dir / "s3_period_motif_tile.py", "s3_period_motif_tile"
    )
    e59_replay = e59.train_replay(task)
    e59_fragment = e59.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e59_replay)
    if (
        e59_fragment is not None
        and e59_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e59_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_period_motif_tile"
        receipt["train_replay"] = e59_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_period_motif_tile_meta"] = e59_replay
        return e59_fragment, receipt

    # 1b60) s2_symmetric_recolor (65b59efc).
    e60 = _load_module(
        arc_dir / "s2_symmetric_recolor.py", "s2_symmetric_recolor"
    )
    e60_replay = e60.train_replay(task)
    e60_fragment = e60.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e60_replay)
    if (
        e60_fragment is not None
        and e60_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e60_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_symmetric_recolor"
        receipt["train_replay"] = e60_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_symmetric_recolor_meta"] = e60_replay
        return e60_fragment, receipt

    # 1b61) s3_path_connect_fill (6e453dd6).
    e61 = _load_module(
        arc_dir / "s3_path_connect_fill.py", "s3_path_connect_fill"
    )
    e61_replay = e61.train_replay(task)
    e61_fragment = e61.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e61_replay)
    if (
        e61_fragment is not None
        and e61_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e61_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_path_connect_fill"
        receipt["train_replay"] = e61_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_path_connect_fill_meta"] = e61_replay
        return e61_fragment, receipt

    # 1b62) s3_complex_spatial_rewrite (6e4f6532).
    e62 = _load_module(
        arc_dir / "s3_complex_spatial_rewrite.py", "s3_complex_spatial_rewrite"
    )
    e62_replay = e62.train_replay(task)
    e62_fragment = e62.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e62_replay)
    if (
        e62_fragment is not None
        and e62_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e62_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_complex_spatial_rewrite"
        receipt["train_replay"] = e62_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_complex_spatial_rewrite_meta"] = e62_replay
        return e62_fragment, receipt

    # 1b63) s2_local_palette_rewrite (6ffbe589).
    e63 = _load_module(
        arc_dir / "s2_local_palette_rewrite.py", "s2_local_palette_rewrite"
    )
    e63_replay = e63.train_replay(task)
    e63_fragment = e63.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e63_replay)
    if (
        e63_fragment is not None
        and e63_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e63_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_local_palette_rewrite"
        receipt["train_replay"] = e63_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_local_palette_rewrite_meta"] = e63_replay
        return e63_fragment, receipt

    # 1b64) s3_frame_motif_project (71e489b6).
    e64 = _load_module(
        arc_dir / "s3_frame_motif_project.py", "s3_frame_motif_project"
    )
    e64_replay = e64.train_replay(task)
    e64_fragment = e64.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e64_replay)
    if (
        e64_fragment is not None
        and e64_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e64_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_frame_motif_project"
        receipt["train_replay"] = e64_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_frame_motif_project_meta"] = e64_replay
        return e64_fragment, receipt

    # 1b65) s3_object_nest_pack (7491f3cf).
    e65 = _load_module(
        arc_dir / "s3_object_nest_pack.py", "s3_object_nest_pack"
    )
    e65_replay = e65.train_replay(task)
    e65_fragment = e65.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e65_replay)
    if (
        e65_fragment is not None
        and e65_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e65_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_object_nest_pack"
        receipt["train_replay"] = e65_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_object_nest_pack_meta"] = e65_replay
        return e65_fragment, receipt

    # 1b66) s2_component_recolor (7b0280bc).
    e66 = _load_module(
        arc_dir / "s2_component_recolor.py", "s2_component_recolor"
    )
    e66_replay = e66.train_replay(task)
    e66_fragment = e66.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e66_replay)
    if (
        e66_fragment is not None
        and e66_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e66_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_component_recolor"
        receipt["train_replay"] = e66_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_component_recolor_meta"] = e66_replay
        return e66_fragment, receipt

    # 1b67) s3_ray_bounce_fill (7b3084d4).
    e67 = _load_module(
        arc_dir / "s3_ray_bounce_fill.py", "s3_ray_bounce_fill"
    )
    e67_replay = e67.train_replay(task)
    e67_fragment = e67.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e67_replay)
    if (
        e67_fragment is not None
        and e67_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e67_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_ray_bounce_fill"
        receipt["train_replay"] = e67_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_ray_bounce_fill_meta"] = e67_replay
        return e67_fragment, receipt

    # 1b68) s3_separator_motif_fill (7b80bb43).
    e68 = _load_module(
        arc_dir / "s3_separator_motif_fill.py", "s3_separator_motif_fill"
    )
    e68_replay = e68.train_replay(task)
    e68_fragment = e68.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e68_replay)
    if (
        e68_fragment is not None
        and e68_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e68_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_separator_motif_fill"
        receipt["train_replay"] = e68_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_separator_motif_fill_meta"] = e68_replay
        return e68_fragment, receipt

    # 1b69) s2_paired_recolor (7ed72f31).
    e69 = _load_module(
        arc_dir / "s2_paired_recolor.py", "s2_paired_recolor"
    )
    e69_replay = e69.train_replay(task)
    e69_fragment = e69.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e69_replay)
    if (
        e69_fragment is not None
        and e69_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e69_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_paired_recolor"
        receipt["train_replay"] = e69_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_paired_recolor_meta"] = e69_replay
        return e69_fragment, receipt

    # 1b70) s3_bbox_motif_stamp (800d221b).
    e70 = _load_module(
        arc_dir / "s3_bbox_motif_stamp.py", "s3_bbox_motif_stamp"
    )
    e70_replay = e70.train_replay(task)
    e70_fragment = e70.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e70_replay)
    if (
        e70_fragment is not None
        and e70_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e70_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_bbox_motif_stamp"
        receipt["train_replay"] = e70_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_bbox_motif_stamp_meta"] = e70_replay
        return e70_fragment, receipt


    # 1b50) s3_keycol_row_extend (7b80bb43).
    heal0 = _load_module(
        arc_dir / "s3_keycol_row_extend.py", "s3_keycol_row_extend"
    )
    heal0_replay = heal0.train_replay(task)
    heal0_fragment = heal0.submission_fragment(task_id, task)
    receipt["engines_tried"].append(heal0_replay)
    if (
        heal0_fragment is not None
        and heal0_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in heal0_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_keycol_row_extend"
        receipt["train_replay"] = heal0_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_keycol_row_extend_meta"] = heal0_replay
        return heal0_fragment, receipt

    # 1b51) s3_axis_reflect_paint (7ed72f31).
    heal1 = _load_module(
        arc_dir / "s3_axis_reflect_paint.py", "s3_axis_reflect_paint"
    )
    heal1_replay = heal1.train_replay(task)
    heal1_fragment = heal1.submission_fragment(task_id, task)
    receipt["engines_tried"].append(heal1_replay)
    if (
        heal1_fragment is not None
        and heal1_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in heal1_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_axis_reflect_paint"
        receipt["train_replay"] = heal1_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_axis_reflect_paint_meta"] = heal1_replay
        return heal1_fragment, receipt


    # 1b71) s3_g_80a900e0 (80a900e0).
    e71 = _load_module(
        arc_dir / "s3_g_80a900e0.py", "s3_g_80a900e0"
    )
    e71_replay = e71.train_replay(task)
    e71_fragment = e71.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e71_replay)
    if (
        e71_fragment is not None
        and e71_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e71_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_80a900e0"
        receipt["train_replay"] = e71_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_80a900e0_meta"] = e71_replay
        return e71_fragment, receipt

    # 1b72) s3_g_88bcf3b4 (88bcf3b4).
    e72 = _load_module(
        arc_dir / "s3_g_88bcf3b4.py", "s3_g_88bcf3b4"
    )
    e72_replay = e72.train_replay(task)
    e72_fragment = e72.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e72_replay)
    if (
        e72_fragment is not None
        and e72_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e72_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_88bcf3b4"
        receipt["train_replay"] = e72_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_88bcf3b4_meta"] = e72_replay
        return e72_fragment, receipt

    # 1b73) s3_g_88e364bc (88e364bc).
    e73 = _load_module(
        arc_dir / "s3_g_88e364bc.py", "s3_g_88e364bc"
    )
    e73_replay = e73.train_replay(task)
    e73_fragment = e73.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e73_replay)
    if (
        e73_fragment is not None
        and e73_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e73_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_88e364bc"
        receipt["train_replay"] = e73_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_88e364bc_meta"] = e73_replay
        return e73_fragment, receipt

    # 1b74) s3_g_8b7bacbf (8b7bacbf).
    e74 = _load_module(
        arc_dir / "s3_g_8b7bacbf.py", "s3_g_8b7bacbf"
    )
    e74_replay = e74.train_replay(task)
    e74_fragment = e74.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e74_replay)
    if (
        e74_fragment is not None
        and e74_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e74_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_8b7bacbf"
        receipt["train_replay"] = e74_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_8b7bacbf_meta"] = e74_replay
        return e74_fragment, receipt

    # 1b75) s3_g_8b9c3697 (8b9c3697).
    e75 = _load_module(
        arc_dir / "s3_g_8b9c3697.py", "s3_g_8b9c3697"
    )
    e75_replay = e75.train_replay(task)
    e75_fragment = e75.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e75_replay)
    if (
        e75_fragment is not None
        and e75_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e75_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_8b9c3697"
        receipt["train_replay"] = e75_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_8b9c3697_meta"] = e75_replay
        return e75_fragment, receipt

    # 1b76) s3_g_8e5c0c38 (8e5c0c38).
    e76 = _load_module(
        arc_dir / "s3_g_8e5c0c38.py", "s3_g_8e5c0c38"
    )
    e76_replay = e76.train_replay(task)
    e76_fragment = e76.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e76_replay)
    if (
        e76_fragment is not None
        and e76_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e76_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_8e5c0c38"
        receipt["train_replay"] = e76_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_8e5c0c38_meta"] = e76_replay
        return e76_fragment, receipt

    # 1b77) s3_g_8f215267 (8f215267).
    e77 = _load_module(
        arc_dir / "s3_g_8f215267.py", "s3_g_8f215267"
    )
    e77_replay = e77.train_replay(task)
    e77_fragment = e77.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e77_replay)
    if (
        e77_fragment is not None
        and e77_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e77_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_8f215267"
        receipt["train_replay"] = e77_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_8f215267_meta"] = e77_replay
        return e77_fragment, receipt

    # 1b78) s3_g_9bbf930d (9bbf930d).
    e78 = _load_module(
        arc_dir / "s3_g_9bbf930d.py", "s3_g_9bbf930d"
    )
    e78_replay = e78.train_replay(task)
    e78_fragment = e78.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e78_replay)
    if (
        e78_fragment is not None
        and e78_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e78_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_9bbf930d"
        receipt["train_replay"] = e78_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_9bbf930d_meta"] = e78_replay
        return e78_fragment, receipt

    # 1b79) s3_g_a251c730 (a251c730).
    e79 = _load_module(
        arc_dir / "s3_g_a251c730.py", "s3_g_a251c730"
    )
    e79_replay = e79.train_replay(task)
    e79_fragment = e79.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e79_replay)
    if (
        e79_fragment is not None
        and e79_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e79_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_a251c730"
        receipt["train_replay"] = e79_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_a251c730_meta"] = e79_replay
        return e79_fragment, receipt

    # 1b80) s3_g_a25697e4 (a25697e4).
    e80 = _load_module(
        arc_dir / "s3_g_a25697e4.py", "s3_g_a25697e4"
    )
    e80_replay = e80.train_replay(task)
    e80_fragment = e80.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e80_replay)
    if (
        e80_fragment is not None
        and e80_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e80_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_a25697e4"
        receipt["train_replay"] = e80_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_a25697e4_meta"] = e80_replay
        return e80_fragment, receipt

    # 1b81) s3_g_a32d8b75 (a32d8b75).
    e81 = _load_module(
        arc_dir / "s3_g_a32d8b75.py", "s3_g_a32d8b75"
    )
    e81_replay = e81.train_replay(task)
    e81_fragment = e81.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e81_replay)
    if (
        e81_fragment is not None
        and e81_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e81_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_a32d8b75"
        receipt["train_replay"] = e81_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_a32d8b75_meta"] = e81_replay
        return e81_fragment, receipt

    # 1b82) s3_g_a395ee82 (a395ee82).
    e82 = _load_module(
        arc_dir / "s3_g_a395ee82.py", "s3_g_a395ee82"
    )
    e82_replay = e82.train_replay(task)
    e82_fragment = e82.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e82_replay)
    if (
        e82_fragment is not None
        and e82_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e82_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_a395ee82"
        receipt["train_replay"] = e82_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_a395ee82_meta"] = e82_replay
        return e82_fragment, receipt

    # 1b83) s3_g_a47bf94d (a47bf94d).
    e83 = _load_module(
        arc_dir / "s3_g_a47bf94d.py", "s3_g_a47bf94d"
    )
    e83_replay = e83.train_replay(task)
    e83_fragment = e83.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e83_replay)
    if (
        e83_fragment is not None
        and e83_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e83_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_a47bf94d"
        receipt["train_replay"] = e83_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_a47bf94d_meta"] = e83_replay
        return e83_fragment, receipt

    # 1b84) s3_g_a6f40cea (a6f40cea).
    e84 = _load_module(
        arc_dir / "s3_g_a6f40cea.py", "s3_g_a6f40cea"
    )
    e84_replay = e84.train_replay(task)
    e84_fragment = e84.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e84_replay)
    if (
        e84_fragment is not None
        and e84_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e84_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_a6f40cea"
        receipt["train_replay"] = e84_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_a6f40cea_meta"] = e84_replay
        return e84_fragment, receipt

    # 1b85) s3_g_b10624e5 (b10624e5).
    e85 = _load_module(
        arc_dir / "s3_g_b10624e5.py", "s3_g_b10624e5"
    )
    e85_replay = e85.train_replay(task)
    e85_fragment = e85.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e85_replay)
    if (
        e85_fragment is not None
        and e85_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e85_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_b10624e5"
        receipt["train_replay"] = e85_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_b10624e5_meta"] = e85_replay
        return e85_fragment, receipt

    # 1b86) s3_g_b5ca7ac4 (b5ca7ac4).
    e86 = _load_module(
        arc_dir / "s3_g_b5ca7ac4.py", "s3_g_b5ca7ac4"
    )
    e86_replay = e86.train_replay(task)
    e86_fragment = e86.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e86_replay)
    if (
        e86_fragment is not None
        and e86_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e86_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_b5ca7ac4"
        receipt["train_replay"] = e86_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_b5ca7ac4_meta"] = e86_replay
        return e86_fragment, receipt

    # 1b87) s3_g_c4d067a0 (c4d067a0).
    e87 = _load_module(
        arc_dir / "s3_g_c4d067a0.py", "s3_g_c4d067a0"
    )
    e87_replay = e87.train_replay(task)
    e87_fragment = e87.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e87_replay)
    if (
        e87_fragment is not None
        and e87_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e87_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_c4d067a0"
        receipt["train_replay"] = e87_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_c4d067a0_meta"] = e87_replay
        return e87_fragment, receipt

    # 1b88) s3_g_cbebaa4b (cbebaa4b).
    e88 = _load_module(
        arc_dir / "s3_g_cbebaa4b.py", "s3_g_cbebaa4b"
    )
    e88_replay = e88.train_replay(task)
    e88_fragment = e88.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e88_replay)
    if (
        e88_fragment is not None
        and e88_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e88_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_cbebaa4b"
        receipt["train_replay"] = e88_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_cbebaa4b_meta"] = e88_replay
        return e88_fragment, receipt

    # 1b89) s3_g_d35bdbdc (d35bdbdc).
    e89 = _load_module(
        arc_dir / "s3_g_d35bdbdc.py", "s3_g_d35bdbdc"
    )
    e89_replay = e89.train_replay(task)
    e89_fragment = e89.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e89_replay)
    if (
        e89_fragment is not None
        and e89_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e89_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_d35bdbdc"
        receipt["train_replay"] = e89_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_d35bdbdc_meta"] = e89_replay
        return e89_fragment, receipt

    # 1b90) s3_g_d59b0160 (d59b0160).
    e90 = _load_module(
        arc_dir / "s3_g_d59b0160.py", "s3_g_d59b0160"
    )
    e90_replay = e90.train_replay(task)
    e90_fragment = e90.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e90_replay)
    if (
        e90_fragment is not None
        and e90_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e90_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_d59b0160"
        receipt["train_replay"] = e90_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_d59b0160_meta"] = e90_replay
        return e90_fragment, receipt

    # 1b91) s3_g_dbff022c (dbff022c).
    e91 = _load_module(
        arc_dir / "s3_g_dbff022c.py", "s3_g_dbff022c"
    )
    e91_replay = e91.train_replay(task)
    e91_fragment = e91.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e91_replay)
    if (
        e91_fragment is not None
        and e91_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e91_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_dbff022c"
        receipt["train_replay"] = e91_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_dbff022c_meta"] = e91_replay
        return e91_fragment, receipt

    # 1b92) s3_g_dd6b8c4b (dd6b8c4b).
    e92 = _load_module(
        arc_dir / "s3_g_dd6b8c4b.py", "s3_g_dd6b8c4b"
    )
    e92_replay = e92.train_replay(task)
    e92_fragment = e92.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e92_replay)
    if (
        e92_fragment is not None
        and e92_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e92_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_dd6b8c4b"
        receipt["train_replay"] = e92_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_dd6b8c4b_meta"] = e92_replay
        return e92_fragment, receipt

    # 1b93) s3_g_de809cff (de809cff).
    e93 = _load_module(
        arc_dir / "s3_g_de809cff.py", "s3_g_de809cff"
    )
    e93_replay = e93.train_replay(task)
    e93_fragment = e93.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e93_replay)
    if (
        e93_fragment is not None
        and e93_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e93_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_de809cff"
        receipt["train_replay"] = e93_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_de809cff_meta"] = e93_replay
        return e93_fragment, receipt

    # 1b94) s3_g_dfadab01 (dfadab01).
    e94 = _load_module(
        arc_dir / "s3_g_dfadab01.py", "s3_g_dfadab01"
    )
    e94_replay = e94.train_replay(task)
    e94_fragment = e94.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e94_replay)
    if (
        e94_fragment is not None
        and e94_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e94_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_dfadab01"
        receipt["train_replay"] = e94_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_dfadab01_meta"] = e94_replay
        return e94_fragment, receipt

    # 1b95) s3_g_e12f9a14 (e12f9a14).
    e95 = _load_module(
        arc_dir / "s3_g_e12f9a14.py", "s3_g_e12f9a14"
    )
    e95_replay = e95.train_replay(task)
    e95_fragment = e95.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e95_replay)
    if (
        e95_fragment is not None
        and e95_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e95_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_e12f9a14"
        receipt["train_replay"] = e95_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_e12f9a14_meta"] = e95_replay
        return e95_fragment, receipt

    # 1b96) s3_g_e3721c99 (e3721c99).
    e96 = _load_module(
        arc_dir / "s3_g_e3721c99.py", "s3_g_e3721c99"
    )
    e96_replay = e96.train_replay(task)
    e96_fragment = e96.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e96_replay)
    if (
        e96_fragment is not None
        and e96_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e96_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_e3721c99"
        receipt["train_replay"] = e96_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_e3721c99_meta"] = e96_replay
        return e96_fragment, receipt

    # 1b97) s3_g_e376de54 (e376de54).
    e97 = _load_module(
        arc_dir / "s3_g_e376de54.py", "s3_g_e376de54"
    )
    e97_replay = e97.train_replay(task)
    e97_fragment = e97.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e97_replay)
    if (
        e97_fragment is not None
        and e97_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e97_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_e376de54"
        receipt["train_replay"] = e97_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_e376de54_meta"] = e97_replay
        return e97_fragment, receipt

    # 1b98) s3_g_e87109e9 (e87109e9).
    e98 = _load_module(
        arc_dir / "s3_g_e87109e9.py", "s3_g_e87109e9"
    )
    e98_replay = e98.train_replay(task)
    e98_fragment = e98.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e98_replay)
    if (
        e98_fragment is not None
        and e98_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e98_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_e87109e9"
        receipt["train_replay"] = e98_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_e87109e9_meta"] = e98_replay
        return e98_fragment, receipt

    # 1b99) s3_g_eee78d87 (eee78d87).
    e99 = _load_module(
        arc_dir / "s3_g_eee78d87.py", "s3_g_eee78d87"
    )
    e99_replay = e99.train_replay(task)
    e99_fragment = e99.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e99_replay)
    if (
        e99_fragment is not None
        and e99_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e99_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_eee78d87"
        receipt["train_replay"] = e99_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_eee78d87_meta"] = e99_replay
        return e99_fragment, receipt

    # 1b100) s3_g_fc7cae8d (fc7cae8d).
    e100 = _load_module(
        arc_dir / "s3_g_fc7cae8d.py", "s3_g_fc7cae8d"
    )
    e100_replay = e100.train_replay(task)
    e100_fragment = e100.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e100_replay)
    if (
        e100_fragment is not None
        and e100_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e100_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_fc7cae8d"
        receipt["train_replay"] = e100_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_fc7cae8d_meta"] = e100_replay
        return e100_fragment, receipt

    # 1b101) s3_g_edb79dae (edb79dae).
    e101 = _load_module(
        arc_dir / "s3_g_edb79dae.py", "s3_g_edb79dae"
    )
    e101_replay = e101.train_replay(task)
    e101_fragment = e101.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e101_replay)
    if (
        e101_fragment is not None
        and e101_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e101_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_edb79dae"
        receipt["train_replay"] = e101_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_edb79dae_meta"] = e101_replay
        return e101_fragment, receipt

    # 1b102) s3_g_f931b4a8 (f931b4a8).
    e102 = _load_module(
        arc_dir / "s3_g_f931b4a8.py", "s3_g_f931b4a8"
    )
    e102_replay = e102.train_replay(task)
    e102_fragment = e102.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e102_replay)
    if (
        e102_fragment is not None
        and e102_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e102_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_f931b4a8"
        receipt["train_replay"] = e102_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_f931b4a8_meta"] = e102_replay
        return e102_fragment, receipt

    # 1b103) s3_g_9385bd28 (9385bd28).
    e103 = _load_module(
        arc_dir / "s3_g_9385bd28.py", "s3_g_9385bd28"
    )
    e103_replay = e103.train_replay(task)
    e103_fragment = e103.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e103_replay)
    if (
        e103_fragment is not None
        and e103_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e103_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_9385bd28"
        receipt["train_replay"] = e103_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_9385bd28_meta"] = e103_replay
        return e103_fragment, receipt

    # 1b104) s3_g_b6f77b65 (b6f77b65).
    e104 = _load_module(
        arc_dir / "s3_g_b6f77b65.py", "s3_g_b6f77b65"
    )
    e104_replay = e104.train_replay(task)
    e104_fragment = e104.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e104_replay)
    if (
        e104_fragment is not None
        and e104_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e104_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_b6f77b65"
        receipt["train_replay"] = e104_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_b6f77b65_meta"] = e104_replay
        return e104_fragment, receipt

    # 1b105) s3_g_b9e38dc0 (b9e38dc0).
    e105 = _load_module(
        arc_dir / "s3_g_b9e38dc0.py", "s3_g_b9e38dc0"
    )
    e105_replay = e105.train_replay(task)
    e105_fragment = e105.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e105_replay)
    if (
        e105_fragment is not None
        and e105_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e105_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_b9e38dc0"
        receipt["train_replay"] = e105_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_b9e38dc0_meta"] = e105_replay
        return e105_fragment, receipt

    # 1b106) s3_g_c7f57c3e (c7f57c3e).
    e106 = _load_module(
        arc_dir / "s3_g_c7f57c3e.py", "s3_g_c7f57c3e"
    )
    e106_replay = e106.train_replay(task)
    e106_fragment = e106.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e106_replay)
    if (
        e106_fragment is not None
        and e106_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e106_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_c7f57c3e"
        receipt["train_replay"] = e106_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_c7f57c3e_meta"] = e106_replay
        return e106_fragment, receipt

    # 1b107) s3_g_cb2d8a2c (cb2d8a2c).
    e107 = _load_module(
        arc_dir / "s3_g_cb2d8a2c.py", "s3_g_cb2d8a2c"
    )
    e107_replay = e107.train_replay(task)
    e107_fragment = e107.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e107_replay)
    if (
        e107_fragment is not None
        and e107_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e107_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_cb2d8a2c"
        receipt["train_replay"] = e107_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_cb2d8a2c_meta"] = e107_replay
        return e107_fragment, receipt

    # 1b108) s3_g_da515329 (da515329).
    e108 = _load_module(
        arc_dir / "s3_g_da515329.py", "s3_g_da515329"
    )
    e108_replay = e108.train_replay(task)
    e108_fragment = e108.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e108_replay)
    if (
        e108_fragment is not None
        and e108_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e108_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_da515329"
        receipt["train_replay"] = e108_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_da515329_meta"] = e108_replay
        return e108_fragment, receipt





    # 1b97) s2_encoded_template_stamp (abc82100).
    abceng = _load_module(
        arc_dir / "s2_encoded_template_stamp.py", "s2_encoded_template_stamp"
    )
    abc_replay = abceng.train_replay(task)
    abc_fragment = abceng.submission_fragment(task_id, task)
    receipt["engines_tried"].append(abc_replay)
    if (
        abc_fragment is not None
        and abc_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in abc_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_encoded_template_stamp"
        receipt["train_replay"] = abc_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_encoded_template_stamp_meta"] = abc_replay
        return abc_fragment, receipt

    # 1b98) s1_g_f560132c (f560132c).
    f560eng = _load_module(
        arc_dir / "s1_g_f560132c.py", "s1_g_f560132c"
    )
    f560_replay = f560eng.train_replay(task)
    f560_fragment = f560eng.submission_fragment(task_id, task)
    receipt["engines_tried"].append(f560_replay)
    if (
        f560_fragment is not None
        and f560_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in f560_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s1_g_f560132c"
        receipt["train_replay"] = f560_replay["train_replay"]
        receipt["ok"] = True
        receipt["s1_g_f560132c_meta"] = f560_replay
        return f560_fragment, receipt

    # 1b99) s2_g_d8e07eb2 (d8e07eb2).
    d8eng = _load_module(
        arc_dir / "s2_g_d8e07eb2.py", "s2_g_d8e07eb2"
    )
    d8_replay = d8eng.train_replay(task)
    d8_fragment = d8eng.submission_fragment(task_id, task)
    receipt["engines_tried"].append(d8_replay)
    if (
        d8_fragment is not None
        and d8_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in d8_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s2_g_d8e07eb2"
        receipt["train_replay"] = d8_replay["train_replay"]
        receipt["ok"] = True
        receipt["s2_g_d8e07eb2_meta"] = d8_replay
        return d8_fragment, receipt


    # 1b109) s3_g_d8e07eb2 (d8e07eb2).
    e109 = _load_module(
        arc_dir / "s3_g_d8e07eb2.py", "s3_g_d8e07eb2"
    )
    e109_replay = e109.train_replay(task)
    e109_fragment = e109.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e109_replay)
    if (
        e109_fragment is not None
        and e109_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e109_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_d8e07eb2"
        receipt["train_replay"] = e109_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_d8e07eb2_meta"] = e109_replay
        return e109_fragment, receipt


    # 1b110) s3_g_faa9f03d (faa9f03d).
    e110 = _load_module(
        arc_dir / "s3_g_faa9f03d.py", "s3_g_faa9f03d"
    )
    e110_replay = e110.train_replay(task)
    e110_fragment = e110.submission_fragment(task_id, task)
    receipt["engines_tried"].append(e110_replay)
    if (
        e110_fragment is not None
        and e110_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in e110_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_g_faa9f03d"
        receipt["train_replay"] = e110_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_g_faa9f03d_meta"] = e110_replay
        return e110_fragment, receipt

    # 1c) Container period tiling (135a2760; stacked panels / color-3 columns).
    cpt = _load_module(
        arc_dir / "container_period_tiling.py", "container_period_tiling"
    )
    cpt_replay = cpt.train_replay(task)
    cpt_fragment = cpt.submission_fragment(task_id, task)
    receipt["engines_tried"].append(cpt_replay)
    if (
        cpt_fragment is not None
        and cpt_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in cpt_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "container_period_tiling"
        receipt["train_replay"] = cpt_replay["train_replay"]
        receipt["ok"] = True
        receipt["cpt_meta"] = cpt_replay
        return cpt_fragment, receipt

    # 1d) S3 separator ray-fill (1ae2feb7; vertical sep + motif rays).
    s3 = _load_module(arc_dir / "s3_separator_ray_fill.py", "s3_separator_ray_fill")
    s3_replay = s3.train_replay(task)
    s3_fragment = s3.submission_fragment(task_id, task)
    receipt["engines_tried"].append(s3_replay)
    if (
        s3_fragment is not None
        and s3_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in s3_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_separator_ray_fill"
        receipt["train_replay"] = s3_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_meta"] = s3_replay
        return s3_fragment, receipt

    # 1e) S3 period-lattice rewrite (16de56c4).
    s3lat = _load_module(
        arc_dir / "s3_period_lattice_rewrite.py", "s3_period_lattice_rewrite"
    )
    lat_replay = s3lat.train_replay(task)
    lat_fragment = s3lat.submission_fragment(task_id, task)
    receipt["engines_tried"].append(lat_replay)
    if (
        lat_fragment is not None
        and lat_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in lat_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_period_lattice_rewrite"
        receipt["train_replay"] = lat_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_lattice_meta"] = lat_replay
        return lat_fragment, receipt

    # 1f) S3 terrain period-bounce (195c6913).
    s3bounce = _load_module(
        arc_dir / "s3_terrain_period_bounce.py", "s3_terrain_period_bounce"
    )
    bounce_replay = s3bounce.train_replay(task)
    bounce_fragment = s3bounce.submission_fragment(task_id, task)
    receipt["engines_tried"].append(bounce_replay)
    if (
        bounce_fragment is not None
        and bounce_replay.get("perfect")
        and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in bounce_fragment[task_id]
        )
    ):
        receipt["accepted_engine"] = "s3_terrain_period_bounce"
        receipt["train_replay"] = bounce_replay["train_replay"]
        receipt["ok"] = True
        receipt["s3_bounce_meta"] = bounce_replay
        return bounce_fragment, receipt

    # 2) Replay-gated DSL (db71c28 lineage).
    dsl_path = repo_root / "kaggle/arc-prize-2026-agi-2/arc_agi_2_kaggle.py"
    try:
        dsl = _load_module(dsl_path, "arc_agi_2_dsl_local")
        dsl_meta = _dsl_train_replay(dsl, task["train"])
        receipt["engines_tried"].append(dsl_meta)
        if dsl_meta["ok"]:
            attempts = [dsl.predictions(task, case["input"]) for case in task["test"]]
            if all(
                _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
                for p in attempts
            ):
                receipt["accepted_engine"] = "replay_gated_dsl"
                receipt["train_replay"] = dsl_meta["train_replay"]
                receipt["ok"] = True
                return {task_id: attempts}, receipt
    except Exception as exc:
        receipt["engines_tried"].append(
            {"engine": "replay_gated_dsl", "ok": False, "error": str(exc)}
        )

    # 3) Icecuber only with full train-replay license.
    ice_path = arc_dir / "icecuber_adapter.py"
    try:
        ice = _load_module(ice_path, "arc_icecuber_adapter_local")
        ice_attempts, ice_meta = _icecuber_train_replay(ice, repo_root, task_id, task)
        receipt["engines_tried"].append(ice_meta)
        if ice_attempts is not None and all(
            _valid_grid(p["attempt_1"]) and _valid_grid(p["attempt_2"])
            for p in ice_attempts
        ):
            receipt["accepted_engine"] = "arc-icecuber"
            receipt["train_replay"] = ice_meta["train_replay"]
            receipt["ok"] = True
            return {task_id: ice_attempts}, receipt
    except Exception as exc:
        receipt["engines_tried"].append(
            {"engine": "arc-icecuber", "ok": False, "error": str(exc)}
        )

    receipt["error"] = "no engine achieved full train-replay; refusing unvalidated guess"
    return None, receipt


def fragment_json(fragment: Dict[str, Any]) -> str:
    return json.dumps(fragment, separators=(",", ":"), sort_keys=True)
