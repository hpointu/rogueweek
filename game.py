import pyxel
import random

from functools import partial

from rogue import debug
from rogue import misc

from rogue.actions import end_turn, open_door, unlock_door

from rogue.core import ITEMS, LevelItem, Tool, MenuItem
from rogue.core import Board, State, VecF, GridCoord
from rogue.core import dist, index_to_pos, cast_ray
from rogue.core import (
    is_empty,
    is_wall,
    is_door,
    is_locked,
    is_hole,
    is_active_tile,
)

from rogue.player import Player

from rogue.dungeon_gen import (
    generate_level,
    populate_enemies,
    level_1,
    level_2,
    level_3,
    room_anchor,
)

from rogue.particles import DamageText, Projectile, Molecule, Aura, Thunder

from rogue.constants import CELL_SIZE, FPS, TPV, STORY
from rogue.sprites import WALLS

from typing import List, Optional


def draw_damage(state, pos, damage, color):
    ppos = state.to_pixel(pos, CELL_SIZE)
    state.particles.append(DamageText(f"-{damage}", ppos, color))


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
    menu_ = menu(state)
    if pyxel.btnr(pyxel.KEY_UP):
        state.menu_index = max(state.menu_index - 1, 0)
        pyxel.play(3, 55)
    elif pyxel.btnr(pyxel.KEY_DOWN):
        state.menu_index = min(state.menu_index + 1, len(menu_) - 1)
        pyxel.play(3, 55)


def player_aiming(state: State):
    aim = state.aim
    return


class AimingTool(Tool):
    def __init__(self):
        self.aim = []

    def draw(self, state: State):
        if not self.aim:
            return
        x, y = state.to_cam_space(self.aim[0].square)
        pyxel.blt(
            x * CELL_SIZE, y * CELL_SIZE + CELL_SIZE, 0, *ITEMS["select"]
        )

    def update(self, state: State, end_fn):
        aim = self.aim

        if not aim:
            state.active_tool = None

        if pyxel.btnr(pyxel.KEY_X):
            state.active_tool = None

        elif pyxel.btnr(pyxel.KEY_C):
            self.use(state, end_fn)
            state.active_tool = None

        elif pyxel.btnr(pyxel.KEY_LEFT):
            self.aim = aim[-1:] + aim[:-1]
            pyxel.play(3, 55)

        elif pyxel.btnr(pyxel.KEY_RIGHT):
            self.aim = aim[1:] + aim[:1]
            pyxel.play(3, 55)


class Wand(AimingTool):
    def __init__(self, state):
        self.aim = sorted(
            [e for e in state.enemies if e.square in state.visible],
            key=lambda x: x.pos[0],
        )

    def use(self, state: State, end_fn):
        e = self.aim[0]
        print("Shooting")
        state.player.shoot(state, e, end_fn)

class Teleport(Tool):
    def __init__(self, state):
        self.pos = state.player.pos
        self.d = 0

    def use(self, state: State, end_fn):
        if (
            not is_empty(state.board.get(*self.pos))
            or self.pos not in state.visible
        ):
            return

        state.active_tool = None
        for _ in range(50):
            state.particles.append(
                Molecule(_center(state.player.pos), _center(self.pos), TPV)
            )
        state.player.teleport(*self.pos, end_fn, TPV)

    def update(self, state, end_fn):
        x, y = self.pos

        if pyxel.btnr(pyxel.KEY_LEFT):
            x -= 1
        elif pyxel.btnr(pyxel.KEY_DOWN):
            y += 1
        elif pyxel.btnr(pyxel.KEY_RIGHT):
            x += 1
        elif pyxel.btnr(pyxel.KEY_UP):
            y -= 1
        elif pyxel.btnr(pyxel.KEY_C):
            self.use(state, end_fn)

        px, py = state.player.pos
        d = abs(x - px) + abs(y - py)
        if d < 5:
            self.pos = x, y
            self.d = int(d)

    def draw(self, state: State):
        x, y = state.to_cam_space(self.pos)
        pyxel.text(
            x * CELL_SIZE + 2, y * CELL_SIZE + 4, str(self.d), 8,
        )


class ThunderTool:
    def update(self, state, end_fn):
        enemies = sorted(
            [
                e
                for e in state.enemies
                if e.square in state.visible
                and dist(state.player.pos, e.pos) < 5
            ],
            key=lambda e: dist(e.pos, state.player.pos),
        )
        if not enemies:
            state.text_box = misc.TextBox(
                "thunder", "There is no one in range"
            )
            target = None
        else:
            target = random.choice(enemies)

        state.active_tool = None
        if target:
            state.player.thunder(state, state.player, target, end_fn)

    def draw(self, state):
        pass


