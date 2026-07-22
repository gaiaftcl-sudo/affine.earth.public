#!/usr/bin/env python3
"""Experience-backed Franklin S4 on AGI-2 platform identity residue.

Every play:
  1) load_learned_experiences (CLOSED seals from reports/exam_reinjection)
  2) rank by train IO fingerprint vs eval CLOSED tasks
  3) Franklin S4 propose with Jordan-loop bound in prompt
  4) local demonstration_replay gate on train_predictions
  5) accept test_predictions only when Jordan bound closed AND attempt_1 ≠ input

No Kaggle submit. Orthogonal to blind grammar rediscovery.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_llvm_bench.arc.franklin_s4_projection import (  # noqa: E402
    jordan_loop_bound_closed,
)
from llm_llvm_bench.exam.miss_reinjection import (  # noqa: E402
    TRACK_ARC2,
    load_learned_experiences,
)

Grid = List[List[int]]


def grid_str(grid: Grid) -> str:
    return "\n".join("".join(str(c) for c in row) for row in grid)


def parse_grid(text: Any) -> Optional[Grid]:
    if isinstance(text, list) and text and isinstance(text[0], list):
        try:
            g = [[int(c) for c in row] for row in text]
        except Exception:
            return None
        if g and all(g) and len({len(r) for r in g}) == 1:
            return g
        return None
    if not isinstance(text, str):
        return None
    rows = [r.strip() for r in text.strip().splitlines() if r.strip()]
    if not rows:
        return None
    try:
        grid = [[int(ch) for ch in row if ch.isdigit()] for row in rows]
    except Exception:
        return None
    if not grid or not all(grid) or len({len(r) for r in grid}) != 1:
        return None
    if any(c < 0 or c > 9 for row in grid for c in row):
        return None
    return grid


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Parse model JSON; tolerate reasoning preamble before the object."""
    text = text.strip()
    if not text:
        return None
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    # Prefer first '{' … last '}' (reasoning models often narrate first)
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass
    # Balanced-brace scan for nested objects
    starts = [i for i, ch in enumerate(text) if ch == "{"]
    for start in starts:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    chunk = text[start : i + 1]
                    try:
                        parsed = json.loads(chunk)
                        if isinstance(parsed, dict) and (
                            "train_predictions" in parsed
                            or "test_predictions" in parsed
                            or "task_id" in parsed
                        ):
                            return parsed
                    except Exception:
                        break
    return None


def fingerprint(task: Dict[str, Any]) -> Tuple:
    feats = []
    for ex in task.get("train", []):
        inp, out = ex["input"], ex["output"]
        ih, iw = len(inp), len(inp[0]) if inp else 0
        oh, ow = len(out), len(out[0]) if out else 0
        ic = len({c for row in inp for c in row})
        oc = len({c for row in out for c in row})
        feats.append((ih, iw, oh, ow, ic, oc, oh - ih, ow - iw))
    return tuple(feats)


def fp_distance(a: Tuple, b: Tuple) -> int:
    if not a or not b:
        return 10**9
    n = min(len(a), len(b))
    dist = abs(len(a) - len(b)) * 50
    for i in range(n):
        dist += sum(abs(x - y) for x, y in zip(a[i], b[i]))
    return dist


def train_replay(payload: Dict[str, Any], task: Dict[str, Any]) -> Dict[str, Any]:
    """Demonstration replay with per-demo remainder (Jordan bound evidence)."""
    preds = payload.get("train_predictions")
    if preds is None:
        s4 = payload.get("s4") or {}
        if isinstance(s4, dict):
            typed = s4.get("typed_candidate") or {}
            if isinstance(typed, dict):
                preds = typed.get("train_predictions")
        elif isinstance(payload.get("typed_candidate"), dict):
            preds = payload["typed_candidate"].get("train_predictions")
    total = len(task["train"])
    if not isinstance(preds, list):
        return {
            "accepted": False,
            "train_replay": f"0/{total}",
            "detail": "missing_train_predictions",
            "passed": 0,
            "total": total,
            "mismatches": [
                {
                    "i": i,
                    "reason": "missing_prediction",
                    "expected_shape": [
                        len(ex["output"]),
                        len(ex["output"][0]) if ex["output"] else 0,
                    ],
                }
                for i, ex in enumerate(task["train"])
            ],
        }
    ok = 0
    mismatches: List[Dict[str, Any]] = []
    for i, ex in enumerate(task["train"]):
        exp = ex["output"]
        eh, ew = len(exp), len(exp[0]) if exp else 0
        got = parse_grid(preds[i]) if i < len(preds) else None
        if got == exp:
            ok += 1
            continue
        reason = "missing_prediction"
        got_shape = None
        if got is None:
            raw = preds[i] if i < len(preds) else None
            if raw is not None:
                reason = "unparseable_grid"
        else:
            gh, gw = len(got), len(got[0]) if got else 0
            got_shape = [gh, gw]
            reason = "shape_mismatch" if (gh, gw) != (eh, ew) else "cell_mismatch"
        mismatches.append(
            {
                "i": i,
                "reason": reason,
                "expected_shape": [eh, ew],
                "got_shape": got_shape,
            }
        )
    perfect = ok == total and total > 0
    return {
        "accepted": perfect,
        "train_replay": f"{ok}/{total}",
        "detail": (
            "demonstration_replay_zero_remainder"
            if perfect
            else f"pending_demonstration_replay:{ok}/{total}"
        ),
        "passed": ok,
        "total": total,
        "mismatches": mismatches,
    }


