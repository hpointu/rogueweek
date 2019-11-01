import random
from dataclasses import dataclass
from typing import List, Tuple

M_SIZE = 4
MAX_ROOM_SIZE = 8

MPath = Tuple[int, int]
Matrix = List[MPath]
Size = Tuple[int, int]
Position = Tuple[int, int]
Room = Size, Position
Board = List[int]


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


def count_neighbours(matrix: Matrix, index: int) -> int:
    return sum(1 for a, b in matrix if a == index or b == index)


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


def random_room(matrix: Matrix, room_index: int) -> Room:
    n_neigh = count_neighbours(matrix, room_index)
    threshold = 4
    min_size = 3 if n_neigh > 1 else threshold

    max_size = MAX_ROOM_SIZE - 0
    w, h = (
        random.randint(min_size, max_size),
        random.randint(min_size, max_size),
    )

    if w < threshold or h < threshold:
        return (1, 1), (0, 0)

    return (w, h), (0, 0)


def create_matrix() -> Matrix:
    start = random.randrange(M_SIZE * M_SIZE)
    return add_loops(dig_matrix(start))


def carve_room(board: Board, room: Room, pos: Position) -> Board:
    (w, h), offset = room
    x, y = pos
    for i in range(h):
        for j in range(w):
            _x = j + x
            _y = i + y
            board[_y * M_SIZE * MAX_ROOM_SIZE + _x] = 0
    return board


def carve_path(board: Board, level: Level, path: MPath) -> Board:
    a, b = path
    r1, r2 = level.rooms[a][0], level.rooms[b][0]
    p1, p2 = list(room_anchor(a)), list(room_anchor(b))
    other = 0 if p1[0] == p2[0] else 1
    max_off = min(r1[other], r2[other])
    off = random.randrange(max_off)

    p1[other] += off
    p2[other] += off

    coord = 1 if p1[0] == p2[0] else 0
    step = 1 if p1[coord] < p2[coord] else -1
    p = p1

    if step > 0:
        p[coord] += r1[coord]
        p2[coord] -= 1
    else:
        p[coord] -= 1
        p2[coord] += r2[coord]

    cpt = 0
    last_i = None
    while p[coord] != p2[coord]:
        x, y = p
        i = y * M_SIZE * MAX_ROOM_SIZE + x

        if board[i] == 0:
            return board

        val = 2 if last_i is None else 0

        if r1 == (1, 1):
            val = 0

        if board[i] == 1:
            first = False

        board[i] = val
        p[coord] += step
        cpt += 1
        last_i = i

    x, y = p2
    i = y * M_SIZE * MAX_ROOM_SIZE + x
    val = 0 if r2 == (1, 1) else 3
    if last_i is not None and cpt < 2:
        board[last_i] = 0

    board[i] = val

    return board


def room_anchor(index: int) -> Position:
    side = M_SIZE * MAX_ROOM_SIZE
    x = (index * MAX_ROOM_SIZE) % side
    y = int((index * MAX_ROOM_SIZE) / side) * MAX_ROOM_SIZE
    return x, y


def create_map(level: Level):
    # fully walls (+ border)
    side = M_SIZE * MAX_ROOM_SIZE
    board = (side * side) * [1]
    for i, room in enumerate(level.rooms):
        board = carve_room(board, room, room_anchor(i))

    for path in level.matrix:
        board = carve_path(board, level, path)

    return board


def generate_level(matrix: Matrix) -> Level:
    return Level(
        matrix=matrix,
        rooms=[random_room(matrix, i) for i in range(M_SIZE * M_SIZE)],
    )
