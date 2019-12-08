from functools import partial
import random
from typing import List, Tuple
from rogue.items import Chest, ADD_KEY, MAGIC_WAND, TELEPORT_SPELL
from rogue.graph import (
    neighbours_map,
    find_paths,
    extract_path,
    board_neighbours,
)

from rogue.core import (
    is_door,
    is_empty,
    is_locked,
    is_wall,
)
from rogue.core import (
    index_to_pos,
    Board,
    AIActor,
    pos_to_index,
    Level,
    Matrix,
    MPath,
    Room,
    Position,
)

from rogue.enemies import Slug, Skeleton, Ghost, Plant, Bat, Necromancer

M_SIZE = 4
MAX_ROOM_SIZE = 8
SIDE = M_SIZE * MAX_ROOM_SIZE


def matrix_neighbours(index: int) -> List[int]:
    col, row = index_to_pos(index, M_SIZE)

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
            board.set(_x, _y, 0)
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

        if board.get(x, y) == 0:
            return board

        val = 2 if last_i is None else 0

        if r1 == (1, 1):
            val = 0

        board.set(x, y, val)
        p[coord] += step
        cpt += 1
        last_i = x, y

    x, y = p2
    val = 0 if r2 == (1, 1) else 2
    if last_i is not None and cpt < 2:
        board.set(*last_i, 0)

    board.set(x, y, val)

    return board


def room_anchor(index: int) -> Position:
    x = (index * MAX_ROOM_SIZE) % SIDE
    y = int((index * MAX_ROOM_SIZE) / SIDE) * MAX_ROOM_SIZE
    return x, y


def encode_wall(board: Board, index: int) -> int:
    val = 0b10000

    x, y = index_to_pos(index, board.side)
    neighs = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]

    for i, (x_, y_) in enumerate(neighs):
        if board.outside(x_, y_) or is_wall(board.get(x_, y_)):
            val = val | (1 << i)

    return int("{0:b}".format(val))


def encode_floor(board: Board, index: int) -> int:
    x, y = index_to_pos(index, board.side)
    top = x, y - 1

    top_val = board.get(*top)

    if board.outside(*top):
        return 32

    elif is_wall(top_val):
        bin_str = str(top_val)
        if bin_str[4] == "0" and bin_str[2] == "1":
            return 31
        elif bin_str[4] == "1" and bin_str[2] == "1":
            return 32
        elif bin_str[4] == "1" and bin_str[2] == "0":
            return 33
        elif bin_str[4] == "0" and bin_str[2] == "0":
            return 34

    elif top_val == 20:  # front door
        return 35

    return 30


def encode_door(board: Board, index: int) -> int:
    x, y = index_to_pos(index, board.side)
    top = x, y - 1

    top_val = board.get(*top)

    if board.outside(*top):
        return 22

    elif is_wall(top_val):
        bin_str = str(top_val)
        if bin_str[4] == "0" and bin_str[2] == "1":
            return 21
        elif bin_str[4] == "1" and bin_str[2] == "1":
            return 22
        elif bin_str[2] == "0":
            return 23

    return 20


def clean_board(board: Board) -> Board:

    for i in range(len(board)):
        val = board[i]
        if val == 1:
            board[i] = encode_wall(board, i)
        elif val == 2:
            # must happen after walls (top down)
            x, y = board.to_pos(i)
            n_neigh = sum(
                1 for k in board.neighbours(x, y) if is_empty(board.get(*k))
            )
            if n_neigh > 2:
                board[i] = 0  # remove door
            else:
                board[i] = encode_door(board, i)
        elif val == 0:
            # Must happen after walls and doors
            board[i] = encode_floor(board, i)

    return board


def create_board(level: Level):
    # fully walls (+ border)
    board = Board(cells=(SIDE * SIDE) * [1], side=SIDE,)
    for i, room in enumerate(level.rooms):
        board = carve_room(board, room, room_anchor(i))

    for path in level.matrix:
        board = carve_path(board, level, path)

    return clean_board(board)


def pick_final_rooms(level: Level) -> List[int]:
    rooms = []
    for i, room in enumerate(level.rooms):
        n = count_neighbours(level.matrix, i)

        if n > 1:
            continue

        x, y = index_to_pos(i, M_SIZE)
        w, h = room[0]

        if x < M_SIZE - 1 and w >= MAX_ROOM_SIZE:
            continue

        if y < M_SIZE - 1 and h >= MAX_ROOM_SIZE:
            continue

        left = pos_to_index(x - 1, y, M_SIZE)
        top = pos_to_index(x, y - 1, M_SIZE)
        left_size = level.rooms[left][0] if x > 0 else None
        top_size = level.rooms[top][0] if y > 0 else None

        if left_size and left_size[0] >= MAX_ROOM_SIZE:
            continue

        if top_size and top_size[1] >= MAX_ROOM_SIZE:
            continue

        if w > 5 and h > 5:
            rooms.append(i)

    return rooms


