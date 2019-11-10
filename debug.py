import pyxel

from core import index_to_pos, State
from dungeon_gen import M_SIZE, MAX_ROOM_SIZE, is_wall, is_door

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
            col = 8
        else:
            col = 7
        pyxel.rect(x * U + OFF, y * U + OFF, U, U, col)
        if i in extras[0]:
            pyxel.pix(x * U + 1 + OFF, y * U + 1 + OFF, 9)

    outline_room(state, state.level.start_room, 12)
    outline_room(state, state.level.final_rooms[0], 14)
    outline_room(state, state.level.final_rooms[1], 3)
    outline_room(state, state.level.final_rooms[2], 3)
