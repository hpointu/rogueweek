from math import sqrt
from typing import List, Tuple

GridCoord = Tuple[int, int]


def index_to_pos(index: int, width: int) -> GridCoord:
    """(col,lin) of an index in a grid of `width`"""
    return index % width, int(index / width)


def dist(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    return sqrt(dx ** 2 + dy ** 2)
