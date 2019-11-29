import pyxel
import random

from functools import partial

from rogue import debug

from rogue.actions import end_turn, open_door, unlock_door

from rogue.core import ITEMS, LevelItem
from rogue.core import Board, State, Player, VecF
from rogue.core import dist, index_to_pos, cast_ray
from rogue.core import is_empty, is_wall, is_door, is_locked, is_hole

from rogue.dungeon_gen import (
    generate_level,
    populate_enemies,
    basic_scenario,
    room_anchor,
)

from rogue.particles import DamageText, Projectile, Molecule, Aura

from rogue.constants import CELL_SIZE, FPS, TPV
from rogue.sprites import WALLS

from typing import List, Optional


MENU = [
    ("Do this", lambda x: print("do this")),
    ("Eat", lambda x: print("eat")),
    ("Do that", lambda x: print("that")),
    ("Exit", lambda x: print("EXIT")),
]


def draw_damage(state, pos, damage, color):
    ppos = state.to_pixel(pos, CELL_SIZE)
    state.particles.append(DamageText(f"-{damage}", ppos, color))


def apply_damage(state, entity, damage, end_fn, source):
    entity.pv -= damage
    draw_damage(state, entity.pos, damage, 12)
    pyxel.play(2, 50)
    state.aim = list()
    end_fn(source)


def _center(pos):
    return pos[0] + 0.5, pos[1] + 0.5


class KeyReg:

    _managed = [
        pyxel.KEY_LEFT,
        pyxel.KEY_RIGHT,
    ]

    def __init__(self):
        self._reg = {k: False for k in self._managed}
        self.clear_queue()

    def clear_queue(self):
        self.queue = list()

    def update(self):
        for k in self._managed:
            if pyxel.btn(k) and not self._reg[k]:
                self._reg[k] = True
                print(f"{k} pressed")

            if not pyxel.btn(k) and self._reg[k]:
                self._reg[k] = False
                print(f"{k} released")
                self.queue.append(k)


def can_walk(board: Board, x, y) -> bool:
    return not board.outside(x, y) and is_empty(board.get(x, y))


def find_entity(state, x, y):
    for e in state.enemies:
        if e.pos == (x, y):
            return e
    return None


def find_item(state, x, y) -> Optional[LevelItem]:
    for i in state.level.items:
        if i.square == (x, y):
            return i
    return None


def can_shoot(state) -> bool:
    return "wand" in state.player.flags


def can_teleport(state) -> bool:
    return "teleport" in state.player.flags


def update_menu(state: State):
    if pyxel.btnr(pyxel.KEY_UP):
        state.menu_item = max(state.menu_item - 1, 0)
        pyxel.play(3, 55)
    elif pyxel.btnr(pyxel.KEY_DOWN):
        state.menu_item = min(state.menu_item + 1, len(MENU) - 1)
        pyxel.play(3, 55)


def player_aiming(state: State):
    aim = state.aim

    if pyxel.btnr(pyxel.KEY_LEFT):
        state.aim = aim[-1:] + aim[:-1]
        pyxel.play(3, 55)
    elif pyxel.btnr(pyxel.KEY_RIGHT):
        state.aim = aim[1:] + aim[:1]
        pyxel.play(3, 55)

    return


