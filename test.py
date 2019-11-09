from functools import partial
from typing import List

import pyxel
import random

from constants import FPS, CELL_SIZE

from core import (
    Player,
    VecF,
    index_to_pos,
    dist,
    cast_ray,
    State,
)

from particles import Glitter, DamageText

from actions import open_door, end_turn

from dungeon_gen import (
    create_matrix,
    Board,
    generate_level,
    populate_enemies,
    WALLS,
    is_door,
    is_empty,
    is_wall,
)


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
    else:
        state.player.wait(FPS * 0.3, _end)


def game_turn(state: State):
    if any(e.is_busy() for e in state.enemies):
        return
    _end = end_turn(state, len(state.enemies))
    for e in state.enemies:
        possible = [
            n
            for n in state.board.neighbours(*e.pos)
            if can_walk(state.board, *n)
        ]
        if e.square in state.visible:
            possible = sorted(
                possible, key=lambda x: dist(x, state.player.square)
            )
            if possible[0] == state.player.square:
                a = e.attack(state.player, _end)
                ppos = state.to_pixel(state.player.pos, CELL_SIZE)
                state.particles.append(DamageText(f"-{a}", ppos, 8))
            else:
                x, y = possible[0]
                e.move(x, y, _end)
        else:
            if possible:
                x, y = random.choice(possible)
                e.move(x, y, _end, 1)
            else:
                e.wait(10, _end)


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

    for i in range(3):
        state.particles.append(Glitter(state.player.pos))

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


YES = (0, 32)
NO = (8, 32)


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

    pyxel.rect(3, 3, 2 * state.player.pv, 7, 2)
    pyxel.rect(3, 3, 2 * state.player.pv, 5, 8)
    pyxel.rect(4, 4, 2 * state.player.pv - 2, 1, 14)
    pyxel.rectb(2, 2, 42, 8, 1)


def main():
    level, m = generate_level(create_matrix())

    print(level.final_room)

    enemies = populate_enemies(level, m)
    # enemies = [Actor((2, 0))]

    spawn = 0, 0
    state = State(
        level=level,
        board=m,
        camera=(0, 0),
        player=Player(spawn, 9000),
        enemies=enemies,
    )
    state.particles = []
    pyxel.init(128, 128)
    pyxel.load("my_resource.pyxres")
    # pyxel.run(partial(update, state), partial(draw, state))

    from debug import update_debug, draw_debug

    pyxel.run(partial(update_debug, state), partial(draw_debug, state))


if __name__ == "__main__":
    main()
