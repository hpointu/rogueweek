import pyxel
from functools import partial
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
    "teleport": "You can now teleport!",
    "wand": "You can shoot at enemies!",
}


def _add_flag(flag: str, state: State) -> State:
    state.text_box = TextBox(
        flag, FLAGS_TEXT_BOX[flag], lambda s: s.player.flags.add(flag)
    )
    pyxel.play(3, 52)
    return state


ADD_KEY = _add_key
TELEPORT_SPELL = partial(_add_flag, "teleport")
MAGIC_WAND = partial(_add_flag, "wand")


class Chest(LevelItem):
    def __init__(self, content_fn, *args, **kw):
        super().__init__(*args, **kw)
        self.content_fn = content_fn
        self.sprite_id = "chest"

    def interact(self, state: State):
        state = self.content_fn(state)
        # I know...
        state.level.items.remove(self)
