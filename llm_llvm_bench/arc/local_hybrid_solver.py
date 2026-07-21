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
