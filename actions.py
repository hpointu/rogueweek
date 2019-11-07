from itertools import zip_longest
from core import Action, State, VecF
from core import dist, pos_to_index
from dungeon_gen import encode_floor, is_empty


def end_turn(state: State):
    def _do(caller):
        state.player_turn = not state.player_turn
        print(f"to_play: {'player' if state.player_turn else 'game'}")
        return state

    return _do


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
