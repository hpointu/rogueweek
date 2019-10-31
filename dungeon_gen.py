import random
from dataclasses import dataclass
from typing import List, Tuple

M_SIZE = 4
MAX_ROOM_SIZE = 8

MPath = Tuple[int, int]
Matrix = List[MPath]
Size = Tuple[int, int]


@dataclass
class Level:
    matrix: Matrix
    rooms: List[Size]


def matrix_neighbours(index: int) -> List[int]:
    row, col = int(index / M_SIZE), int(index % M_SIZE)

    return [
        r * M_SIZE + c
        for r, c in [
            (row, col + 1),
            (row + 1, col),
            (row, col - 1),
            (row - 1, col),
        ]
        if r < M_SIZE and c < M_SIZE and r >= 0 and c >= 0
    ]


def dig_matrix(start) -> Matrix:
    matrix: Matrix = []
    visited = {start}
    to_explore = set(matrix_neighbours(start))
    while to_explore:
        start = random.choice(list(to_explore))
        old = next(n for n in visited if n in matrix_neighbours(start))
        matrix.append((old, start))
        visited.add(start)
        to_explore.remove(start)
        to_explore |= set(
            n for n in matrix_neighbours(start) if n not in visited
        )

    return matrix


def add_loops(matrix: Matrix) -> Matrix:
    extras = random.randrange(int(M_SIZE / 2), M_SIZE)
    goal = extras + len(matrix)
    while len(matrix) < goal:
        a = random.randrange(M_SIZE * M_SIZE)
        try:
            b = next(
                b
                for b in matrix_neighbours(a)
                if (a, b) not in matrix and (b, a) not in matrix
            )
        except StopIteration:
            continue
        else:
            matrix.append((a, b))

    return matrix


def random_room() -> Size:
    max_size = MAX_ROOM_SIZE - 1
    return (random.randint(1, max_size), random.randint(1, max_size))


def create_matrix() -> Matrix:
    start = random.randrange(M_SIZE * M_SIZE)
    return add_loops(dig_matrix(start))


def carve_room(board, room, x, y):
    print(f"carving {x} {y}")
    w, h = room
    for i in range(h):
        for j in range(w):
            _x = j + x
            _y = i + y
            board[(y + i) * M_SIZE * MAX_ROOM_SIZE + x + j] = 0
    return board


def create_map(level: Level):
    # fully walls (+ border)
    side = M_SIZE * MAX_ROOM_SIZE
    board = (side * side) * [1]
    for i, room in enumerate(level.rooms):
        board = carve_room(
            board,
            room,
            (i * MAX_ROOM_SIZE) % side,
            int((i * MAX_ROOM_SIZE) / side) * MAX_ROOM_SIZE,
        )

    return board


def generate_level(matrix: Matrix) -> Level:
    return Level(
        matrix=matrix, rooms=[random_room() for _ in range(M_SIZE * M_SIZE)]
    )
