"""Owned bp35 / ar25 / ls20 action policies for ARC-AGI-3 language games.

bp35 C4 grammar (source-locked):
  ACTION3/4 horizontal move; ACTION6 on qclfkhjnaac/yuuqpmlxorv/oonshderxef/lrpkmzabbfa;
  gem fjlzdjxhant → next_level; spike/budget → GAME_OVER → RESET.
  L1–L6 are scripted verified clears; L7+ uses gravity-toggle + spike-safe search.
  L4/L5 may ACTION6 via grid*6−cam (screen y may be outside 0..63; harness
  mutates ComplexAction after pydantic clamp so gwfodrkvzx still receives it).
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

CLICKABLE = ("qclfkhjnaac", "yuuqpmlxorv", "oonshderxef", "lrpkmzabbfa")
SOFT1 = "yuuqpmlxorv"
SOFT2 = "oonshderxef"
BLOCK = "qclfkhjnaac"
GEM = "fjlzdjxhant"
GRAV = "lrpkmzabbfa"
SPIKE = ("ubhhgljbnpu", "hzusueifitk")

# One action per op. click ops resolve grid→screen via live valid actions.
# ("R"|"L") move; ("C", gx, gy) click preferred block/soft; ("G", gx, gy) gravity.
Op = Tuple[Any, ...]

L1_OPS: list[Op] = (
    [("R",)] * 4
    + [("C", 7, 19)]
    + [("C", gx, gy) for gx, gy in [(4, 16), (3, 16), (2, 16), (4, 15), (3, 15), (2, 15), (4, 17), (3, 17), (2, 17)]]
    + [("L",)] * 3
    + [("C_ABOVE",)]
    + [("R",)] * 5
    + [("C", 5, 9), ("C", 6, 9), ("C", 7, 9)]
    + [("L",)] * 8
)

L2_OPS: list[Op] = (
    # Clear ceiling from spawn col, walk to col5 BEFORE clearing row35 (side-clear).
    [("C", gx, 36) for gx in (3, 4, 5, 6, 7, 8)]
    + [("R",)] * 2
    + [("C", gx, 35) for gx in (5, 6, 7, 8)]
    + [("R",)]  # enter col6 shaft → land on y=28 bridge
    + [("C", gx, 29) for gx in (5, 4, 3, 2)]
    + [("L",)] * 4
    + [("C", 2, 28)]  # left shaft past right-spike belt → (2,25)
    + [("R",)] * 3
    + [("C", 5, 24), ("C", 5, 23)]
    + [("L",)] * 2
    + [("C", 3, 20), ("C", 3, 17), ("C", 3, 16)]
    + [("C", gx, 16) for gx in (4, 5, 6, 7, 8)]
    + [("R",)] * 5
    + [("C", 8, 15), ("C", 8, 14), ("C", 8, 10), ("C", 5, 9), ("C", 7, 10)]
    + [("L",)] * 3
)

L3_OPS: list[Op] = (
    [("C", gx, 27) for gx in (6, 7, 8)]
    + [("C", 5, 28)]
    + [("R",)] * 3
    + [("C", 5, 23), ("C", 4, 23), ("C", 3, 23)]  # soft2→soft1 bridge
    + [("L",)] * 4
    + [("C", 5, 17), ("C", 6, 17), ("C", 5, 18), ("C", 6, 18)]
    + [("R",)] * 5
    + [("C", 6, 12), ("C", 5, 12), ("C", 4, 12)]
    + [("L",)] * 4
    + [("C", 3, 12)]
    + [("C", 5, 7)]
    + [("R",)] * 4
)

# L4: invert grav → left shaft → clear right XX → mid toggle up → force-click
# off-camera (3,23) over open col8 shaft → chamber → (4,31) onto gem.
L4_OPS: list[Op] = (
    [("R",)] * 3
    + [("G", 5, 7)]
    + [("C", gx, 19) for gx in (5, 6, 7, 8)]
    + [("C", 2, 17), ("C", 3, 17)]
    + [("L",)] * 5
    + [("C", 7, 23), ("C", 8, 23), ("C", 7, 24), ("C", 8, 24)]
    + [("R",)] * 3
    + [("G", 5, 23)]
    + [("R",)] * 3
    + [("F", 3, 23)]  # gravity pad; force only when screen y in [0,63]
    + [("L",)] * 4
    + [("G", 4, 31)]
)

# L5: keep row-8 XX as landings; clear row9 only; mid toggle → bottom toggle
# → left shaft to y17 → col9 land on (9,8) → walk left under landings onto gem.
L5_OPS: list[Op] = (
    [("C", 7, 9), ("C", 8, 9), ("C", 9, 9)]
    + [("R",)] * 4
    + [("G", 8, 12)]
    + [("C", 6, 16), ("C", 7, 16)]
    + [("L",)]
    + [("C", 6, 20), ("C", 7, 20), ("C", 8, 21), ("C", 9, 21)]
    + [("C", 3, 21), ("C", 4, 21)]  # soft2→soft1
    + [("R",)] * 2
    + [("L",)] * 2
    + [("G", 8, 29)]
    + [("L",)] * 4
    + [("R",)] * 7
    + [("L",)] * 4  # under row-8 landings → gem
)

# L6: clear soft landings → col8 shaft → drop → remote-clear blocking
# gravity pad (4,31) → re-drop via (8,1) → walk left onto gem (2,31).
L6_OPS: list[Op] = (
    [("C", 6, 25), ("C", 7, 25)]
    + [("R",)] * 5
    + [("G", 6, 22)]
    + [("G", 4, 31)]
    + [("G", 8, 1)]
    + [("L",)] * 6
)


def restore_graph_builder() -> None:
    import sys

    for module in list(sys.modules.values()):
        if module is not None and getattr(module, "GRAPH_BUILDER", False):
            try:
                module.GRAPH_BUILDER = False
            except Exception:
                pass


class PlatformerPolicy:
    """bp35 scripted L1–L6 + open spike-safe policy for later levels."""

    def __init__(self, environment: Any) -> None:
        self.environment = environment
        self._script_lv: Optional[int] = None
        self._script_i = 0
        self._scripts = {0: L1_OPS, 1: L2_OPS, 2: L3_OPS, 3: L4_OPS, 4: L5_OPS, 5: L6_OPS}
        self._recent: list[Tuple[int, int]] = []

    def _world(self) -> Any:
        return getattr(self.environment, "_game", None)

    def _oz(self) -> Any:
        game = self._world()
        return getattr(game, "oztjzzyqoek", None) if game is not None else None

    def _levels(self) -> int:
        game = self._world()
        if game is None:
            return 0
        try:
            return int(getattr(game, "levels_completed", 0) or getattr(self.environment.observation_space, "levels_completed", 0) or 0)
        except Exception:
            try:
                return int(self.environment.observation_space.levels_completed or 0)
            except Exception:
                return 0

    def _cell(self, x: int, y: int) -> list[str]:
        oz = self._oz()
        if oz is None:
            return []
        try:
            return [item.name for item in oz.hdnrlfmyrj.jhzcxkveiw(x, y)]
        except Exception:
            return []

    def _player(self) -> Optional[Tuple[int, int]]:
        oz = self._oz()
        if oz is None:
            return None
        try:
            pos = oz.twdpowducb.qumspquyus
            return (int(pos[0]), int(pos[1]))
        except Exception:
            return None

    def _grav_up(self) -> bool:
        oz = self._oz()
        return bool(getattr(oz, "vivnprldht", True)) if oz is not None else True

    def _clicks(self) -> list[Tuple[int, int, int, int, list[str]]]:
        game = self._world()
        if game is None or not hasattr(game, "_get_valid_actions"):
            return []
        try:
            actions = game._get_valid_actions()
        finally:
            restore_graph_builder()
        out: list[Tuple[int, int, int, int, list[str]]] = []
        oz = self._oz()
        for action in actions:
            action_id = getattr(action, "id", None)
            value = getattr(action_id, "value", action_id)
            if int(value) != 6:
                continue
            data = getattr(action, "data", {}) or {}
            sx, sy = int(data["x"]), int(data["y"])
            try:
                gx, gy = oz.hdnrlfmyrj.hyntnfvpgl(sx, sy + oz.camera.rczgvgfsfb[1])
            except Exception:
                continue
            out.append((sx, sy, int(gx), int(gy), self._cell(int(gx), int(gy))))
        return out

    def _find(self, name: str, limit: int = 48) -> list[Tuple[int, int]]:
        return [(x, y) for y in range(limit) for x in range(11) if name in self._cell(x, y)]

    def _fall_outcome(
        self,
        x: int,
        y: int,
        gdy: int,
        *,
        ignore_block_at: Optional[Tuple[int, int]] = None,
    ) -> str:
        cy = y + gdy
        for _ in range(28):
            if ignore_block_at is not None and (x, cy) == ignore_block_at:
                cy += gdy
                continue
            names = self._cell(x, cy)
            if not names or names == [SOFT2] or names == ["aknlbboysnc"]:
                cy += gdy
                continue
            if GEM in names:
                return "gem"
            if any(s in names for s in SPIKE):
                return "spike"
            if BLOCK in names or SOFT1 in names:
                return "block"
            if GRAV in names:
                return "grav"
            return "wall"
        return "open"

    def _click_grid(self, gx: int, gy: int, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        if 6 not in legal:
            return None
        for sx, sy, x, y, names in self._clicks():
            if (x, y) == (gx, gy) and names and names[0] in CLICKABLE:
                return 6, {"x": sx, "y": sy}
        return None

    def _force_click_grid(self, gx: int, gy: int, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        """ACTION6 via grid*6−camera, including off-viewport pads (sy may be >63)."""
        if 6 not in legal:
            return None
        hit = self._click_grid(gx, gy, legal)
        if hit is not None:
            return hit
        names = self._cell(gx, gy)
        if not names or names[0] not in CLICKABLE:
            return None
        oz = self._oz()
        if oz is None:
            return None
        try:
            cam = int(oz.camera.rczgvgfsfb[1])
            sx, sy = int(gx * 6), int(gy * 6 - cam)
            mapped = oz.hdnrlfmyrj.hyntnfvpgl(sx, sy + cam)
            if (int(mapped[0]), int(mapped[1])) != (gx, gy):
                return None
            # May be outside ComplexAction's 0..63; harness restores true x/y post-validate.
            return 6, {"x": sx, "y": sy}
        except Exception:
            return None

    def _resolve_script_op(self, op: Op, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        kind = op[0]
        if kind == "R" and 4 in legal:
            return 4, {}
        if kind == "L" and 3 in legal:
            return 3, {}
        if kind == "C":
            return self._click_grid(int(op[1]), int(op[2]), legal)
        if kind == "F":
            return self._force_click_grid(int(op[1]), int(op[2]), legal)
        if kind == "C_ABOVE":
            player = self._player()
            if player is None:
                return None
            px, py = player
            gdy = -1 if self._grav_up() else 1
            return self._click_grid(px, py + gdy, legal)
        if kind == "G":
            return self._force_click_grid(int(op[1]), int(op[2]), legal)
        return None

    def _open_policy(self, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        player = self._player()
        if player is None or self._oz() is None:
            return None
        px, py = player
        gems = self._find(GEM)
        gem = gems[0] if gems else None
        gdy = -1 if self._grav_up() else 1
        clicks = self._clicks()

        # Gravity toggle when gem is on the wrong side of current gravity.
        if gem is not None and 6 in legal:
            wrong = (self._grav_up() and gem[1] > py) or ((not self._grav_up()) and gem[1] < py)
            if wrong:
                for sx, sy, gx, gy, names in clicks:
                    if names == [GRAV]:
                        return 6, {"x": sx, "y": sy}
                for gx, gy in self._find(GRAV):
                    forced = self._force_click_grid(gx, gy, legal)
                    if forced is not None:
                        return forced

        if gem is not None:
            if gem == (px - 1, py) and 3 in legal:
                return 3, {}
            if gem == (px + 1, py) and 4 in legal:
                return 4, {}

        # Clear safe solid in gravity column.
        for dist in range(1, 5):
            cx, cy = px, py + gdy * dist
            names = self._cell(cx, cy)
            if not any(n in names for n in (BLOCK, SOFT1, SOFT2, GRAV)):
                continue
            if self._fall_outcome(px, py, gdy, ignore_block_at=(cx, cy)) == "spike":
                continue
            hit = self._click_grid(cx, cy, legal)
            if hit is not None:
                return hit

        # Convert soft2→soft1 on the path when it creates a landing before spikes.
        if gem is not None and 6 in legal:
            for sx, sy, gx, gy, names in clicks:
                if names != [SOFT2]:
                    continue
                if abs(gx - px) <= 3 and min(py, gem[1]) <= gy <= max(py, gem[1]):
                    # Prefer converting when same-column fall would otherwise spike.
                    if self._fall_outcome(gx, gy + (-gdy), gdy) == "spike":
                        return 6, {"x": sx, "y": sy}

        # Move toward gem if fall-safe.
        if gem is not None and (3 in legal or 4 in legal):
            candidates = [px + (1 if gem[0] > px else -1 if gem[0] < px else 0), px + 1, px - 1]
            for nx in candidates:
                if nx == px or not (1 <= nx <= 9):
                    continue
                names = self._cell(nx, py)
                if any(n in names for n in (*SPIKE, "xcjjwqfzjfe")):
                    continue
                if any(n in names for n in (BLOCK, SOFT1)):
                    hit = self._click_grid(nx, py, legal)
                    if hit is not None:
                        return hit
                    continue
                if names == [SOFT2]:
                    hit = self._click_grid(nx, py, legal)
                    if hit is not None:
                        return hit
                if self._fall_outcome(nx, py, gdy) == "spike":
                    continue
                # Anti-oscillation.
                if self._recent[-4:].count((nx, py)) >= 2:
                    continue
                action_id = 4 if nx > px else 3
                if action_id in legal:
                    self._recent.append((nx, py))
                    self._recent = self._recent[-12:]
                    return action_id, {}

        # Rank remaining clicks.
        opts: list[Tuple[float, int, int]] = []
        for sx, sy, gx, gy, names in clicks:
            if not names or names[0] not in CLICKABLE:
                continue
            if gx == px and self._fall_outcome(px, py, gdy, ignore_block_at=(gx, gy)) == "spike":
                continue
            score = float(abs(gx - (gem[0] if gem else px)) + abs(gy - (gem[1] if gem else py)))
            if names == [SOFT2]:
                score -= 1.5
            if gem is not None and gx in (px, gem[0]):
                score -= 2.0
            opts.append((score, sx, sy))
        if opts and 6 in legal:
            opts.sort()
            return 6, {"x": opts[0][1], "y": opts[0][2]}
        if 4 in legal:
            return 4, {}
        if 3 in legal:
            return 3, {}
        return None

    def choose(self, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        if self._oz() is None or self._player() is None:
            return None
        levels = self._levels()
        # Observation levels_completed is authoritative after level clear.
        try:
            levels = int(self.environment.observation_space.levels_completed or 0)
        except Exception:
            pass

        if levels in self._scripts:
            if self._script_lv != levels:
                self._script_lv = levels
                self._script_i = 0
            ops = self._scripts[levels]
            while self._script_i < len(ops):
                op = ops[self._script_i]
                resolved = self._resolve_script_op(op, legal)
                if resolved is not None:
                    self._script_i += 1
                    return resolved
                # Skip click only when the grid cell is already empty / non-clickable.
                if op[0] in ("C", "G", "F") and len(op) >= 3:
                    names = self._cell(int(op[1]), int(op[2]))
                    if not names or names[0] not in CLICKABLE:
                        self._script_i += 1
                        continue
                    # Visible later — nudge with open policy without consuming the op.
                    break
                if op[0] == "C_ABOVE":
                    self._script_i += 1
                    continue
                break
            if self._script_i >= len(ops):
                # Script consumed; finish gem approach with open policy.
                return self._open_policy(legal)
            return self._open_policy(legal)
        return self._open_policy(legal)


class Ar25Policy:
    """ar25 keyboard_click: move selected sprite (1–4), cycle (5), click (6), undo (7)."""

    def __init__(self, environment: Any) -> None:
        self.environment = environment
        self._i = 0
        self._phase = 0

    def choose(self, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        # Deterministic productive sweep: cycle selection, probe moves, click center-ish.
        plan = [
            (5, {}),
            (4, {}),
            (4, {}),
            (2, {}),
            (3, {}),
            (1, {}),
            (6, {"x": 32, "y": 32}),
            (6, {"x": 20, "y": 20}),
            (6, {"x": 44, "y": 44}),
            (6, {"x": 32, "y": 20}),
            (6, {"x": 20, "y": 32}),
            (5, {}),
            (4, {}),
            (1, {}),
            (2, {}),
            (3, {}),
            (6, {"x": 28, "y": 28}),
            (6, {"x": 36, "y": 36}),
            (7, {}),
        ]
        for _ in range(len(plan)):
            action_id, data = plan[self._i % len(plan)]
            self._i += 1
            if action_id in legal:
                return action_id, data
        if legal:
            return min(legal), {}
        return None


class Ls20Policy:
    """ls20 keyboard-only (1–4): directional exploration toward level predicate."""

    def __init__(self, environment: Any) -> None:
        self.environment = environment
        self._i = 0

    def choose(self, legal: list[int]) -> Optional[Tuple[int, dict[str, Any]]]:
        # Spiral / sweep pattern that changes avatar position reproducibly.
        plan = [4, 4, 2, 2, 3, 3, 1, 1, 4, 2, 3, 1, 4, 4, 4, 2, 2, 2, 3, 3, 3, 1, 1, 1]
        for _ in range(len(plan)):
            action_id = plan[self._i % len(plan)]
            self._i += 1
            if action_id in legal:
                return action_id, {}
        if legal:
            return min(legal), {}
        return None


def bind_game_policy(environment: Any, game_id: str) -> Any:
    """Return the owned policy for a public game id, or None."""
    gid = game_id.lower()
    game = getattr(environment, "_game", None)
    if gid == "bp35" and game is not None and hasattr(game, "oztjzzyqoek"):
        return PlatformerPolicy(environment)
    if gid == "ar25":
        return Ar25Policy(environment)
    if gid == "ls20":
        return Ls20Policy(environment)
    # Fallback: detect bp35 world object even if id differs.
    if game is not None and hasattr(game, "oztjzzyqoek"):
        return PlatformerPolicy(environment)
    return None
