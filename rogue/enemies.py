import pyxel
import random
from functools import partial


from rogue.constants import FPS, CELL_SIZE
from rogue.core import is_empty, dist
from rogue.core import AIActor, ActionReport, State, Board
from rogue.particles import Projectile, DamageText


def can_walk(board: Board, x, y) -> bool:
    return not board.outside(x, y) and is_empty(board.get(x, y))


def straight_line(state: State, e: AIActor, end_turn) -> ActionReport:
    possible = [
        n
        for n in state.board.neighbours(*e.pos)
        if can_walk(state.board, *n) and n not in state.occupied
    ]
    if e.square in state.visible and possible:
        possible = sorted(possible, key=lambda x: dist(x, state.player.square))
        if possible[0] == state.player.square:
            return e.attack(state.player, end_turn)
        else:
            x, y = possible[0]
            e.move(x, y, end_turn)
            return x, y
    else:
        if possible:
            x, y = random.choice(possible)
            e.move(x, y, end_turn, 1)
            return x, y
        else:
            e.wait(10, end_turn)
    return None


def random_move(state: State, e: AIActor, end_turn) -> ActionReport:
    possible = [
        n
        for n in state.board.neighbours(*e.pos)
        if can_walk(state.board, *n) and n not in state.occupied
    ]

    speed = int(0.3 * FPS) if e.square in state.visible else 1

    if not possible:
        return e.wait(speed, end_turn)

    if state.player.square in possible:
        return e.attack(state.player, end_turn)

    x, y = random.choice(possible)
    e.move(x, y, end_turn, speed)

    return x, y


class Slug(AIActor):
    pv = 2
    strength = 2

    def __init__(self, pos):
        super().__init__(pos, 9001)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return random_move(state, self, end_turn_fn)


class Ghost(AIActor):
    pv = 3
    strength = 2

    def __init__(self, pos):
        super().__init__(pos, 9002)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return straight_line(state, self, end_turn_fn)


class Skeleton(AIActor):
    pv = 4
    strength = 2

    def __init__(self, pos):
        super().__init__(pos, 9003)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return straight_line(state, self, end_turn_fn)


class Bat(AIActor):
    pv = 1
    strength = 1

    def __init__(self, pos):
        super().__init__(pos, 9005)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return random_move(state, self, end_turn_fn)


class Plant(AIActor):
    pv = 1
    strength = 1

    def __init__(self, pos):
        super().__init__(pos, 9004)

    def shoot(self, state, target, callback):
        self._callback = callback

        def apply_damage(source):
            damage = self.strength
            target.pv -= damage
            ppos = state.to_pixel(target.pos, CELL_SIZE)
            state.particles.append(DamageText(f"-{damage}", ppos, 8))
            pyxel.play(2, 50)
            self.end_turn()

        pyxel.play(3, 56)
        state.particles.append(Projectile(self.pos, target.pos, apply_damage))

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        if self.square in state.visible:
            self.shoot(state, state.player, end_turn_fn)
            return

        return self.wait(1, end_turn_fn)
