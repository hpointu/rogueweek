import pyxel
from rogue.core import Actor, AnimSprite, ANIMATED, dist
from rogue.constants import CELL_SIZE
from rogue.particles import Thunder, DamageText


class Player(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = 0
        self._base_sprite = self.sprite
        self._teleport_sprite = AnimSprite(*ANIMATED[9010])

    def move(self, *a, **kw):
        super().move(*a, **kw)
        self.sprite.play()

    def teleport(self, *a, **kw):
        self.sprite = self._teleport_sprite
        self.move(*a, **kw)

    def wait(self, *a, **kw):
        super().wait(*a, **kw)
        self.sprite.play()

    def attack(self, *a, **kw):
        r = super().attack(*a, **kw)
        self.sprite.play()
        return r

    def thunder(self, state, e1, e2, end_fn, touched=None):

        touched = touched or {e2}

        def _apply_damage(source, delay):
            damage = 1
            e2.pv -= damage
            ppos = state.to_pixel(e2.pos, CELL_SIZE)
            state.particles.append(DamageText(f"-{damage}", ppos, 12))
            pyxel.play(2, 50)

            near = [
                e
                for e in state.enemies
                if dist(e.pos, e2.pos) < 3 and e not in touched
            ]
            for n in near:
                self.thunder(state, e2, n, end_fn, touched | {n})

            if not near:
                self.wait(delay, end_fn)

        def _apply_thunder(cpt, source):
            def _apply(delay):
                nonlocal cpt
                cpt -= 1
                if cpt <= 0:
                    _apply_damage(source, delay)

            return _apply

        from rogue.particles import Thunder

        cb = _apply_thunder(2, e1)
        state.particles.append(Thunder(state, e1.square, e2.square, cb))
        state.particles.append(Thunder(state, e1.square, e2.square, cb))

    def end_turn(self):
        super().end_turn()
        self.sprite.stop()
        self.sprite = self._base_sprite
