import random

from rogue.core import is_empty, dist
from rogue.core import AIActor, ActionReport, State, Board


def can_walk(board: Board, x, y) -> bool:
    return not board.outside(x, y) and is_empty(board.get(x, y))


def straight_line(state: State, e: AIActor, end_turn) -> ActionReport:
    possible = [
        n for n in state.board.neighbours(*e.pos) if can_walk(state.board, *n)
    ]
    if e.square in state.visible:
        possible = sorted(possible, key=lambda x: dist(x, state.player.square))
        if possible[0] == state.player.square:
            return e.attack(state.player, end_turn)
        else:
            x, y = possible[0]
            e.move(x, y, end_turn)
    else:
        if possible:
            x, y = random.choice(possible)
            e.move(x, y, end_turn, 1)
        else:
            e.wait(10, end_turn)
    return None


class Slug(AIActor):
    def __init__(self, pos):
        super().__init__(pos, 9001)

    # TODO Slug will only move random
    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return straight_line(state, self, end_turn_fn)


class Ghost(AIActor):
    def __init__(self, pos):
        super().__init__(pos, 9002)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return straight_line(state, self, end_turn_fn)


class Skeleton(AIActor):
    def __init__(self, pos):
        super().__init__(pos, 9003)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return straight_line(state, self, end_turn_fn)
