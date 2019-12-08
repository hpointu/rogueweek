from __future__ import annotations
from dataclasses import dataclass, field
from math import sqrt
from typing import List, Tuple, Any, Set, Optional, Callable, Union

from rogue import tween

from rogue.constants import FPS, DType, MAX_PV
from rogue.sprites import WALLS


GridCoord = Tuple[int, int]
VecF = Tuple[float, float]

EW, NS = 0, 1
LEFT, RIGHT = 1, 2


ANIMATED = {
    9000: (2, [(0, 32), (8, 32)], (8, 8), (0, 0), 4),
    9001: (2, [(0, 40), (8, 40)], (8, 8), (0, -2), 9),
    9002: (2, [(0, 48), (8, 48)], (8, 8), (0, 0), 10),
    9003: (2, [(0, 56), (8, 56)], (8, 8), (0, 0), 11),
    9004: (2, [(0, 64), (8, 64)], (8, 16), (2, 8), 12),
    9005: (2, [(0, 80), (8, 80)], (8, 8), (0, 0), 8),
    9010: (1, [(48, 40)], (8, 8), (0, 0), 10),
    9888: (2, [(0, 88), (8, 88)], (8, 16), (0, 8), 3),
    9999: (2, [(0, 88), (8, 88)], (8, 16), (0, 8), 15),
}

ITEMS = {
    'chest': (48, 16, 8, 8, 0),
    # 'key': (80, 8, 8, 8, 1),
    'key': (104, 24, 8, 8, 1),
    'thunder': (96, 24, 8, 8, 1),
    'skull': (88, 16, 8, 8, 1),
    'dot': (80, 16, 8, 8, 1),
    'select': (112, 0, 8, 8, 0),
    'flare': (112, 8, 8, 8, 0),
    'sleep_bullet': (120, 8, 8, 8, 0),
    'wand': (80, 24, 8, 8, 1),
    'teleport': (88, 8, 8, 8, 1),
    'armor': (88, 24, 8, 8, 1),
    'book': (88, 0, 8, 8, 1),
    'vial': (96, 16, 8, 8, 1),
    'triA': (96, 8, 8, 8, 1),
    'triB': (104, 8, 8, 8, 1),
    'tri': (96, 0, 8, 8, 1),
}

MPath = Tuple[int, int]
Matrix = List[MPath]
Size = Tuple[int, int]
Position = Tuple[int, int]
Room = Tuple[Size, Position]

Action = Union[int, GridCoord]
ActionReport = Optional[Action]


@dataclass
class LevelItem:
    square: Tuple[int, int]
    sprite_id: int = 0

    def interact(self, state: State):
        pass

    @property
    def sprite(self):
        return ITEMS[self.sprite_id]

@dataclass
class Level:
    matrix: Matrix
    rooms: List[Room]
    start_room: int = 0
    final_rooms: List[int] = field(default_factory=list)
    items: List[LevelItem] = field(default_factory=list)
    board: Optional[Board] = None
    enemies: List[AIActor] = field(default_factory=list)


