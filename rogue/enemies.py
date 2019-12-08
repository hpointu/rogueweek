import pyxel
import random
from functools import partial


from rogue.constants import FPS, CELL_SIZE, TPV, DType
from rogue.core import is_empty, dist, LEFT, RIGHT, ANIMATED
from rogue.core import AIActor, ActionReport, State, Board, AnimSprite
from rogue.particles import Projectile, DamageText, BossMolecule
from rogue.items import Book


def _center(pos):
    return pos[0] + 0.5, pos[1] + 0.5


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

    def __init__(self, pos, parent=None):
        super().__init__(pos, 9003)
        self.parent = parent

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return straight_line(state, self, end_turn_fn)


class Bat(AIActor):
    pv = 1
    strength = 1

    def __init__(self, pos):
        super().__init__(pos, 9005)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        return random_move(state, self, end_turn_fn)


class Shooter(AIActor):
    def shoot(self, state, target, callback):
        self._callback = callback

        def apply_damage(source):
            damage = self.strength
            target.hurt(damage)
            ppos = state.to_pixel(target.pos, CELL_SIZE)
            state.particles.append(DamageText(f"-{damage}", ppos, 8))
            pyxel.play(2, 50)
            self.end_turn()

        pyxel.play(3, 56)
        state.particles.append(Projectile(self.pos, target.pos, apply_damage))


class Necromancer(Shooter):
    pv = 16
    strength = 4
    zindex = 2
    cooldown_shoot = 2
    cooldown_spawn = 1
    should_tp = False
    met_already = False
    state_ref = None

    def __init__(self, pos, room):
        super().__init__(pos, 9999)
        self._base_sprite = self.sprite
        self._teleport_sprite = AnimSprite(*ANIMATED[9010])
        self._invoke_sprite = AnimSprite(*ANIMATED[9888])
        self.room = room

    def pick_free_spot(self, state):
        from rogue.dungeon_gen import room_anchor

        (w, h), _ = state.level.rooms[self.room]
        ax, ay = room_anchor(self.room)
        x, y = self.pos

        def _occupied(x, y):
            return bool(state.get_entity(x, y))

        cpt = 0
        while _occupied(x, y):
            x = ax + random.randrange(0, w)
            y = ay + random.randrange(0, h)
            cpt += 1
            if cpt > 10:
                print("oups, occupied")

        return x, y

    def spawn_skel(self, state):
        pos = self.pick_free_spot(state)
        return Skeleton(pos, self)

    def _do_spawn(self, state, caller, *, end):
        for _ in range(3):
            state.enemies.append(self.spawn_skel(state))
        self.sprite = self._base_sprite
        self.sprite.play()
        end(caller)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        self.state_ref = state
        if not self.square in state.visible:
            return self.wait(1, end_turn_fn)
        elif not self.met_already:
            pyxel.playm(1, loop=True)
            self.met_already = True

        skels = [e for e in state.enemies if e.parent == self]
        can_invoke = not skels and self.cooldown_spawn < 1

        if not skels:
            self.sprite.stop()
            self.cooldown_spawn -= 1
        elif not self.should_tp:
            return self.wait(1, end_turn_fn)

        self.cooldown_shoot -= 1

        if self.should_tp:
            pos = state.player.pos
            while dist(pos, state.player.pos) < 4:
                pos = self.pick_free_spot(state)
            for _ in range(50):
                state.particles.append(
                    BossMolecule(_center(self.pos), _center(pos), TPV)
                )
            self.sprite = self._teleport_sprite
            self.should_tp = False
            return self.move(*pos, end_turn_fn, TPV)

        elif can_invoke:
            self.cooldown_spawn = 4
            self.sprite = self._invoke_sprite
            self.sprite.play()
            pyxel.play(3, 3)
            return self.wait(
                16, partial(self._do_spawn, state, end=end_turn_fn)
            )

        elif self.cooldown_shoot < 1:
            self.cooldown_shoot = 2
            return self.shoot(state, state.player, end_turn_fn)

        return random_move(state, self, end_turn_fn)

    @property
    def orientation(self):
        return -1 if self._orient == LEFT else 1

    def end_turn(self):
        super().end_turn()
        self.sprite = self._base_sprite

    def hurt(self, damage, dtype=DType.MELEE):
        super().hurt(damage, dtype)
        if dtype == DType.MELEE:
            self.should_tp = True

        if self.pv < 1:
            pyxel.stop()
            pyxel.playm(2, loop=True)
            for e in self.state_ref.enemies:
                if e.parent == self:
                    e.hurt(10)
            self.state_ref.level.items.append(Book(square=self.square))

class Plant(Shooter):
    zindex = 1
    pv = 1
    strength = 1

    def __init__(self, pos):
        super().__init__(pos, 9004)

    def take_action(self, state: State, end_turn_fn) -> ActionReport:
        if self.square in state.visible:
            self.shoot(state, state.player, end_turn_fn)
            return

        return self.wait(1, end_turn_fn)
