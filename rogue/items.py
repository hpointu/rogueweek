import pyxel
from functools import partial
from rogue.constants import MAX_PV
from rogue.core import LevelItem, State
from rogue.player import Player
from rogue.misc import TextBox


def _add_key(state: State) -> State:
    def _add(s):
        s.player.keys += 1

    state.text_box = TextBox("key", "You can unlock a door!", _add)
    pyxel.play(3, 52)
    return state


FLAGS_TEXT_BOX = {
    "teleport": "This scrolls seems to teach how to travel... Through... What?",
    "wand": "What is that stick? What if you point it to someone's direction?",
    "thunder": "You're full of electricity!",
    "armor": "Wow! You feel like you're stronger...",
    "triA": "You found a weird stone. It seems to be missing a part.",
    "triB": "You found a weird stone. It seems to be missing a part.",
    "tri": "",
}


def _add_flag(flag: str, state: State) -> State:
    state.text_box = TextBox(
        flag, FLAGS_TEXT_BOX[flag], lambda s: s.player.flags.add(flag)
    )
    pyxel.play(3, 52)
    return state


def _heal(flag: str, state: State) -> State:
    state.player.pv = MAX_PV
    return state


ADD_KEY = _add_key
VIAL = _heal
TELEPORT_SPELL = partial(_add_flag, "teleport")
MAGIC_WAND = partial(_add_flag, "wand")
ARMOR = partial(_add_flag, "armor")
THUNDER = partial(_add_flag, "thunder")
TRI_A = partial(_add_flag, "triA")
TRI_B = partial(_add_flag, "triB")


class Chest(LevelItem):
    def __init__(self, content_fn, *args, **kw):
        super().__init__(*args, **kw)
        self.content_fn = content_fn
        self.sprite_id = "chest"

    def interact(self, state: State):
        state = self.content_fn(state)
        # I know...
        state.level.items.remove(self)


class Book(LevelItem):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.sprite_id = "book"

    def interact(self, state: State):
        state.text_box = TextBox("book", "You found the book! Well done")
