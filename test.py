from functools import partial
from typing import Any, Dict, Tuple, List
from dataclasses import dataclass

import pyxel

from core import index_to_pos, dist

from dungeon_gen import (
    SIDE,
    create_matrix,
    Board,
    Matrix,
    Position,
    Level,
    generate_level,
    create_map,
    WALLS,
    is_wall,
)


CELL_SIZE = 8


@dataclass
class State:
    max_range = 5
    player: Tuple[float, float]
    board: Board
    in_range = List[int]
    camera: Tuple[float, float]


def update(state: State) -> State:
    dx: float
    dy: float

    dx, dy = 0, 0
    step = 0.6

    if pyxel.btn(pyxel.KEY_DOWN):
        dy += step
    if pyxel.btn(pyxel.KEY_UP):
        dy -= step
    if pyxel.btn(pyxel.KEY_LEFT):
        dx -= step
    if pyxel.btn(pyxel.KEY_RIGHT):
        dx += step

    x, y = state.player
    state.player = x + dx, y + dy

    px, py = state.player
    cx, cy = state.camera

    # store in-range block indices
    max_range = state.max_range * CELL_SIZE
    state.in_range = []
    for i in range(len(state.board)):
        x, y = index_to_pos(i, SIDE)
        center = x * CELL_SIZE + CELL_SIZE / 2, y * CELL_SIZE + CELL_SIZE / 2
        if dist(center, state.player) < max_range:
            state.in_range.append(i)

    # Move camera if needed
    lthreshold = 6 * CELL_SIZE
    rthreshold = 10 * CELL_SIZE
    cx = px - lthreshold if px - cx < lthreshold else cx
    cx = px - rthreshold if px - cx > rthreshold else cx
    cy = py - lthreshold if py - cy < lthreshold else cy
    cy = py - rthreshold if py - cy > rthreshold else cy
    state.camera = cx, cy

    return state


YES = (0, 32)
NO = (8, 32)


def draw(state: State):
    pyxel.cls(0)

    player_sprite = (0, 24)
    non_walls = {
        0: (32, 16),
        2: (48, 0),
    }

    cx, cy = state.camera

    # for i, v in enumerate(state.board):
    #     col, lin = index_to_pos(i, SIDE)
    #     x = col * CELL_SIZE - cx
    #     y = lin * CELL_SIZE - cy
    #     colors = WALLS if is_wall(v) else non_walls
    #     u_, v_ = colors[v]
    #     pyxel.blt(x, y, 0, u_, v_, CELL_SIZE, CELL_SIZE)

    # draw in range
    for i in state.in_range:
        col, lin = index_to_pos(i, SIDE)
        v = state.board[i]
        x = col * CELL_SIZE - cx
        y = lin * CELL_SIZE - cy
        colors = WALLS if is_wall(v) else non_walls
        u_, v_ = colors[v]
        pyxel.blt(x, y, 0, u_, v_, CELL_SIZE, CELL_SIZE)
        # pyxel.blt(x, y, 0, *(YES + (CELL_SIZE, CELL_SIZE)), 5)

    x, y = map(int, state.player)
    u, v = player_sprite
    pyxel.blt(x - cx, y - cy, 0, u, v, CELL_SIZE, CELL_SIZE, 5)


def main():
    level = generate_level(create_matrix())
    m = create_map(level)

    state = State(board=m, camera=(0, 0), player=(0, 0))
    pyxel.init(128, 128)
    pyxel.load("my_resource.pyxres")
    pyxel.run(partial(update, state), partial(draw, state))


if __name__ == "__main__":
    main()
