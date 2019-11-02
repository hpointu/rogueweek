from functools import partial
from typing import Any, Dict
from dataclasses import dataclass

import pyxel

from dungeon_gen import (
    M_SIZE,
    MAX_ROOM_SIZE,
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
    player: Position
    board: Board
    camera: Position


def update(state: State) -> State:
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
    lthreshold = 6 * CELL_SIZE
    rthreshold = 10 * CELL_SIZE
    cx = px - lthreshold if px - cx < lthreshold else cx
    cx = px - rthreshold if px - cx > rthreshold else cx
    cy = py - lthreshold if py - cy < lthreshold else cy
    cy = py - rthreshold if py - cy > rthreshold else cy

    state.camera = cx, cy

    return state


def draw(state: Any):
    pyxel.cls(0)

    player_sprite = (0, 24)
    non_walls = {
        0: (32, 16),
        2: (48, 0),
    }

    cx, cy = state.camera

    for i, v in enumerate(state.board):
        col = i % (M_SIZE * MAX_ROOM_SIZE)
        lin = int(i / (M_SIZE * MAX_ROOM_SIZE))
        x = col * CELL_SIZE - cx
        y = lin * CELL_SIZE - cy
        colors = WALLS if is_wall(v) else non_walls
        u_, v_ = colors[v]
        pyxel.blt(x, y, 0, u_, v_, CELL_SIZE, CELL_SIZE)

    x, y = map(int, state.player)
    u, v = player_sprite
    pyxel.blt(x - cx, y - cy, 0, u, v, CELL_SIZE, CELL_SIZE, 5)

    # draw_matrix(state.matrix)

    # # draw room sizes
    # for i, room in enumerate(state.rooms):
    #     l, c = int(i / M_SIZE), int(i % M_SIZE)
    #     pyxel.text(c * 16, l * 16, f"({room[0]},{room[1]})", 8)


def main():
    level = generate_level(create_matrix())
    m = create_map(level)

    state = State(board=m, camera=(0, 0), player=(0, 0))
    pyxel.init(128, 128)
    pyxel.load("my_resource.pyxres")
    pyxel.run(partial(update, state), partial(draw, state))


if __name__ == "__main__":
    main()
