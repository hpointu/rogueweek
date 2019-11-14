import pyxel
import random

from functools import partial

from rogue import debug

from rogue.actions import end_turn, open_door

from rogue.core import ITEMS
from rogue.core import Board, State, Player, VecF
from rogue.core import dist, index_to_pos, cast_ray
from rogue.core import is_empty, is_wall, is_door

from rogue.dungeon_gen import generate_level, populate_enemies, basic_scenario

from rogue.particles import DamageText

from rogue.constants import CELL_SIZE, FPS
from rogue.sprites import WALLS

from typing import List


def can_walk(board: Board, x, y) -> bool:
    return not board.outside(x, y) and is_empty(board.get(x, y))


def find_entity(state, x, y):
    for e in state.enemies:
        if e.pos == (x, y):
            return e
    return None


def player_action(state: State, x, y):
    if state.player.is_busy():
        return

    target = x, y
    val = state.board.get(*target)
    entity = find_entity(state, *target)
    _end = end_turn(state)

    if entity:
        # interact with an other entity
        # TODO assume it's an enemy for now, will change
        a = state.player.attack(entity, _end)
        ppos = state.to_pixel(entity.pos, CELL_SIZE)
        state.particles.append(DamageText(f"-{a}", ppos, 12))
    elif can_walk(state.board, *target):
        state.player.move(*target, _end)
    elif is_door(val):
        open_door(state, target)
        state.player.wait(FPS * 0.3, _end)
    elif is_wall(val) or state.board.outside(*target):
        state.player.bump_to(target, _end)
    else:
        state.player.wait(FPS * 0.3, _end)


def game_turn(state: State):
    if any(e.is_busy() for e in state.enemies):
        return
    _end = end_turn(state, len(state.enemies))
    for e in state.enemies:
        # Only damage report, so far. Might add more reporting
        report = e.take_action(state, _end)
        if report is not None:
            ppos = state.to_pixel(state.player.pos, CELL_SIZE)
            state.particles.append(DamageText(f"-{report}", ppos, 8))


def update(state: State) -> State:
    x, y = state.player.pos

    if state.player_turn:
        if pyxel.btn(pyxel.KEY_DOWN):
            player_action(state, x, y + 1)
        elif pyxel.btn(pyxel.KEY_UP):
            player_action(state, x, y - 1)
        elif pyxel.btn(pyxel.KEY_LEFT):
            player_action(state, x - 1, y)
            state.player.orientation = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            player_action(state, x + 1, y)
            state.player.orientation = 1
    else:
        game_turn(state)

    state.player.update(state)

    # Move camera if needed
    px, py = state.player.pos
    cx, cy = state.camera
    lthreshold = 6
    rthreshold = 10
    cx = px - lthreshold if px - cx < lthreshold else cx
    cx = px - rthreshold if px - cx > rthreshold else cx
    cy = py - lthreshold if py - cy < lthreshold else cy
    cy = py - rthreshold if py - cy > rthreshold else cy
    state.camera = cx, cy

    deads_enemies = []
    for e in state.enemies:
        e.update(state)
        if e.pv < 1:
            deads_enemies.append(e)
    for d in deads_enemies:
        state.enemies.remove(d)

    deads_particles = []
    for p in state.particles:
        p.update(state)
        if not p.living():
            deads_particles.append(p)
    for dp in deads_particles:
        state.particles.remove(dp)

    # store in-range block indices
    max_range = state.max_range
    state.in_range = set()
    for i in range(len(state.board)):
        x, y = index_to_pos(i, state.board.side)
        center = x + 0.5, y + 0.5
        if dist(center, state.player.pos) < max_range * 2:
            state.in_range.add(i)

    # for i in range(3):
    #     state.particles.append(Glitter(state.player.pos))

    def ray_dirs(i):
        px, py = state.player.pos
        c, r = index_to_pos(i, state.board.side)
        return [
            (x - px, y - py)
            for x, y in [
                (c + 0.5, r),
                (c + 1, r + 0.5),
                (c + 0.5, r + 1),
                (c, r + 0.5),
            ]
            if x - px and y - py
        ]

    def hit_wall(x, y):
        return (
            state.board.outside(x, y)
            or is_wall(state.board.get(x, y))
            or dist(state.player.pos, (x, y)) > state.max_range
            or is_door(state.board.get(x, y))
        )

    rays: List[VecF] = sum([ray_dirs(i) for i in state.in_range], [])
    state.visible = set()
    for r in rays:
        trav, hit, _ = cast_ray((px + 0.5, py + 0.5), r, hit_wall)
        state.visible.update(trav)
        if not state.board.outside(*hit):
            state.visible.add(hit)

    return state


