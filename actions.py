from core import Action, State, VecF
from core import dist, pos_to_index
from dungeon_gen import encode_floor, is_empty


def wait(state: State) -> State:
    return state


def move_to(target) -> Action:
    def _move(state: State) -> State:
        state.player = target
        return state

    return _move


def open_door(target) -> Action:
    def _open(state: State) -> State:
        state.board.set(*target, 0)
        i = pos_to_index(*target, state.board.side)
        floor = encode_floor(state.board, i)
        state.board.set(*target, floor)

        botx, boty = target
        boty += 1
        if is_empty(state.board.get(botx, boty)):
            i = pos_to_index(botx, boty, state.board.side)
            floor = encode_floor(state.board, i)
            state.board.set(botx, boty, floor)
        return state

    return _open
