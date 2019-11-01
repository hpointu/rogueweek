from functools import partial
from typing import Any, Dict

import pyxel

from dungeon_gen import (
    M_SIZE,
    MAX_ROOM_SIZE,
    create_matrix,
    Matrix,
    Level,
    generate_level,
    create_map,
)


CELL_SIZE = 3

State = Dict[Any, Any]


def update(state: State):
    pass


def draw(state: Any):
    pyxel.cls(0)

    colors = {
        0: 7,
        1: 0,
        2: 8,
        3: 3,
    }

    for i, v in enumerate(state):
        col = i % (M_SIZE * MAX_ROOM_SIZE)
        lin = int(i / (M_SIZE * MAX_ROOM_SIZE))
        pyxel.rect(
            col * CELL_SIZE,
            lin * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
            colors[v],
        )

    # draw_matrix(state.matrix)

    # # draw room sizes
    # for i, room in enumerate(state.rooms):
    #     l, c = int(i / M_SIZE), int(i % M_SIZE)
    #     pyxel.text(c * 16, l * 16, f"({room[0]},{room[1]})", 8)


def main():
    level = generate_level(create_matrix())
    m = create_map(level)

    state = m
    pyxel.init(160, 120)
    pyxel.run(partial(update, state), partial(draw, state))


if __name__ == "__main__":
    main()
