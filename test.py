from functools import partial
from typing import Any, Dict, Tuple, List
from dataclasses import dataclass

import pyxel

from core import index_to_pos, dist, normalize, cast_ray

from dungeon_gen import (
    SIDE,
    create_matrix,
    Board,
    Matrix,
    Position,
    Level,
    generate_level,
    create_board,
    WALLS,
    is_door,
    is_wall,
)


CELL_SIZE = 8


@dataclass
class State:
    max_range = 5
    player: Tuple[float, float]
    orientation = 1
    board: Board
    in_range = List[int]
    camera: Tuple[float, float]
    visible = List[int]

    def to_cam_space(self, pos: Tuple[float, float]):
        px, py = pos
        cx, cy = self.camera
        return px - cx, py - cy


def update(state: State) -> State:
    dx: float
    dy: float

    dx, dy = 0, 0
    step = 0.08

    if pyxel.btn(pyxel.KEY_DOWN):
        dy += step
    if pyxel.btn(pyxel.KEY_UP):
        dy -= step
    if pyxel.btn(pyxel.KEY_LEFT):
        state.orientation = -1
        dx -= step
    if pyxel.btn(pyxel.KEY_RIGHT):
        state.orientation = 1
        dx += step

    x, y = state.player
    state.player = x + dx, y + dy

    px, py = state.player
    cx, cy = state.camera

    # store in-range block indices
    max_range = state.max_range
    state.in_range = []
    for i in range(len(state.board)):
        x, y = index_to_pos(i, SIDE)
        center = x + 0.5, y + 0.5
        if dist(center, state.player) < max_range * 2:
            state.in_range.append(i)

    # Move camera if needed
    lthreshold = 6
    rthreshold = 10
    cx = px - lthreshold if px - cx < lthreshold else cx
    cx = px - rthreshold if px - cx > rthreshold else cx
    cy = py - lthreshold if py - cy < lthreshold else cy
    cy = py - rthreshold if py - cy > rthreshold else cy
    state.camera = cx, cy

    def ray_dirs(i):
        px, py = state.player
        c, l = index_to_pos(i, SIDE)
        return [
            (x - px, y - py)
            for x, y in [
                (c + 0.5, l),
                (c + 1, l + 0.5),
                (c + 0.5, l + 1),
                (c, l + 0.5),
            ]
        ]

    def hit_wall(x, y):
        return (
            state.board.outside(x, y)
            or is_wall(state.board.get(x, y))
            or dist(state.player, (x, y)) > state.max_range
            or is_door(state.board.get(x, y))
        )

    rays = sum([ray_dirs(i) for i in state.in_range], [])
    state.visible = []
    for r in rays:
        trav, hit, _ = cast_ray(state.player, r, hit_wall)
        state.visible += trav
        if not state.board.outside(*hit):
            state.visible.append(hit)

    return state


YES = (0, 32)
NO = (8, 32)


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

    cx, cy = state.camera

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

    x, y = state.to_cam_space(state.player)
    u, v = player_sprite
    pyxel.blt(
        x * CELL_SIZE - CELL_SIZE / 2,
        y * CELL_SIZE - CELL_SIZE / 2,
        0,
        u,
        v,
        CELL_SIZE * state.orientation,
        CELL_SIZE,
        5,
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

    state = State(board=m, camera=(0, 0), player=(0, 0))
    pyxel.init(128, 128)
    pyxel.load("my_resource.pyxres")
    # pyxel.run(partial(update_debug, state), partial(draw_debug, state))
    pyxel.run(partial(update, state), partial(draw, state))


if __name__ == "__main__":
    main()