@dataclass
class Board:
    cells: List[int]
    side: int
    entrance: int = 0

    def set(self, x, y, val):
        self.cells[int(y) * self.side + int(x)] = val

    def get(self, x, y):
        return self.cells[int(y) * self.side + int(x)]

    def __getitem__(self, k):
        return self.cells[k]

    def __setitem__(self, k, val):
        self.cells[k] = val

    def __len__(self):
        return len(self.cells)

    def outside(self, x, y):
        return x < 0 or y < 0 or x >= self.side or y >= self.side

    def to_pos(self, i):
        return index_to_pos(i, self.side)

    def to_index(self, x, y):
        return pos_to_index(x, y, self.side)

    def neighbours(self, x, y):
        return [
            (x_, y_)
            for x_, y_ in [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
            if not self.outside(x_, y_)
        ]


class Actor:
    parent = None
    _orient = LEFT
    pv = MAX_PV
    strength = 2

    def __init__(self, pos, sprite_id):
        self.pos = pos
        self._action = None
        self._path = None
        self._callback = None
        self.sprite = AnimSprite(*ANIMATED[sprite_id])
        self.flags = set()

    def hurt(self, damage, dtype=DType.MELEE):
        self.pv -= damage

    @property
    def square(self) -> GridCoord:
        x, y = map(int, self.pos)
        return x, y

    def is_busy(self):
        return self._callback is not None

    def bump_to(self, target, callback):
        path = []
        x, y = target
        self.update_orientation(x, y)
        start = self.pos
        end = (start[0] + x) / 2, (start[1] + y) / 2
        path.extend(tween.tween(start, end, int(0.1 * FPS)))
        path.extend(tween.tween(end, start, int(0.1 * FPS)))

        self._action = self.do_move
        self._callback = callback
        self._path = path

    def update(self, state):
        self.sprite.update()
        if self._action:
            self._action()

    def attack(self, target, callback):
        self.bump_to(target.pos, callback)
        target.hurt(2)
        return 2

    def shoot(self, target, callback):
        pass

    def update_orientation(self, x, y):
        if x < self.pos[0]:
            self._orient= LEFT
        if x > self.pos[0]:
            self._orient= RIGHT

    def move(self, x, y, callback, frames=int(FPS * 0.3)):
        self.update_orientation(x, y)
        self._action = self.do_move
        self._callback = callback
        self._path = list(tween.tween(self.pos, (x, y), frames))

    def wait(self, nframes, callback):
        self._action = self.do_wait
        self._callback = callback
        self._path = nframes

    def end_turn(self):
        if self._callback:
            self._callback(self)
        self._callback = None
        self._action = None

    def do_move(self):
        self.pos = self._path.pop(0)
        if not self._path:
            self.end_turn()

    def do_wait(self):
        self._path -= 1
        if self._path < 1:
            self.end_turn()

    @property
    def orientation(self):
        return 1 if self._orient == LEFT else -1


class AIActor(Actor):
    zindex = 0
    def take_action(self, state: State, end_turn) -> ActionReport:
        end_turn(self)
        return None


@dataclass
class AnimSprite:
    count: int
    uvs: List[Tuple[int, int]]
    size: Tuple[int, int]
    center: Tuple[int, int]
    rate: int

    _start = 0
    _playing = False

    @property
    def uv(self):
        i = (self._start // self.rate) % self.count
        return self.uvs[i]

    def play(self):
        self._playing = True

    def stop(self):
        self._start = 0
        self._playing = False

    def update(self):
        if self._playing:
            self._start += 1


class Tool:
    def update(self, state):
        raise NotImplementedError

    def draw(self, state):
        raise NotImplementedError


@dataclass
class State:
    max_range = 5
    player: Actor
    levels: List[Level]
    current_level: int
    camera: Tuple[float, float]
    in_range: Set[Any] = field(default_factory=set)
    visible: Set[GridCoord] = field(default_factory=set)
    particles: List[Particle] = field(default_factory=list)
    player_turn: bool = True
    menu_index: Optional[int] = None
    active_tool: Optional[Tool] = None
    text_box: Optional[Any] = None
    visited_by_floor: Set[GridCoord] = field(default_factory=list)
    occupied: Set[GridCoord] = field(default_factory=set)

    def get_entity(self, x, y):
        pos = x, y
        for e in self.enemies:
            if e.square == pos:
                return e
        for i in self.level.items:
            if i.square == pos:
                return i
        if  self.player.square == pos:
            return self.player

        return None

    def to_cam_space(self, pos: Tuple[float, float]):
        px, py = pos
        cx, cy = self.camera
        return px - cx, py - cy

    def to_pixel(self, pos: Tuple[float, float], tile_size):
        return tuple(int(c * tile_size) for c in self.to_cam_space(pos))

    @property
    def level(self):
        return self.levels[self.current_level]

    @property
    def board(self):
        return self.level.board

    @property
    def enemies(self):
        return self.level.enemies

    @enemies.setter
    def enemies(self, val):
        self.level.enemies = val

    @property
    def visited(self):
        return self.visited_by_floor[self.current_level]

    @visited.setter
    def visited(self, val):
        self.visited_by_floor[self.current_level] = val

    def change_level(self, offset):
        self.current_level += offset
        if offset > 0:
            self.player.pos = self.board.to_pos(self.board.entrance)
        elif offset < 0:
            for i in range(len(self.board)):
                if self.board[i] == 99:
                    break
            self.player.pos = self.board.to_pos(i)

MenuItem = Tuple[str, Callable[[State], None]]


class Particle:
    def draw(self, state: State):
        pass

    def update(self, state: State):
        pass

    def living(self) -> bool:
        raise NotImplementedError


def is_wall(val: int) -> bool:
    return val in WALLS or val == 1


def is_door(val: int) -> bool:
    return val == 2 or 20 <= val < 30


def is_locked(val: int) -> bool:
    return 25 <= val < 30


def is_empty(val: int) -> bool:
    return val == 0 or 30 <= val < 40 or val == 99 or val == 66


def is_active_tile(val) -> bool:
    return val in {66, 99}


def is_hole(val: int) -> bool:
    return 40 <= val < 45


def index_to_pos(index: int, width: int) -> GridCoord:
    """(col,lin) of an index in a grid of `width`"""
    return index % width, int(index / width)


def pos_to_index(x: int, y: int, width: int) -> int:
    return width * int(y) + int(x)


def dist(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    return sqrt(dx ** 2 + dy ** 2)


def normalize(v):
    length = dist((0, 0), v)
    return v[0] / length, v[1] / length


def line(a, b):
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    error = 0
    line_ = []


    if abs(dx) > abs(dy):
        if ax > bx:
            return line(b, a)
        if dx == 0:
            return [(ax, y) for y in range(ay, by)]
        derr = abs(dy / dx)
        y = ay
        for x in range(ax, bx):
            line_.append((x, y))
            error += derr
            if error >= 0.5:
                y += 1 if dy > 0 else -1
                error -= 1
    else:
        if ay > by:
            return line(b, a)
        if dy == 0:
            return [(x, dy) for x in range(ax, bx)]
        x = ax
        derr = abs(dx / dy)
        for y in range(ay, by):
            line_.append((x, y))
            error += derr
            if error >= 0.5:
                x += 1 if dx > 0 else -1
                error -= 1

    return line_


def cast_ray(
    start: VecF, direction: VecF, hit_predicate,
):
    """
    `start` is the position within the world, where each square is of size 1x1
    `direction` is the direction vector or the ray to cast from `start`
    `hit_predicate` is a function that's called with the square value,
                    should return True if the square is considered a hit.
    """
    direction = normalize(direction)
    dir_x, dir_y = direction
    pos_x, pos_y = start
    map_x, map_y = map(int, start)
    dx, dy = abs(1 / dir_x) if dir_x else 0, abs(1 / dir_y) if dir_y else 0

    if dir_x < 0:
        side_dist_x = (pos_x - map_x) * dx
        step_x = -1
    else:
        side_dist_x = (map_x + 1 - pos_x) * dx
        step_x = 1

    if dir_y < 0:
        side_dist_y = (pos_y - map_y) * dy
        step_y = -1
    else:
        side_dist_y = (map_y + 1 - pos_y) * dy
        step_y = 1

    # keep all traversed cells
    traversed = [(map_x, map_y)]
    hit = None

    while hit is None:
        if side_dist_x < side_dist_y:
            side_dist_x += dx
            map_x += step_x
            side = EW
        else:
            side_dist_y += dy
            map_y += step_y
            side = NS

        if hit_predicate(map_x, map_y):
            hit = map_x, map_y
        else:
            traversed.append((map_x, map_y))

    return traversed, hit, side
