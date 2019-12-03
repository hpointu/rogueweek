import random
import pyxel

import math
from math import sin, cos

from rogue import tween
from rogue.core import Particle, normalize, dist, ITEMS, line, State
from rogue.constants import CELL_SIZE, FPS


class DamageText(Particle):
    def __init__(self, text, pos, color):
        self.text = text
        self.color = color
        x, y = pos
        self._path = list(
            tween.tween(pos, (x, y - 10), 45, tween.EASE_OUT_QUAD)
        )

    def update(self, state):
        self._path.pop(0)

    @property
    def pos(self):
        return self._path[0]

    def living(self):
        return bool(self._path)

    def draw(self, state):
        pyxel.text(*self.pos, self.text, self.color)


class Glitter(Particle):
    def __init__(self, pos):
        x, y = pos
        direction = 0, 0
        while direction == (0, 0):
            direction = random.randint(-10, 10), random.randint(-10, 10)
        direction = normalize(direction)
        distance = random.randint(5, 20) / 10
        dx, dy = map((lambda x: x * distance), direction)
        self._path = list(
            tween.tween(pos, (x + dx, y + dy), 20, tween.EASE_IN_QUAD)
        )
        self.color = random.choice([6, 7, 12])

    def update(self, state):
        self._path.pop(0)

    def living(self):
        return bool(self._path)

    @property
    def pos(self):
        return self._path[0]

    def draw(self, state):
        pyxel.pix(*state.to_pixel(self.pos, CELL_SIZE), self.color)


class Ash(Particle):
    def __init__(self, pos, color, life):
        self.pos = pos
        self.color = color
        self.life = life

    def update(self, state):
        self.life -= 1

    def living(self):
        return self.life > 0

    def draw(self, state):
        x, y = state.to_pixel(self.pos, CELL_SIZE)
        pyxel.pix(x, y, self.color)


class Projectile(Particle):
    sprite = ITEMS["flare"]
    ashes = [3, 11]

    def __init__(self, start, end, callback=None):
        speed = 1 / 15
        d = dist(start, end)
        self._path = list(tween.tween(start, end, int(speed * d * FPS)))
        self._callback = callback

    def update(self, state):
        # ashes
        n = random.randint(1, 3)
        for i in range(n):
            col = random.choice(self.ashes)
            x, y = self.pos
            x += random.randint(0, 50) / 100 + 0.25
            y += random.randint(0, 50) / 100 + 0.25
            life = random.randint(10, 30) / 100 * FPS
            state.particles.append(Ash((x, y), col, life))

        self._path.pop(0)

        if self._callback and not self._path:
            self._callback(self)
            self._callback = None

    def draw(self, state):
        x, y = state.to_pixel(self.pos, CELL_SIZE)
        pyxel.blt(x, y, 0, *self.sprite)

    @property
    def pos(self):
        return self._path[0]

    def living(self):
        return bool(self._path)


class SleepBullet(Projectile):
    sprite = ITEMS["sleep_bullet"]
    ashes = [13, 14]


class FakeFountain(Particle):
    def __init__(self, pos):
        self.pos = pos

    def update(self, state):
        state.particles.append(Glitter(self.pos))

    def living(self):
        return False


class Molecule(Particle):
    def __init__(self, start, end, frames):
        x, y = start
        direction = 0, 0
        while direction == (0, 0):
            direction = random.randint(-10, 10), random.randint(-10, 10)
        direction = normalize(direction)
        distance = random.randint(10, 30) / 10
        dx, dy = map((lambda x: x * distance), direction)
        climax = (x + dx, y + dy)
        self._path = list(
            tween.tween(start, climax, frames // 2, tween.EASE_OUT_QUAD)
        )
        self._path += list(
            tween.tween(climax, end, frames // 2, tween.EASE_IN_QUAD)
        )
        self.color = random.choice([3, 7, 9, 15, 3])

    def living(self):
        return bool(self._path)

    def update(self, state):
        self._path.pop(0)

    @property
    def pos(self):
        return self._path[0]

    def draw(self, state):
        pyxel.pix(*state.to_pixel(self.pos, CELL_SIZE), self.color)


class Aura(Particle):
    def __init__(self, center):
        self._center = center
        r = random.randint(0, 10) / 100
        t = random.choice(
            [r, math.pi / 2 + r, math.pi + r, math.pi * 3 / 2 + r]
        )
        # t = random.choice([r, math.pi + r])
        self._path = list(tween.tween((2 + r, 2 * math.pi + t), (r, t), 20))
        self._color = random.choice([8, 14])

    @property
    def pos(self):
        r, theta = self._path[0]
        x, y = self._center
        dx, dy = r * cos(theta), r * sin(theta)
        return x + dx, y + dy

    def living(self):
        return bool(self._path)

    def update(self, state):
        self._path.pop(0)

    def draw(self, state):
        pyxel.pix(*state.to_pixel(self.pos, CELL_SIZE), self._color)


def rwalk(a, b):
    d = int(dist(a, b) / CELL_SIZE) + 2
    path = list(tween.tween(a, b, d))

    def _distort(p):
        x, y = p
        delta = random.gauss(0, CELL_SIZE / 3)
        nx, ny = normalize((y, -x))
        dx = nx * delta
        dy = ny * delta

        return x + dx, y + dy

    return [_distort(p) for p in path[:-1]] + [path[-1]]


def _center(pos):
    return pos[0] + 0.5, pos[1] + 0.5


class Pixel(Particle):
    def __init__(self, pos, col, life):
        self.pos = pos
        self.col = col
        self.life = life

    def living(self):
        return self.life > 0

    def draw(self, state):
        pyxel.pix(*self.pos, self.col)

    def update(self, state):
        self.life -= 1


class Thunder(Particle):
    _cpt = 30

    def __init__(self, state: State, start, target, callback):
        self.callback = callback
        start = state.to_pixel(_center(start), CELL_SIZE)
        target = state.to_pixel(_center(target), CELL_SIZE)
        points = rwalk(start, target)
        path = []
        for p in points:
            p = tuple(map(int, p))
            path += line(start, p)
            start = p
        self._path = path

    def update(self, state):
        self._cpt -= 1
        for _ in range(8):
            if self._path:
                state.particles.append(
                    Pixel(self._path.pop(0), random.choice([7, 12]), 8)
                )

        if not self._path:
            self.callback(8)

    def draw(self, state):
        pass

    def living(self):
        return bool(self._path)