def draw(state: State):
    pyxel.cls(0)

    non_walls = {
        0: (32, 16),
        30: (40, 24),
        31: (0, 24),
        32: (8, 24),
        33: (16, 24),
        34: (40, 16),
        35: (48, 8),
        20: (48, 0),
        21: (56, 16),
        22: (56, 8),
        23: (56, 0),
        25: (64, 0),
        26: (72, 16),
        27: (72, 8),
        28: (72, 0),
    }

    # draw in range
    for x, y in state.visible:
        # for i in range(len(state.board)):
        #     x, y = index_to_pos(i, state.board.side)
        if state.board.outside(x, y):
            continue
        v = state.board.get(x, y)
        x, y = state.to_cam_space((x, y))
        colors = WALLS if is_wall(v) else non_walls
        u_, v_ = colors[v]
        pyxel.blt(
            x * CELL_SIZE, y * CELL_SIZE, 0, u_, v_, CELL_SIZE, CELL_SIZE
        )

    # draw collectibles and stuff
    for item in state.level.items:
        if item.square not in state.visible:
            continue
        x, y = state.to_cam_space(item.square)
        pyxel.blt(x * CELL_SIZE, y * CELL_SIZE, 0, *item.sprite)

    x, y = state.to_cam_space(state.player.pos)
    sp = state.player.sprite
    pyxel.blt(
        x * CELL_SIZE - sp.center[0],
        y * CELL_SIZE - sp.center[1],
        0,
        *sp.uv,
        CELL_SIZE * state.player.orientation,
        CELL_SIZE,
        1,
    )

    for enemy in state.enemies:
        if enemy.square not in state.visible:
            continue
        x, y = state.to_cam_space(enemy.pos)
        sp = enemy.sprite
        pyxel.blt(
            x * CELL_SIZE - sp.center[0],
            y * CELL_SIZE - sp.center[1],
            0,
            *sp.uv,
            CELL_SIZE,
            CELL_SIZE,
            1,
        )

    for p in state.particles:
        p.draw(state)

    # HUD
    pyxel.rect(3, 3, 2 * state.player.pv, 7, 2)
    pyxel.rect(3, 3, 2 * state.player.pv, 5, 8)
    pyxel.rect(4, 4, 2 * state.player.pv - 2, 1, 14)
    pyxel.rectb(2, 2, 42, 8, 1)

    for i in range(state.player.keys):
        pyxel.blt(3 + i * 7, 12, 0, *ITEMS['key'])


class App:
    _debug: bool = False

    def __init__(self):
        level, board = basic_scenario(*generate_level())
        enemies = populate_enemies(level, board)

        self.state = State(
            level=level,
            board=board,
            camera=(0, 0),
            player=Player(board.to_pos(board.entrance), 9000),
            enemies=enemies,
        )

        self._draw = partial(draw, self.state)
        self._draw_debug = partial(debug.draw_debug, self.state)

        self._update = partial(update, self.state)
        self._update_debug = partial(debug.update_debug, self.state)

    def update(self):
        if pyxel.btnr(pyxel.KEY_D):
            self._debug = not self._debug

        if self._debug:
            self._update_debug()
        else:
            self._update()

    def draw(self):
        if self._debug:
            self._draw_debug()
        else:
            self._draw()


def main():
    app = App()
    pyxel.init(128, 128)
    pyxel.load("my_resource.pyxres")
    pyxel.run(app.update, app.draw)


if __name__ == "__main__":
    main()
