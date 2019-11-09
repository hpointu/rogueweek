import pyxel

from core import index_to_pos, State
from dungeon_gen import M_SIZE, MAX_ROOM_SIZE, is_wall, is_door

U = 3


def update_debug(state: State):
    pass


def outline_room(state, room_index, color):
    x, y = index_to_pos(room_index, M_SIZE)
    size = state.level.rooms[room_index][0]
    pyxel.rectb(
        x * U * 8, y * U * MAX_ROOM_SIZE, size[0] * U, size[1] * U, color
    )
    pass


def draw_debug(state: State):
    pyxel.cls(0)
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

    outline_room(state, state.level.start_room, 12)
    outline_room(state, state.level.final_room, 14)
