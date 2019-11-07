from core import Action, State, VecF
from core import dist


def wait(state: State) -> State:
    return state


def move_to(target) -> State:
    def _move(state):
        state.player = target
        return state
    return _move
