#!/usr/bin/env python3
"""Per-engine timeout zoom Jordan closer on AGI-2 identity residue.

Parent stays warm (loads challenges once). Each engine try runs in a spawn
child with a short timeout so one hung engine cannot stall the residue sweep.
No :8080. Safe beside Franklin LLM + HLE.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import multiprocessing as mp
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ZOOM_STEMS = {
    "zoom_out_expand": [
        "s1_period_tile_colflip_rowblock",
        "s1_period_tile_dihedral2",
        "s1_nw_wrap_mark_period_tile",
        "s1_plus_sig_quad_expand",
        "container_period_tiling",
        "s1_ones_stamp_period_fill",
        "s1_panel_scale_project",
        "s1_oriented_block_pack",
        "s1_motif_stamp_jigsaw",
        "s1_fixed_canvas_template",
        "s1_canvas_hole_sprite_fill",
        "s1_diagonal_mod3_period_fill",
        "s1_seed_period_stripe_fill",
        "s1_ncomp_staircase_project",
        "s1_crop_hstack_dup",
        "s1_oddcol_slot_band_expand",
        "s1_ccw_frame_double_stack",
        "s1_motif_cardinal_dihedral",
    ],
    "zoom_in_crop": [
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
        "s2_line_len_concentric_frames",
        "s2_color_square_d4_compose",
        "s2_most_plus5_comp_crop",
        "s2_host_accent_align_twos",
        "s2_hinge5_nearest_comp_pack",
        "s2_largest_host_frame_interior",
    ],
    "same_canvas_rewrite": [
        "s2_color_gate_rewrite",
        "s2_component_recolor",
        "s2_dual_palette_rewrite",
        "s1_header_bracket_fill",
        "s2_ones_shape_template_recolor",
        "s2_marker_freq_column_project",
        "s1_checker_frame_fill",
        "s2_triplet_mask_digit_map",
        "s2_bbox_fourfold_mirror_complete",
        "s2_seed_neighborhood_stamp",
        "s2_slide_touch_blocker",
        "s2_row_run_shift_left_fill",
        "s2_enclosed_zero_rect_fill",
        "s2_legend_row_recolor_or_stamp",
        "s1_singleton_3x3_stamp",
        "s2_marker3_template_stamp",
        "s2_sep_panel_template_stamp",
        "s1_diagonal_component_stack",
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
        "s2_nine_step_to_six",
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
        "s2_lattice_hub_halo_stamp",
        "s2_dual_band_longest_path_corridors",
        "s2_wall_marker_extend",
        "s2_small_comp_recolor3",
        "s2_solid_rect_erase4",
        "s2_host_block_nested_frame_stamp",
        "s2_host_cross_template_stamp",
        "s2_ink_sealed_open_side_dock",
        "s2_marker6_rank_row_bar",
        "s2_marker_col_template_bands",
        "s2_sprite_magnet_reseat",
        "s2_template_h_motif_recolor",
        "s2_oddcol_max8_pack9",
        "s2_border_color_dock_edge_extend",
        "s2_wall_room_period2_motif_stamp",
        "s2_eight_channel_fill",
        "s2_motif4_arrow_translate_diag_x",
        "s2_unique_band_slot_composite",
    ],
}


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


def _engine_worker(payload: Tuple[str, str, str, Dict[str, Any]]) -> Dict[str, Any]:
    """Child: try one engine on one task (task JSON passed in — no big reload)."""
    root_s, tid, eng, task = payload
    root = Path(root_s)
    path = root / "llm_llvm_bench" / "arc" / f"{eng}.py"
    if not path.is_file():
        return {"ok": False, "reason": "missing"}
    spec = importlib.util.spec_from_file_location(f"eng_{eng}", path)
    if spec is None or spec.loader is None:
        return {"ok": False, "reason": "import"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "train_replay") or not hasattr(mod, "submission_fragment"):
        return {"ok": False, "reason": "api"}
    if hasattr(mod, "applies"):
        try:
            if not mod.applies(task):
                return {"ok": False, "reason": "applies_false"}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "reason": f"applies_err:{exc}"[:80]}
    try:
        replay = mod.train_replay(task)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"replay_err:{exc}"[:80]}
    if not (isinstance(replay, dict) and replay.get("perfect")):
        return {"ok": False, "reason": "imperfect"}
    try:
        frag = mod.submission_fragment(tid, task)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"frag_err:{exc}"[:80]}
    if not frag or tid not in frag:
        return {"ok": False, "reason": "no_frag"}
    preds = frag[tid]
    if len(preds) != len(task["test"]):
        return {"ok": False, "reason": "pred_len"}
    licensed = sum(
        1
        for i, p in enumerate(preds)
        if isinstance(p.get("attempt_1"), list)
        and p["attempt_1"] != task["test"][i]["input"]
    )
    if licensed <= 0:
        return {"ok": False, "reason": "identity"}
    return {
        "ok": True,
        "task_id": tid,
        "engine": eng,
        "predictions": preds,
        "licensed_grids": licensed,
        "train_n": len(task["train"]),
        "test_n": len(task["test"]),
        "train_replay": f"{len(task['train'])}/{len(task['train'])}",
    }


def try_engine_inplace(root: Path, tid: str, task: Dict[str, Any], eng: str) -> Optional[Dict[str, Any]]:
    """In-process try for trusted zoom stems (milliseconds when applies=False)."""
    path = root / "llm_llvm_bench" / "arc" / f"{eng}.py"
    if not path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(f"eng_{eng}", path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "train_replay") or not hasattr(mod, "submission_fragment"):
            return None
        if hasattr(mod, "applies") and not mod.applies(task):
            return None
        replay = mod.train_replay(task)
        if not (isinstance(replay, dict) and replay.get("perfect")):
            return None
        frag = mod.submission_fragment(tid, task)
        if not frag or tid not in frag:
            return None
        preds = frag[tid]
        if len(preds) != len(task["test"]):
            return None
        licensed = sum(
            1
            for i, p in enumerate(preds)
            if isinstance(p.get("attempt_1"), list)
            and p["attempt_1"] != task["test"][i]["input"]
        )
        if licensed <= 0:
            return None
        return {
            "ok": True,
            "task_id": tid,
            "engine": eng,
            "predictions": preds,
            "licensed_grids": licensed,
            "train_n": len(task["train"]),
            "test_n": len(task["test"]),
            "train_replay": f"{len(task['train'])}/{len(task['train'])}",
        }
    except Exception:
        return None


def try_engines(
    root: Path,
    tid: str,
    task: Dict[str, Any],
    zoom_engines: Sequence[str],
    exp_engines: Sequence[str],
    *,
    engine_timeout: float,
    ctx: mp.context.BaseContext,
) -> Optional[Dict[str, Any]]:
    for eng in zoom_engines:
        row = try_engine_inplace(root, tid, task, eng)
        if row and row.get("ok"):
            return row
    # Experience engines may hang — isolate with spawn timeout
    for eng in exp_engines:
        if eng in zoom_engines:
            continue
        with ctx.Pool(1) as pool:
            async_r = pool.apply_async(
                _engine_worker, ((str(root), tid, eng, task),)
            )
            try:
                row = async_r.get(timeout=engine_timeout)
            except Exception:
                pool.terminate()
                continue
        if row.get("ok"):
            return row
    return None


def seal_closed(root: Path, row: Dict[str, Any]) -> Path:
    tid = row["task_id"]
    eng = row.get("engine") or "unknown"
    gdir = root / "reports/exam_reinjection/grammar/arc2"
    gdir.mkdir(parents=True, exist_ok=True)
    train_n = int(row.get("train_n") or 0)
    replay = row.get("train_replay") or f"{train_n}/{train_n}"
    seal = {
        "task_id": tid,
        "exam": "ARC-AGI-2",
        "language_game_class": "ZOOM_ENGINE_EXACT",
        "status": "CLOSED",
        "last_gate": "LOCKED",
        "train": train_n,
        "test": int(row.get("test_n") or 1),
        "engine": eng,
        "module": f"llm_llvm_bench/arc/{eng}.py",
        "observations": [
            f"Zoom grammar engine {eng}",
            f"Train demonstration_replay {replay}",
        ],
        "validator": "demonstration_replay",
        "validator_result": {
            "accepted": True,
            "detail": "train_replay_perfect",
            "train_replay": replay,
            "engine": eng,
        },
        "c4_invariant": eng,
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    out = gdir / f"{tid}.json"
    out.write_text(json.dumps(seal, indent=2) + "\n")
    return out


def identity_residue(root: Path) -> List[str]:
    sub = json.loads(
        (root / "reports/airgap_agi2_test_20260721T175400Z/submission.json").read_text()
    )
    ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    out: List[str] = []
    for tid, preds in sub.items():
        if tid not in ch:
            continue
        tin = ch[tid]["test"][0]["input"]
        a1 = preds[0].get("attempt_1") if preds else None
        if a1 == tin:
            out.append(tid)
    return out


def experience_engines(root: Path, limit: int = 80) -> List[str]:
    from llm_llvm_bench.exam.miss_reinjection import TRACK_ARC2, load_learned_experiences

    arc = root / "llm_llvm_bench" / "arc"
    exps = load_learned_experiences(
        root / "reports/exam_reinjection", track=TRACK_ARC2, limit=limit
    )
    seen: List[str] = []
    for ex in exps:
        for key in ("engine",):
            name = str(ex.get(key) or "").strip()
            if name and (arc / f"{name}.py").is_file() and name not in seen:
                seen.append(name)
        eid = str(ex.get("task_id") or "")
        if eid:
            for pref in ("s3_g_", "s2_g_", "s1_g_", ""):
                name = f"{pref}{eid}" if pref else eid
                if (arc / f"{name}.py").is_file() and name not in seen:
                    seen.append(name)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "reports/airgap_agi2_zoom_engine_mine",
    )
    ap.add_argument("--engine-timeout", type=float, default=4.0)
    ap.add_argument("--experience-limit", type=int, default=80)
    ap.add_argument(
        "--with-experience",
        action="store_true",
        help="Also try CLOSED experience engines (spawn-isolated; slower)",
    )
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    root = args.root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    ch = json.loads(
        (root / "data/arc-prize-2026-agi-2/arc-agi_test_challenges.json").read_text()
    )
    ids = identity_residue(root)
    if args.limit > 0:
        ids = ids[: args.limit]

    sub_path = out / "submission.partial.json"
    rec_path = out / "receipts.partial.json"
    submission: Dict[str, Any] = {}
    receipts: Dict[str, Any] = {}
    if sub_path.is_file() and sub_path.stat().st_size > 2:
        submission = json.loads(sub_path.read_text())
    if rec_path.is_file() and rec_path.stat().st_size > 2:
        receipts = json.loads(rec_path.read_text())

    pending = [t for t in ids if t not in submission]
    exp_engs = (
        experience_engines(root, args.experience_limit) if args.with_experience else []
    )
    print(
        f"START zoom_engine_mine residue={len(ids)} pending={len(pending)} "
        f"stored={len(submission)} eng_timeout={args.engine_timeout}s "
        f"exp_engines={len(exp_engs)} zoom_only={not args.with_experience}",
        flush=True,
    )

    ctx = mp.get_context("spawn")
    new_closes = 0
    t0 = time.time()
    for i, tid in enumerate(pending):
        task = ch[tid]
        zoom = _zoom_move(task)
        row = try_engines(
            root,
            tid,
            task,
            ZOOM_STEMS.get(zoom, []),
            exp_engs,
            engine_timeout=args.engine_timeout,
            ctx=ctx,
        )
        if row and row.get("ok"):
            submission[tid] = row["predictions"]
            receipts[tid] = {
                "task_id": tid,
                "ok": True,
                "path": "zoom_engine_experience",
                "engine": row.get("engine"),
                "licensed_grids": row.get("licensed_grids"),
                "validator_result": {
                    "accepted": True,
                    "train_replay": row.get("train_replay"),
                    "detail": "train_replay_perfect",
                },
                "jordan_loop_bound": {"closed": True, "reason": "LOCKED"},
            }
            seal_closed(root, row)
            new_closes += 1
            print(
                f"CLOSE {tid} eng={row.get('engine')} "
                f"licensed={row.get('licensed_grids')} zoom={zoom}",
                flush=True,
            )
        else:
            receipts[tid] = {
                "task_id": tid,
                "ok": False,
                "path": "no_engine",
                "zoom_move": zoom,
            }
        if (i + 1) % 10 == 0 or (row and row.get("ok")):
            sub_path.write_text(json.dumps(submission))
            rec_path.write_text(json.dumps(receipts, indent=2))
            print(
                f"progress {i+1}/{len(pending)} new={new_closes} "
                f"stored={len(submission)}",
                flush=True,
            )

    sub_path.write_text(json.dumps(submission))
    rec_path.write_text(json.dumps(receipts, indent=2))
    summary = {
        "new_closes": new_closes,
        "stored": len(submission),
        "pending_seen": len(pending),
        "elapsed_s": round(time.time() - t0, 1),
        "closed_ids": sorted(submission),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out / "MINE_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"DONE {json.dumps(summary)}", flush=True)
    return 0


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    raise SystemExit(main())
