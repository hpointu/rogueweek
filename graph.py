from collections import defaultdict


def neighbours_map(matrix):
    neighbours = defaultdict(set)

    for a, b in matrix:
        neighbours[a].add(b)
        neighbours[b].add(a)

    return neighbours


def find_paths(nodes, start, neighbours_fn):
    q = set(nodes)
    prev = dict()
    dist = defaultdict(lambda: float("inf"))
    dist[start] = 0

    def min_dist():
        n, d = None, float("inf")
        for k in q:
            v = dist[k]
            if v < d:
                n, d = k, v
        return n

    while q:
        u = min_dist()
        if dist[u] == float("inf"):
            break  # no more accessible nodes
        q.discard(u)

        for v in neighbours_fn(u):
            tmp = dist[u] + 1
            if tmp < dist[v]:
                dist[v] = tmp
                prev[v] = u

    return prev


def extract_path(paths, target):
    path = []
    u = target
    while u in paths:
        path.insert(0, u)
        u = paths[u]
    return path