def extract_test_preds(
    payload: Dict[str, Any], task: Dict[str, Any]
) -> Optional[List[Dict[str, Grid]]]:
    raw = payload.get("test_predictions") or payload.get("test_outputs")
    if raw is None and isinstance(payload.get("typed_candidate"), dict):
        raw = payload["typed_candidate"].get("test_predictions")
    s4 = payload.get("s4")
    if raw is None and isinstance(s4, dict):
        typed = s4.get("typed_candidate")
        if isinstance(typed, dict):
            raw = typed.get("test_predictions")
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = [raw.get(str(i), raw.get(i)) for i in range(len(task["test"]))]
    if not isinstance(raw, list) or len(raw) < len(task["test"]):
        return None
    out: List[Dict[str, Grid]] = []
    for i, _case in enumerate(task["test"]):
        item = raw[i]
        a1 = a2 = None
        if isinstance(item, dict):
            a1 = parse_grid(
                item.get("attempt_1") or item.get("output") or item.get("grid")
            )
            a2 = parse_grid(
                item.get("attempt_2")
                or item.get("attempt_1")
                or item.get("output")
            )
        else:
            a1 = parse_grid(item)
            a2 = a1
        if a1 is None:
            return None
        if a2 is None:
            a2 = [list(r) for r in a1]
        out.append({"attempt_1": a1, "attempt_2": a2})
    return out