def player_action(state: State):
    if state.player.is_busy():
        return

    x, y = state.player.square
    _end = end_turn(state)

    if pyxel.btnr(pyxel.KEY_C):
        if state.menu_item is None:
            state.menu_item = 0
            return
        else:
            menu_select = MENU[state.menu_item]
            state.menu_item = None
            return menu_select[1](state)

    #if can_shoot(state) and pyxel.btnr(pyxel.KEY_C):
    #    if state.aim:
    #        e = state.aim[0]
    #        fn = partial(apply_damage, state, e, 1, _end)
    #        state.particles.append(Projectile(state.player.pos, e.pos, fn))
    #        pyxel.play(3, 56)

    #    else:
    #        state.aim = sorted(
    #            [e for e in state.enemies if e.square in state.visible],
    #            key=lambda x: x.pos[0],
    #        )

    if state.menu_item is not None:
        return update_menu(state)
    elif state.active_tool is not None:
        return state.active_tool.update(state)
    elif pyxel.btn(pyxel.KEY_DOWN):
        delta = 0, 1
    elif pyxel.btn(pyxel.KEY_UP):
        delta = 0, -1
    elif pyxel.btn(pyxel.KEY_LEFT):
        delta = -1, 0
    elif pyxel.btn(pyxel.KEY_RIGHT):
        delta = 1, 0

    elif pyxel.btn(pyxel.KEY_SPACE):
        for _ in range(50):
            state.particles.append(Aura(_center(state.player.pos)))
        return
    else:
        return

    target = x + delta[0], y + delta[1]

    val = state.board.get(*target)
    entity = find_entity(state, *target)
    item = find_item(state, *target)

    if entity:
        a = state.player.attack(entity, _end)
        pyxel.play(3, 50)
        draw_damage(state, entity.pos, a, 12)
    elif item:
        item.interact(state)
        state.player.wait(FPS * 0.3, _end)
    elif can_walk(state.board, *target):
        state.player.move(*target, _end)
    elif is_door(val):
        if is_locked(state.board.get(*target)):
            if state.player.keys:
                unlock_door(state, target)
                pyxel.play(3, 53)
            else:
                pyxel.play(3, 54)
        else:
            open_door(state, target)
            pyxel.play(3, 49)
        state.player.wait(FPS * 0.3, _end)
    elif is_wall(val) or state.board.outside(*target):
        state.player.bump_to(target, _end)

    elif is_hole(val):
        if can_teleport(state):
            target = tuple(sum(e) for e in zip(target, delta))
            for _ in range(50):
                state.particles.append(
                    Molecule(_center(state.player.pos), _center(target), TPV)
                )
            state.player.teleport(*target, _end, TPV)
        else:
            state.player.bump_to(target, _end)
    else:
        state.player.wait(FPS * 0.3, _end)


def game_turn(state: State):
    if any(e.is_busy() for e in state.enemies):
        return
    _end = end_turn(state, len(state.enemies))
    for e in state.enemies:
        # Only damage report, so far. Might add more reporting
        report = e.take_action(state, _end)
        if report is not None:
            pyxel.play(3, 51)
            draw_damage(state, state.player.pos, report, 8)


def update(state: State) -> State:
    x, y = state.player.pos

    if state.player_turn:
        player_action(state)
    else:
        game_turn(state)

    state.player.update(state)

    # Move camera if needed
    px, py = state.player.pos
    cx, cy = state.camera
    lthreshold = 6
    rthreshold = 9
    cx = px - lthreshold if px - cx < lthreshold else cx
    cx = px - rthreshold if px - cx > rthreshold else cx
    cy = py - lthreshold if py - cy < lthreshold else cy
    cy = py - rthreshold if py - cy > rthreshold else cy
    state.camera = cx, cy

    deads_enemies = []
    for e in state.enemies:
        e.update(state)
        if e.pv < 1:
            deads_enemies.append(e)
    for d in deads_enemies:
        state.enemies.remove(d)

    deads_particles = []
    for p in state.particles:
        p.update(state)
        if not p.living():
            deads_particles.append(p)
    for dp in deads_particles:
        state.particles.remove(dp)

    # store in-range block indices
    max_range = state.max_range
    state.in_range = set()
    for i in range(len(state.board)):
        x, y = index_to_pos(i, state.board.side)
        center = x + 0.5, y + 0.5
        if dist(center, state.player.pos) < max_range * 2:
            state.in_range.add(i)

    # for i in range(3):
    #     state.particles.append(Glitter(state.player.pos))

    def ray_dirs(i):
        px, py = state.player.pos
        c, r = index_to_pos(i, state.board.side)
        return [
            (x - px, y - py)
            for x, y in [
                (c + 0.5, r),
                (c + 1, r + 0.5),
                (c + 0.5, r + 1),
                (c, r + 0.5),
            ]
            if x - px and y - py
        ]

    def hit_wall(x, y):
        return (
            state.board.outside(x, y)
            or is_wall(state.board.get(x, y))
            or dist(state.player.pos, (x, y)) > state.max_range
            or is_door(state.board.get(x, y))
        )

    rays: List[VecF] = sum([ray_dirs(i) for i in state.in_range], [])
    state.visible = set()
    for r in rays:
        trav, hit, _ = cast_ray((px + 0.5, py + 0.5), r, hit_wall)
        state.visible.update(trav)
        if not state.board.outside(*hit):
            state.visible.add(hit)


    return state


