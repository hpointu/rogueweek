from dataclasses import dataclass
from math import sqrt
from typing import List, Tuple

GridCoord = Tuple[int, int]
VecF = Tuple[float, float]

EW, NS = 0, 1


@dataclass
class Board:
    cells: List[int]
    side: int

    def set(self, x, y, val):
        self.cells[y * self.side + x] = val

    def get(self, x, y):
        return self.cells[y * self.side + x]

    def __getitem__(self, k):
        return self.cells[k]

    def __setitem__(self, k, val):
        self.cells[k] = val

    def __len__(self):
        return len(self.cells)

    def outside(self, x, y):
        return x < 0 or y < 0 or x >= self.side or y >= self.side


def index_to_pos(index: int, width: int) -> GridCoord:
    """(col,lin) of an index in a grid of `width`"""
    return index % width, int(index / width)


def pos_to_index(x: int, y: int, width: int) -> int:
    return width * y + x


def dist(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    return sqrt(dx ** 2 + dy ** 2)


def normalize(v):
    l = dist((0, 0), v)
    return v[0] / l, v[1] / l


def cast_ray(
    start: VecF,
    direction: VecF,
    hit_predicate,
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
    dx, dy = abs(1 / dir_x), abs(1 / dir_y)

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
