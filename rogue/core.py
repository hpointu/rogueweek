from __future__ import annotations
from dataclasses import dataclass, field
from math import sqrt
from typing import List, Tuple, Any, Set, Optional

from rogue import tween

from rogue.constants import FPS
from rogue.sprites import WALLS


GridCoord = Tuple[int, int]
VecF = Tuple[float, float]

EW, NS = 0, 1


ANIMATED = {
    9000: (2, [(0, 32), (8, 32)], (0, 0), 4),
    9001: (2, [(0, 40), (8, 40)], (0, -2), 10),
    9002: (2, [(0, 48), (8, 48)], (0, 0), 11),
    9003: (2, [(0, 56), (8, 56)], (0, 0), 12),
}

ITEMS = {
    'chest': (48, 16, 8, 8, 0),
    'key': (80, 8, 8, 8, 1),
}

MPath = Tuple[int, int]
Matrix = List[MPath]
Size = Tuple[int, int]
Position = Tuple[int, int]
Room = Tuple[Size, Position]

ActionReport = Optional[int]


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
    orientation = 1
    pv = 20

    def __init__(self, pos, sprite_id):
        self.pos = pos
        self._action = None
        self._path = None
        self._callback = None
        self.sprite = AnimSprite(*ANIMATED[sprite_id])
        self.flags = set()

    @property
    def square(self) -> GridCoord:
        x, y = map(int, self.pos)
        return x, y

    def is_busy(self):
        return self._callback is not None

    def bump_to(self, target, callback):
        path = []
        x, y = target
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
        target.pv -= 2
        return 2

    def move(self, x, y, callback, frames=int(FPS * 0.3)):
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


class Player(Actor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = 0

    def move(self, *a, **kw):
        super().move(*a, **kw)
        self.sprite.play()

    def wait(self, *a, **kw):
        super().wait(*a, **kw)
        self.sprite.play()

    def attack(self, *a, **kw):
        r = super().attack(*a, **kw)
        self.sprite.play()
        return r

    def end_turn(self):
        super().end_turn()
        self.sprite.stop()


class AIActor(Actor):
    def take_action(self, state: State, end_turn) -> ActionReport:
        end_turn(self)
        return None


@dataclass
class AnimSprite:
    count: int
    uvs: List[Tuple[int, int]]
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


@dataclass
class State:
    max_range = 5
    player: Actor
    level: Level
    board: Board
    camera: Tuple[float, float]
    enemies: List[AIActor] = field(default_factory=list)
    in_range: Set[Any] = field(default_factory=set)
    visible: Set[GridCoord] = field(default_factory=set)
    particles: List[Particle] = field(default_factory=list)
    player_turn: bool = True

    def to_cam_space(self, pos: Tuple[float, float]):
        px, py = pos
        cx, cy = self.camera
        return px - cx, py - cy

    def to_pixel(self, pos: Tuple[float, float], tile_size):
        return tuple(c * tile_size for c in self.to_cam_space(pos))


class Particle:
    def draw(self, state: State):
        raise NotImplementedError

    def update(self, state: State):
        raise NotImplementedError

    def living(self) -> bool:
        raise NotImplementedError


def is_wall(val: int) -> bool:
    return val in WALLS or val == 1


def is_door(val: int) -> bool:
    return val == 2 or 20 <= val < 30


def is_locked(val: int) -> bool:
    return 25 <= val < 30


def is_empty(val: int) -> bool:
    return val == 0 or 30 <= val < 40


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