def draw(state: State):
    pyxel.cls(0)

    non_walls = {
        0: (32, 16),
        30: (40, 24),
        31: (0, 24),
        32: (8, 24),
        33: (16, 24),
        34: (40, 16),
        35: (48, 8),
        40: (40, 32),
        41: (32, 32),
        42: (32, 32),
        43: (32, 32),
        20: (48, 0),
        21: (56, 16),
        22: (56, 8),
        23: (56, 0),
        25: (64, 0),
        26: (72, 16),
        27: (72, 8),
        28: (72, 0),
    }

    # draw in range
    for x, y in state.visible:
        # for i in range(len(state.board)):
        #     x, y = index_to_pos(i, state.board.side)
        if state.board.outside(x, y):
            continue
        v = state.board.get(x, y)
        x, y = state.to_cam_space((x, y))
        colors = WALLS if is_wall(v) else non_walls
        u_, v_ = colors[v]
        pyxel.blt(
            x * CELL_SIZE, y * CELL_SIZE, 0, u_, v_, CELL_SIZE, CELL_SIZE
        )

    # draw collectibles and stuff
    for item in state.level.items:
        if item.square not in state.visible:
            continue
        x, y = state.to_cam_space(item.square)
        pyxel.blt(x * CELL_SIZE, y * CELL_SIZE, 0, *item.sprite)

    x, y = state.to_cam_space(state.player.pos)
    sp = state.player.sprite
    pyxel.blt(
        x * CELL_SIZE - sp.center[0],
        y * CELL_SIZE - sp.center[1],
        0,
        *sp.uv,
        CELL_SIZE * state.player.orientation,
        CELL_SIZE,
        1,
    )

    for enemy in state.enemies:
        if enemy.square not in state.visible:
            continue
        x, y = state.to_cam_space(enemy.pos)
        sp = enemy.sprite
        pyxel.blt(
            x * CELL_SIZE - sp.center[0],
            y * CELL_SIZE - sp.center[1],
            0,
            *sp.uv,
            *enemy.sprite.size,
            1,
        )

    for p in state.particles:
        p.draw(state)

    if state.aim:
        x, y = state.to_cam_space(state.aim[0].square)
        pyxel.blt(
            x * CELL_SIZE, y * CELL_SIZE + CELL_SIZE, 0, *ITEMS["select"]
        )

    # HUD
    pyxel.rect(3, 3, 2 * state.player.pv, 7, 2)
    pyxel.rect(3, 3, 2 * state.player.pv, 5, 8)
    pyxel.rect(4, 4, 2 * state.player.pv - 2, 1, 14)
    pyxel.rectb(2, 2, 42, 8, 1)

    for i in range(state.player.keys):
        pyxel.blt(3 + i * 7, 12, 0, *ITEMS["key"])

    for i, flag in enumerate(["wand", "teleport"]):
        if flag in state.player.flags:
            pyxel.blt(3 + i * 8, 20, 0, *ITEMS[flag])

    # MENU
    if state.menu_item is not None:
        h = 4 + len(MENU) * 8
        pyxel.rect(40, 40, 48, h, 0)
        pyxel.rectb(40, 40, 48, h, 2)

        for i, (item, _) in enumerate(MENU):
            pyxel.text(50, 43 + i * 8, item, 6)

        pyxel.blt(41, 42 + state.menu_item * 8, 0, *ITEMS["dot"])


class App:
    _debug: bool = False

    def __init__(self):
        level, board = basic_scenario(*generate_level())
        enemies = populate_enemies(level, board)

        # entrance = board.to_index(*room_anchor(level.final_rooms[0]))
        entrance = board.entrance

        self.state = State(
            level=level,
            board=board,
            camera=(0, 0),
            player=Player(board.to_pos(entrance), 9000),
            enemies=enemies,
        )
        self.state.player.flags.add("teleport")
        self.state.player.flags.add("wand")
        self.state.player.flags.add("thunder")

        self._draw = partial(draw, self.state)
        self._draw_debug = partial(debug.draw_debug, self.state)

        self._update = partial(update, self.state)
        self._update_debug = partial(debug.update_debug, self.state)

    def run(self):
        pyxel.init(128, 128)
        pyxel.load("my_resource.pyxres")
        pyxel.playm(0, loop=True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if pyxel.btnr(pyxel.KEY_D):
            self._debug = not self._debug

        if self._debug:
            self._update_debug()
        else:
            self._update()

    def draw(self):
        if self._debug:
            self._draw_debug()
        else:
            self._draw()


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