def pick_starting_room(level: Level) -> int:
    start = level.final_rooms[0]
    neighs = neighbours_map(level.matrix)
    paths = find_paths(range(len(level.rooms)), start, neighs.get)

    def distance(idx):
        return len(extract_path(paths, idx))

    far, d = start, 0
    for i in range(len(level.rooms)):
        if i in level.final_rooms or level.rooms[i][0] == (1, 1):
            continue
        di = distance(i)
        if di > d:
            far = i
            d = di

    return far


def lock_door(val):
    return val + 5


def dig_door(val):
    return val + 20


def amend_door(board: Board, room_index: int, door_fn) -> Board:
    nodes = list(range(len(board)))
    start = board.to_index(*room_anchor(room_index))
    target = board.entrance
    neighs = partial(board_neighbours, board, lambda x: not is_wall(x))
    path = extract_path(find_paths(nodes, start, neighs), target)

    for i in path:
        if is_door(board[i]):
            board[i] = door_fn(board[i])

            botx, boty = board.to_pos(i)
            boty += 1
            # might rencode floor below
            if is_empty(board.get(botx, boty)):
                i = board.to_index(botx, boty)
                floor = encode_floor(board, i)
                board.set(botx, boty, floor)

            return board

    return board


def generate_level() -> Level:
    final_rooms: List[int] = []

    while len(final_rooms) < 3:
        matrix = create_matrix()
        level = Level(
            matrix=matrix,
            rooms=[random_room(matrix, i) for i in range(M_SIZE * M_SIZE)],
        )
        final_rooms = pick_final_rooms(level)[:3]

    level.final_rooms = final_rooms
    level.start_room = pick_starting_room(level)
    board = create_board(level)

    (w, h), _ = level.rooms[level.start_room]
    x, y = room_anchor(level.start_room)
    board.entrance = board.to_index(x + int(w/2), y + int(h/2))

    level.board = board
    return level


def populate_enemies(level: Level, stock, empty):
    board = level.board
    enemies = []
    for i in range(len(board)):
        if not is_empty(board[i]):
            continue

        if any(index_in_room(level, r, i) for r in level.final_rooms):
            continue

        # if any(board.to_index(i.square) for i in level.items):
        #     pass

        r = random.randint(0, 100)
        if r >= empty:
            enemy_cls = random.choice(stock)
            e = enemy_cls(index_to_pos(i, board.side))
            e.sprite.play()
            enemies.append(e)

    return enemies


def square_from_room(level: Level, room_index):
    x = random.randrange(1, level.rooms[room_index][0][0] - 2)
    y = random.randrange(1, level.rooms[room_index][0][1] - 2)
    ox, oy = room_anchor(room_index)
    return ox + x, oy + y


def set_exit(level):
    final_rooms = level.final_rooms
    (w, h), _ = level.rooms[final_rooms[0]]
    x, y = room_anchor(final_rooms[0])
    level.board.set(x + int(w/2), y + int(h/2), 99)

    return level


def index_in_room(level, room, index):
    rx, ry = room_anchor(room)
    (w, h), _ = level.rooms[room]
    x, y = level.board.to_pos(index)
    return x >= rx and x < rx + w and y >= ry and y < ry + h


def level_1() -> Level:
    level = generate_level()
    board = amend_door(level.board, level.final_rooms[0], dig_door)
    for r in level.final_rooms[1:]:
        board = amend_door(board, r, lock_door)

    rooms = random.choices(
        [
            i
            for i in range(len(level.rooms))
            if i not in level.final_rooms
            and level.rooms[i][0][0] > 3
            and level.rooms[i][0][1] > 3
        ],
        k=2,
    )
    level.items.append(
        Chest(ADD_KEY, square=square_from_room(level, rooms[0]))
    )
    level.items.append(
        Chest(ADD_KEY, square=square_from_room(level, rooms[1]))
    )

    final_rooms = level.final_rooms
    level.items.append(
        Chest(MAGIC_WAND, square=square_from_room(level, final_rooms[1]))
    )
    level.items.append(
        Chest(TELEPORT_SPELL, square=square_from_room(level, final_rooms[2]))
    )

    stock = [Bat] * 2 + [Slug]
    level.enemies = populate_enemies(level, stock, empty=95)

    level = set_exit(level)
    return level


def level_2() -> Level:
    level = generate_level()

    level.board[level.board.entrance] = 66
    set_exit(level)

    stock = [Skeleton] * 3 + [Bat] * 3 + [Plant] + [Slug] * 4
    level.enemies = populate_enemies(level, stock, empty=95)

    return level


def level_3() -> Level:
    level = generate_level()

    level.board[level.board.entrance] = 66
    boss_room = level.final_rooms[0]
    (w, h), _ = level.rooms[boss_room]
    x, y = room_anchor(boss_room)
    boss = Necromancer((int(x + w/2), int(y + h/2)), boss_room)

    stock = [Skeleton] * 3 + [Bat] * 3 + [Plant] + [Slug] * 4
    level.enemies = populate_enemies(level, stock, empty=96)
    level.enemies.append(boss)

    return level
