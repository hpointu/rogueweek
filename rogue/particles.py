import random
import pyxel

from rogue import tween
from rogue.core import Particle, normalize, dist, ITEMS
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
    def __init__(self, start, end, callback=None):
        speed = 1/15
        d = dist(start, end)
        self._path = list(tween.tween(start, end, int(speed * d * FPS)))
        self._callback = callback

    def update(self, state):
        # ashes
        n = random.randint(1, 3)
        for i in range(n):
            col = random.choice([3, 11])
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
        pyxel.blt(x, y, 0, *ITEMS['flare'])

    @property
    def pos(self):
        return self._path[0]

    def living(self):
        return bool(self._path)

