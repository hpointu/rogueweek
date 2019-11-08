from functools import partial
from typing import Any, Dict, Tuple, List
from dataclasses import dataclass

import pyxel
import random

from core import (
    Actor,
    index_to_pos,
    dist,
    normalize,
    cast_ray,
    State,
    Action,
    AnimSprite,
    pos_to_index,
)

from actions import open_door, end_turn

from dungeon_gen import (
    create_matrix,
    Board,
    Matrix,
    Position,
    Level,
    generate_level,
    populate_enemies,
    create_board,
    WALLS,
    is_door,
    is_empty,
    is_wall,
)
import tween


CELL_SIZE = 8
FPS = 30


def can_walk(board: Board, x, y) -> bool:
    return not board.outside(x, y) and is_empty(board.get(x, y))


def find_entity(state, x, y):
    for e in state.enemies:
        if e.pos == (x, y):
            return e
    return None


def game_turn(state: State) -> List[Action]:
    # Game just waits five seconds and gives back player hand
    if state.actions:
        return state.actions
    return [end_turn]


def player_action(state, *target):
    if state.player.is_busy():
        return

    val = state.board.get(*target)
    if can_walk(state.board, *target):
        state.player.move(*target, end_turn(state))
    elif is_door(val):
        open_door(state, target)
        state.player.wait(FPS * 0.3, end_turn(state))


def game_turn(state: State):
    if any(e.is_busy() for e in state.enemies):
        return
    _end = end_turn(state, len(state.enemies))
    for e in state.enemies:
        target = random.choice(
            [
                n
                for n in state.board.neighbours(*e.pos)
                if can_walk(state.board, *n)
            ]
        )
        if e.square in state.visible:
            e.move(*target, _end)
        else:
            e.move(*target, _end, 1)


def update(state: State) -> State:
    dx: float
    dy: float

    dx, dy = 0, 0
    step = 0.08

    x, y = state.player.pos

    if state.player_turn:
        if pyxel.btn(pyxel.KEY_DOWN):
            player_action(state, x, y + 1)
        elif pyxel.btn(pyxel.KEY_UP):
            player_action(state, x, y - 1)
        elif pyxel.btn(pyxel.KEY_LEFT):
            player_action(state, x - 1, y)
            state.orientation = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            player_action(state, x + 1, y)
            state.orientation = 1
    else:
        game_turn(state)

    state.player.update(state)

    for e in state.enemies:
        e.update(state)

    px, py = state.player.pos
    cx, cy = state.camera

    # store in-range block indices
    max_range = state.max_range
    state.in_range = set()
    for i in range(len(state.board)):
        x, y = index_to_pos(i, state.board.side)
        center = x + 0.5, y + 0.5
        if dist(center, state.player.pos) < max_range * 2:
            state.in_range.add(i)

    # Move camera if needed
    lthreshold = 6
    rthreshold = 10
    cx = px - lthreshold if px - cx < lthreshold else cx
    cx = px - rthreshold if px - cx > rthreshold else cx
    cy = py - lthreshold if py - cy < lthreshold else cy
    cy = py - rthreshold if py - cy > rthreshold else cy
    state.camera = cx, cy

    def ray_dirs(i):
        px, py = state.player.pos
        c, l = index_to_pos(i, state.board.side)
        return [
            (x - px, y - py)
            for x, y in [
                (c + 0.5, l),
                (c + 1, l + 0.5),
                (c + 0.5, l + 1),
                (c, l + 0.5),
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

    rays = sum([ray_dirs(i) for i in state.in_range], [])
    state.visible = set()
    for r in rays:
        trav, hit, _ = cast_ray((px + 0.5, py + 0.5), r, hit_wall)
        state.visible.update(trav)
        if not state.board.outside(*hit):
            state.visible.add(hit)

    return state


YES = (0, 32)
NO = (8, 32)


ANIMATED = {
    9001: AnimSprite(2, [(0, 40), (8, 40)], (0, -2), 10),
}


def draw(state: State):
    pyxel.cls(0)

    player_sprite = (0, 24)
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
            x * CELL_SIZE, y * CELL_SIZE, 1, u_, v_, CELL_SIZE, CELL_SIZE
        )

    x, y = state.to_cam_space(state.player.pos)
    u, v = player_sprite
    pyxel.blt(
        x * CELL_SIZE,
        y * CELL_SIZE,
        0,
        u,
        v,
        CELL_SIZE * state.orientation,
        CELL_SIZE,
        5,
    )

    for enemy in state.enemies:
        if enemy.square not in state.visible:
            continue
        x, y = state.to_cam_space(enemy.pos)
        sp = ANIMATED[9001]
        pyxel.blt(
            x * CELL_SIZE - sp.center[0],
            y * CELL_SIZE - sp.center[1],
            1,
            *sp.uv,
            CELL_SIZE,
            CELL_SIZE,
            1
        )


def update_debug(state: State):
    pass


def draw_debug(state: State):
    pyxel.cls(0)
    U = 3
    for i in range(len(state.board)):
        x, y = index_to_pos(i, state.board.side)
        v = state.board[i]
        if is_wall(v):
            col = 0
        elif is_door(v):
            col = 8
        else:
            col = 7
        pyxel.rect(x * U, y * U, U, U, col)


def main():
    level = generate_level(create_matrix())
    m = create_board(level)

    enemies = populate_enemies(level, m)
    # enemies = [Actor((2, 0))]

    spawn = 0, 0
    state = State(board=m, camera=(0, 0), player=Actor(spawn), enemies=enemies)
    pyxel.init(128, 128)
    pyxel.load("my_resource.pyxres")
    # pyxel.run(partial(update_debug, state), partial(draw_debug, state))
    pyxel.run(partial(update, state), partial(draw, state))


if __name__ == "__main__":
    main()
