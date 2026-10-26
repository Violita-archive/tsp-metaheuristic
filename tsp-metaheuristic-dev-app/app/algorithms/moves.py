"""
app/algorithms/moves.py
Move operator (neighborhood) untuk SA dan Tabu Search.

Rute disimpan sebagai list index kota, posisi 0 = depot (tidak dipindah).
Move dinyatakan dengan pasangan posisi (i, j), 1 <= i, j <= n-1.

Operator:
    swap      : tukar kota di posisi i dan j
    2opt      : balik segmen posisi i..j
    insertion : pindahkan kota di posisi i ke posisi j

Delta jarak dihitung O(1) tanpa menghitung ulang seluruh rute.
"""

MOVE_LABELS = {"swap": "Swap", "2opt": "2-Opt", "insertion": "Insertion"}
MOVE_KEYS = {v: k for k, v in MOVE_LABELS.items()}


def all_moves(n, op):
    """Daftar seluruh move (i, j) yang valid untuk rute berukuran n."""
    if n < 3:
        return []
    if op == "insertion":
        return [(i, j) for i in range(1, n) for j in range(1, n) if i != j]
    moves = [(i, j) for i in range(1, n - 1) for j in range(i + 1, n)]
    if op == "2opt" and n > 3:
        # (1, n-1) hanya membalik arah seluruh rute -> delta selalu 0
        moves.remove((1, n - 1))
    return moves


def random_move(rng, n, op):
    """Satu move acak (i, j)."""
    if op == "insertion":
        i, j = rng.sample(range(1, n), 2)
        return i, j
    while True:
        i, j = sorted(rng.sample(range(1, n), 2))
        if not (op == "2opt" and n > 3 and i == 1 and j == n - 1):
            return i, j


def delta(route, d, op, i, j):
    """Perubahan total jarak jika move (i, j) diterapkan."""
    n = len(route)
    if op == "2opt":
        a, b = route[i - 1], route[i]
        c, e = route[j], route[(j + 1) % n]
        return d[a][c] + d[b][e] - d[a][b] - d[c][e]

    if op == "swap":
        if i > j:
            i, j = j, i
        a, b = route[i - 1], route[i]
        c, e = route[j], route[(j + 1) % n]
        if j == i + 1:
            return d[a][c] + d[b][e] - d[a][b] - d[c][e]
        b_next = route[i + 1]
        c_prev = route[j - 1]
        old = d[a][b] + d[b][b_next] + d[c_prev][c] + d[c][e]
        new = d[a][c] + d[c][b_next] + d[c_prev][b] + d[b][e]
        return new - old

    # insertion: kota di posisi i dipindah ke posisi j
    c = route[i]
    p, nx = route[i - 1], route[(i + 1) % n]
    removed = d[p][c] + d[c][nx] - d[p][nx]
    # indeks pada rute tanpa kota c (panjang n-1)
    m = n - 1

    def r_wo(k):
        k %= m
        return route[k] if k < i else route[k + 1]

    u, v = r_wo(j - 1), r_wo(j)
    added = d[u][c] + d[c][v] - d[u][v]
    return added - removed


def apply_move(route, op, i, j):
    """Rute baru hasil move (i, j)."""
    r = route[:]
    if op == "swap":
        r[i], r[j] = r[j], r[i]
    elif op == "2opt":
        r[i:j + 1] = r[i:j + 1][::-1]
    else:
        c = r.pop(i)
        r.insert(j, c)
    return r


def move_attr(route, op, i, j):
    """Atribut tabu: pasangan kota yang terlibat (bukan posisi)."""
    if op == "insertion":
        return frozenset({route[i]})
    return frozenset({route[i], route[j]})


def move_text(route, op, i, j, names=None):
    """Teks move untuk log, mis. 2-Opt(2,5) [Gresik-Blitar]."""
    lbl = MOVE_LABELS.get(op, op)
    if names is None:
        return f"{lbl}({i},{j})"
    if op == "insertion":
        return f"{lbl}({i}->{j}) [{names[route[i]]}]"
    return f"{lbl}({i},{j}) [{names[route[i]]}-{names[route[j]]}]"


def route_length(route, d):
    n = len(route)
    return sum(d[route[k]][route[(k + 1) % n]] for k in range(n))


def rotate_to_start(route, start=0):
    """Putar rute supaya diawali kota `start` (jarak tidak berubah)."""
    if start not in route:
        return route[:]
    k = route.index(start)
    return route[k:] + route[:k]
