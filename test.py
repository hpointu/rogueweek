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


CELL_SIZE = 4

State = Dict[Any, Any]


def update(state: State):
    pass


def draw_matrix(matrix: Matrix):

    # draw cells
    for i in range(M_SIZE):
        for j in range(M_SIZE):
            pyxel.rect(j * 16, i * 16, 8, 8, 7)

    # draw paths
    for a, b in matrix:
        l1, c1 = int(a / M_SIZE), int(a % M_SIZE)
        l2, c2 = int(b / M_SIZE), int(b % M_SIZE)
        pyxel.line(c1 * 16 + 4, l1 * 16 + 4, c2 * 16 + 4, l2 * 16 + 4, 7)


def draw(state: Any):
    pyxel.cls(0)

    for i, v in enumerate(state):
        col = i % (M_SIZE * MAX_ROOM_SIZE)
        lin = int(i / (M_SIZE * MAX_ROOM_SIZE))
        pyxel.rect(
            col * CELL_SIZE,
            lin * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE,
            7 if v else 1,
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
