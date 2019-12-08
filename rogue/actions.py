import pyxel
from rogue.constants import CELL_SIZE
from rogue.core import State
from rogue.core import pos_to_index
from rogue.dungeon_gen import encode_floor, is_empty
from rogue.particles import DamageText


def end_turn(state: State, n: int = 1):
    def _do(caller):
        nonlocal n
        n -= 1
        if n < 1:
            state.player_turn = not state.player_turn
            g = "player" if state.player_turn else "game"
            print("----")
            print(f"{g} turn")
        return state

    return _do


def unlock_door(state, target):
    val = state.board.get(*target)
    state.player.keys -= 1
    state.board.set(*target, val - 5)


def open_door(state, target):
    # remove door
    state.board.set(*target, 0)

    # rencode floor
    i = pos_to_index(*target, state.board.side)
    floor = encode_floor(state.board, i)
    state.board.set(*target, floor)

    botx, boty = target
    boty += 1
    # might rencode floor below
    if is_empty(state.board.get(botx, boty)):
        i = pos_to_index(botx, boty, state.board.side)
        floor = encode_floor(state.board, i)
        state.board.set(botx, boty, floor)
