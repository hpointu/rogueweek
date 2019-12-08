import pyxel
from collections import defaultdict
from rogue.core import Actor, AnimSprite, ANIMATED, dist, LEFT, RIGHT
from rogue.constants import CELL_SIZE, DType
from rogue.particles import Thunder, DamageText, Projectile


class Player(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = 0
        self._base_sprite = self.sprite
        self._teleport_sprite = AnimSprite(*ANIMATED[9010])

        self._cooldown = defaultdict(lambda: 0)

    def move(self, *a, **kw):
        super().move(*a, **kw)
        self.sprite.play()

    def hurt(self, damage, dtype=DType.MELEE):
        if "armor" in self.flags:
            damage //= 2
        super().hurt(damage, dtype)

    def teleport(self, *a, **kw):
        self._cooldown["teleport"] = 4
        self.sprite = self._teleport_sprite
        self.move(*a, **kw)

    def wait(self, *a, **kw):
        super().wait(*a, **kw)
        self.sprite.play()

    def attack(self, *a, **kw):
        r = super().attack(*a, **kw)
        self.sprite.play()
        return r

    def shoot(self, state, target, callback):
        self._cooldown["wand"] = 4
        self._callback = callback

        def apply_damage(source):
            damage = 2
            target.hurt(damage)
            ppos = state.to_pixel(target.pos, CELL_SIZE)
            state.particles.append(DamageText(f"-{damage}", ppos, 12))
            pyxel.play(2, 50)
            self.end_turn()

        pyxel.play(3, 56)
        state.particles.append(Projectile(self.pos, target.pos, apply_damage))

    @property
    def orientation(self):
        return -1 if self._orient == LEFT else 1

    def thunder(self, state, e1, e2, end_fn, touched=None):
        self._cooldown["thunder"] = 5
        touched = touched or {e2}

        def _apply_damage(source, delay):
            damage = 1
            e2.hurt(damage, DType.THUNDER)
            ppos = state.to_pixel(e2.pos, CELL_SIZE)
            state.particles.append(DamageText(f"-{damage}", ppos, 12))
            pyxel.play(2, 50)

            near = [
                e
                for e in state.enemies
                if dist(e.pos, e2.pos) < 3 and e not in touched
            ]
            nt = touched | set(e for e in near)
            for n in near:
                self.thunder(state, e2, n, end_fn, nt)

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

    def cooldown(self, flag):
        return self._cooldown[flag]

    def end_turn(self):
        super().end_turn()
        self.sprite.stop()
        self.sprite = self._base_sprite

        for k, cd in self._cooldown.items():
            if self._cooldown[k]:
                self._cooldown[k] -= 1
