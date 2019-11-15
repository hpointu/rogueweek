import pyxel

from rogue.core import index_to_pos, State
from rogue.dungeon_gen import (
    M_SIZE,
    MAX_ROOM_SIZE,
    is_wall,
    is_door,
    is_locked,
)

U = 3
OFF = 4


def update_debug(state: State):
    pass


def outline_room(state, room_index, color):
    x, y = index_to_pos(room_index, M_SIZE)
    size = state.level.rooms[room_index][0]
    pyxel.rectb(
        x * U * MAX_ROOM_SIZE + OFF,
        y * U * MAX_ROOM_SIZE + OFF,
        size[0] * U,
        size[1] * U,
        color,
    )
    pass


def draw_debug(state: State, *extras):
    pyxel.cls(0)
    for i in range(len(state.board)):
        x, y = index_to_pos(i, state.board.side)

        v = state.board[i]
        if is_wall(v):
            col = 0
        elif is_door(v):
            if is_locked(v):
                col = 8
            else:
                col = 13
        elif 40 <= v <45:
            col = 1
        elif state.board.entrance == i:
            col = 12
        else:
            col = 7
        pyxel.rect(x * U + OFF, y * U + OFF, U, U, col)
        # if i in extras[0]:
        #     pyxel.pix(x * U + 1 + OFF, y * U + 1 + OFF, 9)

    for i in state.level.items:
        x, y = i.square
        pyxel.rect(x * U + OFF, y * U + 1 + OFF, U, U, 9)

    outline_room(state, state.level.start_room, 12)
    outline_room(state, state.level.final_rooms[0], 14)
    for fr in state.level.final_rooms[1:]:
        outline_room(state, fr, 3)
