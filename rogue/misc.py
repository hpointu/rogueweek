import pyxel
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