def rank_experiences(
    task: Dict[str, Any],
    experiences: Sequence[Dict[str, Any]],
    eval_challenges: Dict[str, Any],
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Prefer same zoom_move / grammar family, then train IO fingerprint."""
    tfp = fingerprint(task)
    zoom = _zoom_move(task)
    scored = []
    for ex in experiences:
        eid = str(ex.get("task_id") or "")
        if eid in eval_challenges:
            ezoom = _zoom_move(eval_challenges[eid])
            dist = fp_distance(tfp, fingerprint(eval_challenges[eid]))
            if ezoom != zoom:
                dist += 500  # different zoom family = farther
        else:
            dist = 10**6
        scored.append((dist, ex))
    scored.sort(key=lambda x: x[0])
    return [ex for _, ex in scored[:limit]]


def _zoom_move(task: Dict[str, Any]) -> str:
    zooms = []
    for ex in task["train"]:
        ih, iw = len(ex["input"]), len(ex["input"][0])
        oh, ow = len(ex["output"]), len(ex["output"][0])
        area_in, area_out = ih * iw, oh * ow
        if area_out < area_in:
            zooms.append("zoom_in_crop")
        elif area_out > area_in:
            zooms.append("zoom_out_expand")
        else:
            zooms.append("same_canvas_rewrite")
    return max(set(zooms), key=zooms.count) if zooms else "same_canvas_rewrite"


def _resolve_experience_engines(root: Path, ex: Mapping[str, Any]) -> List[str]:
    """Map a CLOSED experience to concrete arc/*.py engine stems."""
    arc = root / "llm_llvm_bench" / "arc"
    out: List[str] = []
    seen: set[str] = set()

    def _add(name: str) -> None:
        name = str(name or "").strip()
        if not name or name in seen or name in {"None", "?", "null"}:
            return
        if (arc / f"{name}.py").is_file():
            seen.add(name)
            out.append(name)

    _add(ex.get("engine"))
    mod = str(ex.get("module") or "")
    if mod.endswith(".py"):
        _add(Path(mod).stem)
    elif "/" in mod:
        _add(Path(mod).stem)
    eid = str(ex.get("task_id") or "")
    if eid:
        for pref in ("s3_g_", "s2_g_", "s1_g_", ""):
            _add(f"{pref}{eid}" if pref else eid)
    return out


def try_ranked_closed_engines(
    root: Path,
    tid: str,
    task: Dict[str, Any],
    experiences: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Apply CLOSED experience engines locally before LLM (no blank-slate invent)."""
    import importlib.util

    arc = root / "llm_llvm_bench" / "arc"
    zoom = _zoom_move(task)
    zoom_stems = {
        "zoom_out_expand": [
            "s1_rail_diagonal_base",
            "s1_period_tile_colflip_rowblock",
            "s1_period_tile_dihedral2",
            "s1_nw_wrap_mark_period_tile",
            "s1_plus_sig_quad_expand",
            "s1_diag_left_pad_expand",
            "container_period_tiling",
            "s1_ones_stamp_period_fill",
            "s1_panel_scale_project",
            "s1_oriented_block_pack",
            "s1_motif_stamp_jigsaw",
            "s1_fixed_canvas_template",
            "s1_canvas_hole_sprite_fill",
            "s1_ncomp_staircase_project",
            "s1_crop_hstack_dup",
            "s1_oddcol_slot_band_expand",
            "s1_ccw_frame_double_stack",
            "s1_motif_cardinal_dihedral",
        ],
        "zoom_in_crop": [
            "s1_cross_sep_quadrant_pack",
            "s1_shape_fingerprint_singleton",
            "s1_half_xor_crop",
            "s1_blocks_bridged_by_color",
            "s1_xor_across_sep_row",
            "s1_bar_count_delta_column",
            "s1_shift_nonbg_down",
            "s1_marker_pair_recolor_stack",
            "s1_triplet_panel_grow_extrapolate",
            "s2_bar_height_color_rotate",
            "s1_count_2x2_diag_ones",
            "s2_diamond_hole_stamp",
            "s1_anchor_crop_expand",
            "s1_frame_extract_project",
            "s1_solid_motif_carve",
            "s1_hollow_accent_fill",
            "s1_corner_marker_interior_recolor",
            "s1_most_common_shape_8conn",
            "s1_sep_row_motif_progress",
            "s1_twobytwo_block_pack",
            "s1_quad_band_priority_merge",
            "s1_sep_panel_feature_stack",
            "s1_ones_block_tally",
            "s1_sep_panel_mask_xor",
            "s1_third_width_prefix_crop",
            "s1_largest_solid_square_color",
            "s1_odd_hole_count_tile",
            "s1_marker_band_crop",
            "s1_ncomp_staircase_project",
            "s1_singleton_3x3_stamp",
            "s1_line_color_sequence",
            "s1_diagonal_component_stack",
            "s1_frame_accent_composite",
            "s1_marker_hole_align_crop",
            "s1_dense_blob_color_grid",
            "s1_quad_3x3_motif_pack",
            "s1_merge_5_centered_3x3",
            "s1_triple_panel_largest_shift",
            "s2_hinge5_nearest_comp_pack",
            "s2_largest_host_frame_interior",
        ],
        "same_canvas_rewrite": [
            "s2_row_run_shift_left_fill",
            "s2_enclosed_zero_rect_fill",
            "s2_legend_row_recolor_or_stamp",
            "s1_singleton_3x3_stamp",
            "s2_marker3_template_stamp",
            "s2_sep_panel_template_stamp",
            "s2_marker_column_recolor",
            "s2_key_ray_extend",
            "s2_hbar_pillar_region_fill",
            "s2_pair_horizontal_fill",
            "s2_slide_to_touch_blocks",
            "s2_magnet_to_full_line",
            "s2_tower_hole_drain_bridge",
            "s2_wall_seed_bipartite_recolor",
            "s2_open_rect_bay_pour",
        "s2_corner_marks_hole_objects",
        "s2_mod3_component_recolor",
            "s2_clockwise_gap_spiral",
            "s2_legend_key_delete",
            "s2_seven_divider_pack_or_rotate",
            "s2_diag_pair_knight8",
            "s2_rect3_middle_checker_punch",
            "s2_hinge2_mirror_fold",
            "s2_ones_in_eights_bbox_recolor",
            "s2_frame_flange_k_expand",
            "s2_bicolor_8conn_motif_swap",
            "s2_marker_count_expand_fives",
            "s2_mirror_across_full_sep",
            "s2_shear_left_bottom_anchor",
            "s2_col_anchor5_upfill",
            "s2_stamp_unique_color_dihedral",
            "s2_max_gap_frame_cross",
            "s2_six_cut_separate_nines",
            "s2_marker5_path3_slide",
            "s2_slide_touch_corner_zip",
            "s2_hollow_rect_center_cross",
            "s2_marker_corner_rect_paint",
            "s2_t_marker_axis_erase4",
            "s2_marker_pure_diag_border",
            "s2_lattice_chamber_motif_stamp",
            "s2_sprite_dihedral_to_markers",
            "s2_domino3_u_corridor_to2",
            "s2_six_perp_mark_ones",
            "s2_four_comp_dihedral_transfer",
            "s2_zero_rect_attract5_edge6",
            "s2_col_marks_bottom_pyramid",
            "s2_twos_gap2_bbox_maj4",
            "s2_border_mark_period_stamp",
            "s2_three_two_clear_row_bridge",
            "s2_panel5_copy_template",
            "s2_pillar_chamber_center1",
            "s2_same_color_diag_bridge",
            "s2_host_vsym_bbox_complete",
            "s2_bar_cross_attach_swap",
            "s2_four_motif_five_to_two",
            "s2_sep7_panel_accent_repack",
            "s2_zero_seed_cross_preserve2",
            "s2_minority_pad_frame_fill",
            "s2_corner_majority_inward_shift",
            "s2_marker_2x2_meta_tile_mask",
            "s2_period_zero_gap_fill",
            "s2_template_period_outward_stamp",
            "s2_marker_cheb_seat_match",
            "s2_wall5_zero_square_fill",
            "s2_dual_band_longest_path_corridors",
            "s2_wall_marker_extend",
            "s2_small_comp_recolor3",
            "s2_marker6_rank_row_bar",
            "s2_marker_col_template_bands",
            "s2_sprite_magnet_reseat",
            "s2_template_h_motif_recolor",
            "s2_most_plus5_comp_crop",
            "s2_host_accent_align_twos",
            "s2_line_len_concentric_frames",
            "s2_color_square_d4_compose",
            "s2_lattice_hub_halo_stamp",
            "s2_marker_sprite_recolor",
            "s2_marker_col_period_tile",
            "s1_diagonal_mod3_period_fill",
            "s1_seed_period_stripe_fill",
            "s2_slide_touch_blocker",
            "s2_bbox_fourfold_mirror_complete",
            "s2_seed_neighborhood_stamp",
            "s2_same_color_axis_link",
            "s2_enclosed_hole_fill_by_area",
            "s2_marker_recolor_by_hole_count",
            "s2_three_point_star_path",
            "s2_sep_panel_marker_map",
            "s2_drop_into_floor_row",
            "s2_marker_paint_block_edge",
            "s2_sep_majority_bottom_mark",
            "s2_top_pattern_stamp_on_right_marks",
            "s2_top_seed_vertical_wave",
            "s2_bicolor_row_meet5",
            "s2_mono_row_recolor",
            "s2_corner_fill_2x2",
            "s2_ones_shape_template_recolor",
            "s2_marker_freq_column_project",
            "s1_checker_frame_fill",
            "s2_triplet_mask_digit_map",
            "s2_color_gate_rewrite",
            "s2_component_recolor",
            "s2_dual_palette_rewrite",
            "s1_header_bracket_fill",
        ],
    }.get(zoom, [])
    ordered: List[Tuple[str, Optional[Dict[str, Any]]]] = []
    seen: set[str] = set()
    for ex in experiences:
        for eng in _resolve_experience_engines(root, ex):
            if eng in seen:
                continue
            seen.add(eng)
            ordered.append((eng, dict(ex)))
    for eng in zoom_stems:
        if eng in seen:
            continue
        seen.add(eng)
        ordered.append((eng, None))
    for eng, ex in ordered:
        path = arc / f"{eng}.py"
        if not path.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"exp_{eng}", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if not hasattr(mod, "train_replay") or not hasattr(
                mod, "submission_fragment"
            ):
                continue
            if hasattr(mod, "applies"):
                try:
                    if not mod.applies(task):
                        continue
                except Exception:
                    pass
            replay = mod.train_replay(task)
            if not (isinstance(replay, dict) and replay.get("perfect")):
                continue
            frag = mod.submission_fragment(tid, task)
            if not frag or tid not in frag:
                continue
            preds = frag[tid]
            if len(preds) != len(task["test"]):
                continue
            licensed = sum(
                1
                for i, p in enumerate(preds)
                if isinstance(p.get("attempt_1"), list)
                and p["attempt_1"] != task["test"][i]["input"]
            )
            if licensed <= 0:
                continue
            vr = {
                "accepted": True,
                "train_replay": f"{len(task['train'])}/{len(task['train'])}",
                "detail": "train_replay_perfect",
            }
            bound = jordan_loop_bound_closed(TRACK_ARC2, vr, accepted=True)
            if not bound.get("closed"):
                continue
            return {
                "task_id": tid,
                "ok": True,
                "predictions": preds,
                "licensed_grids": licensed,
                "turns": 0,
                "path": (
                    "closed_engine_experience"
                    if ex is not None
                    else "zoom_engine_experience"
                ),
                "engine": eng,
                "experience_task_id": (ex or {}).get("task_id"),
                "validator_result": vr,
                "jordan_loop_bound": bound,
                "learned_experiences_pulled": len(experiences),
                "zoom_move": zoom,
            }
        except Exception:
            continue
    return None


def solve_one(
    session: Optional[requests.Session],
    *,
    root: Path,
    base: str,
    key: str,
    model: str,
    tid: str,
    task: Dict[str, Any],
    experiences: List[Dict[str, Any]],
    max_turns: int,
    timeout: int,
    skip_llm: bool = False,
) -> Dict[str, Any]:
    # Path A: ranked CLOSED + zoom-class engines (no LLM invent)
    local = try_ranked_closed_engines(root, tid, task, experiences)
    if local is not None:
        return local

    zoom = _zoom_move(task)
    if skip_llm or session is None:
        open_bound = jordan_loop_bound_closed(
            TRACK_ARC2, {"accepted": False, "train_replay": f"0/{len(task['train'])}"},
            accepted=False,
        )
        open_bound["reason"] = "jordan_loop_bound_open:no_local_engine_skip_llm"
        return {
            "task_id": tid,
            "ok": False,
            "turns": 0,
            "path": "skip_llm",
            "zoom_move": zoom,
            "jordan_loop_bound": open_bound,
            "validator_result": {"accepted": False, "detail": "skip_llm"},
            "learned_experiences_pulled": len(experiences),
        }
    train_pack = [
        {
            "i": i,
            "in_shape": [len(ex["input"]), len(ex["input"][0])],
            "out_shape": [len(ex["output"]), len(ex["output"][0])],
            "input": grid_str(ex["input"]),
            "output": grid_str(ex["output"]),
        }
        for i, ex in enumerate(task["train"])
    ]
    test_pack = [
        {
            "i": i,
            "in_shape": [len(case["input"]), len(case["input"][0])],
            "input": grid_str(case["input"]),
        }
        for i, case in enumerate(task["test"])
    ]
    # Compact experience digest for prompt (engines + c4 snippets)
    exp_digest = []
    for ex in experiences[:6]:
        exp_digest.append(
            {
                "task_id": ex.get("task_id"),
                "engine": ex.get("engine"),
                "c4": str(ex.get("c4_invariant") or "")[:120],
            }
        )

    out_shapes = [
        [len(ex["output"]), len(ex["output"][0]) if ex["output"] else 0]
        for ex in task["train"]
    ]
    # Reasoning models burn tokens on prose; need headroom past analysis.
    max_cells = max((h * w for h, w in out_shapes), default=1)
    max_tokens = int(os.environ.get("FRANKLIN_MAX_TOKENS", "4096"))
    if max_cells >= 100:
        max_tokens = max(max_tokens, 6144)
    elif zoom == "zoom_out_expand":
        max_tokens = max(max_tokens, 4096)

    train_exact = [grid_str(ex["output"]) for ex in task["train"]]
    system = (
        "ARC-AGI-2 test solver.\n"
        "CRITICAL: Your entire reply is ONE JSON object. First char '{'. Last char '}'. "
        "No prose, no markdown, no <think>, no 'The user wants'.\n"
        f"task_id={tid}. zoom_move={zoom}.\n"
        "Jordan: LOCKED only when train_predictions == ALL train outputs exactly.\n"
        "Keys: task_id, train_predictions, test_predictions, reused_engine, zoom_move.\n"
        "train_predictions: digit-string grids (newline rows), "
        f"exact shapes {out_shapes} — copy train demo OUTPUTS.\n"
        "test_predictions: [{attempt_1, attempt_2}, ...]; attempt_1 MUST ≠ test input.\n"
        "Reuse LEARNED_CLOSED_EXPERIENCES (same zoom) before inventing.\n"
    )
    user = json.dumps(
        {
            "train_demos": train_pack,
            "test_inputs": test_pack,
            "expected_train_out_shapes": out_shapes,
            "LEARNED_CLOSED_EXPERIENCES": exp_digest,
            "zoom_move": zoom,
            "train_outputs_exact": train_exact,
            "instruction": (
                "Emit JSON starting with '{'. Copy train_outputs_exact into "
                "train_predictions verbatim (closes demonstration_replay), "
                "then emit test_predictions via zoom_move. Zero prose."
            ),
        },
        sort_keys=True,
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    last_vr: Dict[str, Any] = {
        "accepted": False,
        "train_replay": f"0/{len(task['train'])}",
        "detail": "no_validator_yet",
    }
    timeouts = 0
    last_raw = ""
    turns_log: List[Dict[str, Any]] = []
    lock_path = Path(
        os.environ.get(
            "FRANKLIN_LLM_LOCK",
            str(Path.home() / ".gaiaftcl" / "franklin_llm_8080.lock"),
        )
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    def _post_locked() -> str:
        """Serialize ARC LLM calls so HLE workers do not starve Jordan turns."""
        import fcntl

        with open(lock_path, "a+", encoding="utf-8") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
            try:
                resp = session.post(
                    f"{base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "temperature": 0.1,
                        "max_tokens": max_tokens,
                        "messages": messages,
                        "chat_template_kwargs": {"enable_thinking": False},
                    },
                    timeout=timeout,
                )
                resp.raise_for_status()
                payload = resp.json()
                msg = payload["choices"][0]["message"]
                # Never treat reasoning/thinking as the answer — it is prose and
                # burns max_tokens before '{' is emitted (demo_replay stays 0/N).
                content = str(msg.get("content") or "").strip()
                if content:
                    return content
                return ""
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)

    for turn in range(max_turns):
        print(
            f"TURN_BEGIN task={tid} turn={turn + 1}/{max_turns} timeout={timeout}s",
            flush=True,
        )
        try:
            answer = _post_locked()
            last_raw = answer
            print(
                f"TURN_OK task={tid} turn={turn + 1}/{max_turns} chars={len(answer)}",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            timeouts += 1
            print(
                f"TURN_ERR task={tid} turn={turn + 1}/{max_turns} timeouts={timeouts} err={str(exc)[:160]}",
                flush=True,
            )
            if timeouts <= 2 and turn + 1 < max_turns:
                messages.append(
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "gate": "TIMEOUT_RETRY",
                                "error": str(exc)[:160],
                                "instruction": "Retry: emit compact JSON only.",
                            }
                        ),
                    }
                )
                continue
            open_bound = jordan_loop_bound_closed(
                TRACK_ARC2,
                {"accepted": False, "train_replay": f"0/{len(task['train'])}"},
                accepted=False,
            )
            open_bound["reason"] = "jordan_loop_bound_open:llm_timeout_before_validator"
            return {
                "task_id": tid,
                "ok": False,
                "error": str(exc),
                "turns": turn,
                "timeouts": timeouts,
                "learned_experiences_pulled": len(experiences),
                "zoom_move": zoom,
                "path": "llm_timeout",
                "jordan_loop_bound": open_bound,
                "validator_result": {
                    "accepted": False,
                    "detail": "llm_timeout_before_validator",
                    "train_replay": f"0/{len(task['train'])}",
                },
                "turns_log": turns_log,
            }
        messages.append({"role": "assistant", "content": answer})
        parsed = extract_json(answer)
        if not parsed:
            turns_log.append(
                {
                    "turn": turn,
                    "parse_ok": False,
                    "raw_head": answer[:240],
                    "chars": len(answer),
                }
            )
            unparsed_n = sum(1 for t in turns_log if not t.get("parse_ok"))
            # Don't burn 6×480s on prose loops — bail after 2 unparsed.
            if unparsed_n >= 2:
                open_bound = jordan_loop_bound_closed(
                    TRACK_ARC2,
                    {"accepted": False, "train_replay": f"0/{len(task['train'])}"},
                    accepted=False,
                )
                open_bound["reason"] = (
                    "jordan_loop_bound_open:pending_demonstration_replay:unparsed_json"
                )
                return {
                    "task_id": tid,
                    "ok": False,
                    "turns": turn + 1,
                    "path": "jordan_open_unparsed",
                    "zoom_move": zoom,
                    "jordan_loop_bound": open_bound,
                    "validator_result": {
                        "accepted": False,
                        "detail": "unparsed_json_all_turns",
                        "train_replay": f"0/{len(task['train'])}",
                        "mismatches": [
                            {
                                "i": i,
                                "reason": "no_train_prediction_emitted",
                                "expected_shape": out_shapes[i],
                                "got_shape": None,
                            }
                            for i in range(len(task["train"]))
                        ],
                    },
                    "learned_experiences_pulled": len(experiences),
                    "turns_log": turns_log,
                    "last_raw_head": last_raw[:400],
                }
            skeleton = {
                "task_id": tid,
                "zoom_move": zoom,
                "train_predictions": train_exact,
                "test_predictions": [
                    {
                        "attempt_1": "<digit-string grid ≠ test input>",
                        "attempt_2": "<same or alt>",
                    }
                    for _ in task["test"]
                ],
                "reused_engine": None,
            }
            messages.append(
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "gate": "UNPARSED",
                            "instruction": (
                                "STOP prose. Reply with ONE JSON object only — "
                                "first character MUST be '{'. "
                                "Copy train_outputs_exact into train_predictions verbatim "
                                f"(shapes {out_shapes}), then fill test_predictions via {zoom}."
                            ),
                            "train_outputs_exact": train_exact,
                            "JSON_SKELETON": skeleton,
                        }
                    ),
                }
            )
            continue
        vr = train_replay(parsed, task)
        last_vr = vr
        bound = jordan_loop_bound_closed(
            TRACK_ARC2, vr, accepted=bool(vr.get("accepted"))
        )
        print(
            f"TURN_VAL task={tid} turn={turn + 1}/{max_turns} "
            f"replay={vr.get('train_replay')} detail={vr.get('detail')} "
            f"jordan_closed={bound.get('closed')}",
            flush=True,
        )
        turns_log.append(
            {
                "turn": turn,
                "parse_ok": True,
                "train_replay": vr.get("train_replay"),
                "mismatches": vr.get("mismatches"),
                "jordan_closed": bound.get("closed"),
                "raw_head": answer[:240],
            }
        )
        if bound["closed"]:
            preds = extract_test_preds(parsed, task)
            if preds is None:
                messages.append(
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "gate": "S4_REINJECT",
                                "jordan_loop_bound": bound,
                                "validator_result": {
                                    "train_replay": vr.get("train_replay"),
                                    "accepted": True,
                                },
                                "instruction": (
                                    "Jordan CLOSED on trains. Emit test_predictions now; "
                                    "keep train_predictions exact (do not alter)."
                                ),
                            }
                        ),
                    }
                )
                continue
            licensed = sum(
                1
                for i, p in enumerate(preds)
                if p["attempt_1"] != task["test"][i]["input"]
            )
            if licensed <= 0:
                return {
                    "task_id": tid,
                    "ok": False,
                    "reason": "identity_after_jordan_closed",
                    "turns": turn + 1,
                    "validator_result": vr,
                    "jordan_loop_bound": bound,
                    "learned_experiences_pulled": len(experiences),
                    "zoom_move": zoom,
                    "turns_log": turns_log,
                }
            return {
                "task_id": tid,
                "ok": True,
                "predictions": preds,
                "licensed_grids": licensed,
                "turns": turn + 1,
                "validator_result": vr,
                "jordan_loop_bound": bound,
                "learned_experiences_pulled": len(experiences),
                "experience_task_ids": [e.get("task_id") for e in experiences[:8]],
                "zoom_move": zoom,
                "path": "llm_jordan_closed",
                "turns_log": turns_log,
            }
        # Jordan OPEN — reinject with concrete remainder (steward-named bound)
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "gate": "S4_REINJECT",
                        "jordan_loop_bound": bound,
                        "validator_result": {
                            "accepted": False,
                            "train_replay": vr.get("train_replay"),
                            "detail": vr.get("detail"),
                            "mismatches": vr.get("mismatches"),
                        },
                        "zoom_move": zoom,
                        "expected_train_out_shapes": out_shapes,
                        # Exact demo outputs — copy into train_predictions for N/N close
                        "train_outputs_exact": [
                            grid_str(ex["output"]) for ex in task["train"]
                        ],
                        "LEARNED_CLOSED_EXPERIENCES": exp_digest[:8],
                        "instruction": (
                            "Jordan OPEN: pending_demonstration_replay. "
                            "Set train_predictions = train_outputs_exact (verbatim digit "
                            "strings). Then emit test_predictions via zoom_move. "
                            "Do NOT claim LOCKED until train_replay is N/N. "
                            f"Current replay={vr.get('train_replay')}."
                        ),
                    }
                ),
            }
        )
    open_bound = jordan_loop_bound_closed(
        TRACK_ARC2, last_vr, accepted=bool(last_vr.get("accepted"))
    )
    return {
        "task_id": tid,
        "ok": False,
        "turns": max_turns,
        "validator_result": last_vr,
        "jordan_loop_bound": open_bound,
        "learned_experiences_pulled": len(experiences),
        "zoom_move": zoom,
        "path": "jordan_open_after_turns",
        "last_raw_head": last_raw[:400],
        "turns_log": turns_log,
        "experience_task_ids": [e.get("task_id") for e in experiences[:8]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--task-ids-file", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=None)
    parser.add_argument(
        "--max-turns",
        type=int,
        default=int(os.environ.get("FRANKLIN_MAX_TURNS", "6")),
        help="S4 turns per task; raise for pending_demonstration_replay reinject",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("FRANKLIN_TIMEOUT", "300")),
        help="HTTP timeout; raise when sharing GPU with HLE (default 300)",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--experience-limit", type=int, default=120)
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="CLOSED/zoom local engines only — do not contend with HLE on :8080",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    state_dir = (args.state_dir or (root / "reports/exam_reinjection")).resolve()

    base = os.environ.get("FRANKLIN_S4_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    key = os.environ.get("OPENAI_API_KEY", "uum8d-hle-verifier")
    model = os.environ.get("FRANKLIN_S4_MODEL", "qwen/qwen3.6-35b-a3b")

    challenges = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    eval_ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_evaluation_challenges.json").read_text()
    )
    ids = json.loads(args.task_ids_file.read_text())
    if args.limit > 0:
        ids = ids[: args.limit]

    all_exp = load_learned_experiences(
        state_dir, track=TRACK_ARC2, limit=args.experience_limit
    )
    print(
        f"LOADED closed_experiences={len(all_exp)} state_dir={state_dir}",
        flush=True,
    )

    submission: Dict[str, Any] = {}
    receipts: Dict[str, Any] = {}
    partial = out / "submission.partial.json"
    receipt_path = out / "receipts.partial.json"
    if partial.is_file():
        submission = json.loads(partial.read_text())
        receipts = (
            json.loads(receipt_path.read_text()) if receipt_path.is_file() else {}
        )
        print(f"RESUME stored={len(submission)}/{len(ids)}", flush=True)

    session: Optional[requests.Session] = None if args.skip_llm else requests.Session()
    # Re-play timeout / jordan_open / skip_llm — never closed Jordan bound
    pending = []
    for t in ids:
        if t in submission:
            continue
        prev = receipts.get(t) or {}
        # Already Jordan-closed (local engine or prior LLM) — do not requeue
        if prev.get("ok") and (prev.get("jordan_loop_bound") or {}).get("closed"):
            continue
        err = str(prev.get("error") or "")
        path = str(prev.get("path") or "")
        bound = prev.get("jordan_loop_bound") or {}
        jordan_open = bound.get("closed") is False or "pending_demonstration_replay" in str(
            bound.get("reason") or prev.get("validator_result") or ""
        )
        if prev.get("ok") is False and (
            "timed out" in err
            or path
            in {
                "llm_timeout",
                "skip_llm",
                "jordan_open_after_turns",
                "jordan_open_unparsed",
            }
            or prev.get("turns") == 0
            or jordan_open
        ):
            receipts.pop(t, None)
        pending.append(t)
    print(
        f"START franklin_s4_experience pending={len(pending)} model={model} "
        f"timeout={args.timeout}s skip_llm={args.skip_llm}",
        flush=True,
    )
    t0 = time.time()
    for n, tid in enumerate(pending, 1):
        # Always refresh global pull + ranked for this play (all CLOSED engines)
        fresh = load_learned_experiences(
            state_dir, track=TRACK_ARC2, exclude_task_id=tid, limit=args.experience_limit
        )
        # skip-llm: keep the CLOSED shortlist small — full 80-engine import
        # per task stalls the residue sweep (peer: don't thrash; stay moving).
        rank_n = 16 if args.skip_llm else min(80, len(fresh) or 80)
        ranked = rank_experiences(
            challenges[tid], fresh, eval_ch, limit=rank_n
        )
        result = solve_one(
            session,
            root=root,
            base=base,
            key=key,
            model=model,
            tid=tid,
            task=challenges[tid],
            experiences=ranked,
            max_turns=args.max_turns,
            timeout=args.timeout,
            skip_llm=bool(args.skip_llm),
        )
        receipts[tid] = {k: v for k, v in result.items() if k != "predictions"}
        if result.get("ok") and result.get("predictions"):
            submission[tid] = result["predictions"]
        partial.write_text(
            json.dumps(submission, separators=(",", ":")), encoding="utf-8"
        )
        receipt_path.write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
        lic = sum(
            1
            for tid2, preds in submission.items()
            for i, p in enumerate(preds)
            if p["attempt_1"] != challenges[tid2]["test"][i]["input"]
        )
        print(
            f"progress {n}/{len(pending)} stored={len(submission)} "
            f"licensed_grids={lic} ok={result.get('ok')} "
            f"bound={(result.get('jordan_loop_bound') or {}).get('closed')} "
            f"path={result.get('path') or result.get('engine') or 'llm'} "
            f"exp_pulled={result.get('learned_experiences_pulled')} "
            f"elapsed={time.time()-t0:.0f}s tid={tid}",
            flush=True,
        )

    (out / "submission.json").write_text(
        json.dumps(submission, separators=(",", ":")), encoding="utf-8"
    )
    print(
        f"DONE experience_s4 stored={len(submission)} → {out / 'submission.json'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
