import random
import pyxel

from rogue import tween
from rogue.core import Particle, normalize
from rogue.constants import CELL_SIZE


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