class Map:
    def update(self, state, end_fn):
        if pyxel.btnr(pyxel.KEY_X) or pyxel.btnr(pyxel.KEY_C):
            state.active_tool = None

    def draw(self, state):
        offx, offy = 48, 48
        pyxel.rect(offx - 5, offy - 5, 42, 42, 7)
        pyxel.rect(offx - 4, offy - 4, 40, 40, 0)
        pyxel.rect(offx - 2, offy - 2, 36, 36, 5)
        for x, y in state.visited:
            col = 7
            v = state.board.get(x, y)
            if is_door(v):
                col = 8 if is_locked(v) else 4
            elif is_wall(v):
                col = 1
            elif is_active_tile(v):
                col = 12
            pyxel.pix(offx + x, offy + y, col)
        x, y = state.player.pos
        pyxel.pix(offx + x, offy + y, 11)


def menu(state) -> List[MenuItem]:
    m = []

    def set_tool(t, s):
        s.active_tool = t

    m.append(("map", "Show Map", partial(set_tool, Map())))

    if "wand" in state.player.flags:
        m.append(("wand", "Shoot", partial(set_tool, Wand(state))))
    if "teleport" in state.player.flags:
        m.append(("teleport", "Teleport", partial(set_tool, Teleport(state))))
    if "thunder" in state.player.flags:
        m.append(("thunder", "Thunder", partial(set_tool, ThunderTool())))

    return m + [("exit", "Exit", lambda x: print("exit game"))]


def menu_item(state):
    menu_ = menu(state)
    return menu_[state.menu_index]


def player_action(state: State):
    if state.player.is_busy():
        return

    x, y = state.player.square
    _end = end_turn(state)

    if state.active_tool is not None:
        return state.active_tool.update(state, _end)
    elif pyxel.btnr(pyxel.KEY_X) and state.menu_index is not None:
        state.menu_index = None
        return
    elif pyxel.btnr(pyxel.KEY_C):
        if state.menu_index is None:
            state.menu_index = 0
            return
        else:
            menu_select = menu_item(state)
            if state.player.cooldown(menu_select[0]):
                return
            state.menu_index = None
            return menu_select[2](state)

    if state.menu_index is not None:
        return update_menu(state)

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

        def _change_level(val, caller):
            if val == 66:
                state.change_level(-1)
            elif val == 99:
                state.change_level(1)
            return _end(caller)

        if is_active_tile(val):
            state.player.move(*target, partial(_change_level, val))
        else:
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
    print("Game playing...")
    _end = end_turn(state, len(state.enemies))
    if not state.enemies:
        _end(None)
    state.occupied = set(e.square for e in state.enemies)
    for e in state.enemies:
        # report is either None, or a Pos or a Damage
        report = e.take_action(state, _end)
        if isinstance(report, int):
            pyxel.play(3, 51)
            draw_damage(state, state.player.pos, report, 8)
        elif report is not None:
            # then they moved
            state.occupied.add(report)


