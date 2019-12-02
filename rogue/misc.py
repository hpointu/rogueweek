import pyxel
import random
from textwrap import wrap
from rogue.core import ITEMS


class TextBox:
    def __init__(self, icon, text, close_callback=None):
        self.icon = icon
        self.text = text
        self._cb = close_callback

    def draw(self, state):
        lines = wrap(self.text, 16)
        pyxel.rect(20, 38, 88, 10 + 8*len(lines), 0)
        pyxel.rectb(20, 38, 88, 10 + 8*len(lines), 6)
        pyxel.blt(25, 44, 0, *ITEMS[self.icon])
        for i, l in enumerate(lines):
            pyxel.text(38, 43 + i * 8, l, 6)

    def update(self, state):
        if pyxel.btnr(pyxel.KEY_C) or pyxel.btnr(pyxel.KEY_X):
            if self._cb is not None:
                self._cb(state)
            state.text_box = None


def rwalk_freed(pos, target):
    x, y = pos
    tx, ty = target

    path = [pos]
    while (x, y) != target:
        dx, dy = tx - x, ty - y
        dx = dx // dx if dx else dx
        dy = dy // dy if dy else dy
        i = random.randint(1, 3)
        if i & 1:
            x += dx
        if i & 2:
            y += dy
        path.append((x, y))

    return path


def rwalk_antoine(pos, target):
    x, y = pos
    tx, ty = target

    path = [pos]
    while (x, y) != target:
        dx, dy = tx - x, ty - y
        dx = dx // dx if dx else dx
        dy = dy // dy if dy else dy
        i = random.randint(1, 3)
        if i & 1:
            proba = random.randint(0,9)
            if proba == 0:
                x -= dx
            else:
                x += dx
        if i & 2:
            proba = random.randint(0,9)
            if proba == 0:
                y -= dy
            else:
                y += dy

        path.append((x, y))

    return path


def rwalk(pos, target):
    x, y = pos
    tx, ty = target

    path = [pos]

    while (x, y) != target:
        dx, dy = tx - x, ty - y
        dx = 1 if dx > 0 else -1
        dy = 1 if dy > 0 else -1

        if abs(dx) <= abs(dy):
            dy = random.choice([dy, dy, -dy])
        else:
            dx = random.choice([dx, dx, -dx])

        x += dx
        y += dy
        path.append((x, y))

    return path