def update(state: State) -> State:
    x, y = state.player.pos

    deads_enemies = []
    for e in state.enemies:
        e.update(state)
        if e.pv < 1:
            deads_enemies.append(e)
    for d in deads_enemies:
        state.enemies.remove(d)

    if state.text_box is not None:
        state.text_box.update(state)
        return
    elif state.player_turn:
        player_action(state)
    else:
        game_turn(state)

    state.player.update(state)

    # if state.player.pv < 1:
    #     state.text_box = misc.TextBox("skull", "You are dead...")

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
    state.visited |= state.visible

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
        66: (64, 16),  # UP
        99: (64, 24),  # DOWN
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

    enemies = sorted(state.enemies, key=lambda e: e.zindex)
    for enemy in enemies:
        if enemy.square not in state.visible:
            continue
        x, y = state.to_cam_space(enemy.pos)
        sp = enemy.sprite
        pyxel.blt(
            x * CELL_SIZE - sp.center[0],
            y * CELL_SIZE - sp.center[1],
            0,
            *sp.uv,
            enemy.sprite.size[0] * enemy.orientation,
            enemy.sprite.size[1],
            1,
        )

    for p in state.particles:
        p.draw(state)

    # Active Tool
    if state.active_tool is not None:
        state.active_tool.draw(state)

    if state.text_box is not None:
        state.text_box.draw(state)

    # HUD
    pyxel.rect(3, 3, 2 * state.player.pv, 7, 2)
    pyxel.rect(3, 3, 2 * state.player.pv, 5, 8)
    pyxel.rect(4, 4, 2 * state.player.pv - 2, 1, 14)
    pyxel.rectb(2, 2, 42, 8, 1)

    for i in range(state.player.keys):
        pyxel.blt(3 + i * 7, 12, 0, *ITEMS["key"])

    for i, flag in enumerate(["wand", "teleport", "thunder", "armor"]):
        if flag in state.player.flags:
            pyxel.blt(117 - i * 8, 2, 0, *ITEMS[flag])

    # MENU
    menu_ = menu(state)
    if state.menu_index is not None:
        h = 4 + len(menu_) * 8
        pyxel.rect(40, 40, 48, h, 0)
        pyxel.rectb(40, 40, 48, h, 5)

        for i, (code, item, _) in enumerate(menu_):
            col = 5 if state.player.cooldown(code) else 7
            pyxel.text(50, 43 + i * 8, item, col)

        pyxel.blt(41, 42 + state.menu_index * 8, 0, *ITEMS["dot"])
        pyxel.rect(17, 121, 128, 7, 0)
        pyxel.text(19, 122, "X: Exit / C: Confirm", 7)
    elif state.text_box is not None:
        pyxel.text(3, 122, "X/C: Close", 7)
    else:
        pyxel.text(3, 122, "C: Menu", 7)


class App:
    _debug: bool = False

    def __init__(self):
        self._title = True
        self.particles = []
        self.story = misc.RollingText(12, 64, STORY)
        levels = [
            level_1(),
            level_2(),
            level_3(),
        ]
        # level = populate_enemies(level)

        self.state = State(
            levels=levels,
            current_level=-1,
            camera=(0, 0),
            player=Player((0, 0), 9000),
        )
        self.state.visited_by_floor = [
            set() for _ in range(len(self.state.levels))
        ]
        self.state.change_level(3)
        self.state.player.flags.add("teleport")
        self.state.player.flags.add("wand")
        self.state.player.flags.add("thunder")
        self.state.player.flags.add("armor")

        self._draw = partial(draw, self.state)
        self._draw_debug = partial(debug.draw_debug, self.state)

        self._update = partial(update, self.state)
        self._update_debug = partial(debug.update_debug, self.state)

    def run(self):
        pyxel.init(128, 128)
        pyxel.load("my_resource.pyxres")
        pyxel.playm(2, loop=True)
        pyxel.run(self.update, self.draw)

    def update(self):
        if self._title:
            self.story.update()
            if pyxel.btnr(pyxel.KEY_C) or pyxel.btnr(pyxel.KEY_X):
                self._title = False
                pyxel.stop()
                pyxel.playm(0, loop=True)

            m = random.randrange(1, 6)
            m *= 30

            if (pyxel.frame_count % m) == 0:
                cb = lambda x: x
                p1 = random.randrange(10, 20), random.randrange(10, 26)
                p2 = random.randrange(112, 124), random.randrange(10, 26)

                if random.randint(0, 2):
                    p1, p2 = p2, p1

                self.particles.append(Thunder(None, p1, p2, cb, False))
                self.particles.append(Thunder(None, p1, p2, cb, False))

            clear = []
            for p in self.particles:
                p.update(self)
                if not p.living():
                    clear.append(p)
            for p in clear:
                self.particles.remove(p)

            return

        if pyxel.btnr(pyxel.KEY_D):
            self._debug = not self._debug

        if self._debug:
            self._update_debug()
        else:
            self._update()

    def draw(self):
        if self._title:
            self.draw_title()
            return

        if self._debug:
            self._draw_debug()
        else:
            self._draw()

    def draw_title(self):
        pyxel.cls(0)

        for p in self.particles:
            p.draw(self.state)

        pyxel.blt(40, 10, 2, 0, 94, 48, 122)
        pyxel.blt(88, 20, 0, 88, 0, 8, 8, 1)

        self.story.draw()
        pyxel.rect(0, 100, 128, 50, 0)
        if (pyxel.frame_count // 15) % 2 == 0:
            pyxel.text(30, 115, "Press C to start", 7)



def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
