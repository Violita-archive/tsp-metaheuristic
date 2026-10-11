"""
app/algorithms/tabu.py
Tabu Search untuk TSP.

Alur:
    1. Mulai dari initial_route (hasil constructive)
    2. Tiap iterasi: generate semua swap (i,j) sebagai kandidat neighbor
    3. Pilih neighbor terbaik yang TIDAK ada di tabu list
       -- kecuali memenuhi aspiration criterion (lebih baik dari best ever)
    4. Tambahkan move (i,j) ke tabu list; hapus yang paling lama jika penuh
    5. Update best jika current lebih baik
    6. Ulangi sampai max_iter habis

Input:
    dist_matrix    : np.ndarray (NxN)
    initial_route  : list[int] dari constructive
    tabu_tenure    : berapa iterasi sebuah move dilarang (default: N//2)
    max_iter       : batas iterasi (default 500)

Output:
    best_route     : list[int]
    best_distance  : float
    history        : list[dict] -- untuk plot konvergensi
"""

import numpy as np
from collections import deque


def tabu_search(
    dist_matrix: np.ndarray,
    initial_route: list[int],
    tabu_tenure: int | None = None,
    max_iter: int = 500,
) -> tuple[list[int], float, list[dict]]:
    """
    Tabu Search untuk TSP.

    Returns:
        best_route     : rute terbaik (list of indices)
        best_distance  : jarak terbaik
        history        : list of {"iter": int, "current_dist": float,
                                  "best_dist": float, "tabu_size": int}
    """
    n = len(initial_route)
    if tabu_tenure is None:
        tabu_tenure = max(5, n // 2)

    current_route = initial_route[:]
    current_dist = _total_distance(current_route, dist_matrix)

    best_route = current_route[:]
    best_dist = current_dist

    # tabu list: simpan move (i, j) sebagai frozenset supaya (i,j) == (j,i)
    tabu_list: deque[frozenset] = deque()
    tabu_set: set[frozenset] = set()

    history = []

    for iteration in range(max_iter):

        best_neighbor_route = None
        best_neighbor_dist = float("inf")
        best_move = None

        # -- Generate semua swap neighbor ----------------------------------------
        for i in range(n - 1):
            for j in range(i + 1, n):
                move = frozenset({i, j})

                neighbor = current_route[:]
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                neighbor_dist = _total_distance(neighbor, dist_matrix)

                is_tabu = move in tabu_set

                # Aspiration criterion: boleh meski tabu kalau lebih baik dari best
                if is_tabu and neighbor_dist >= best_dist:
                    continue

                if neighbor_dist < best_neighbor_dist:
                    best_neighbor_dist = neighbor_dist
                    best_neighbor_route = neighbor
                    best_move = move

        # Kalau semua move tabu dan aspiration ga terpenuhi (edge case)
        if best_neighbor_route is None:
            break

        # -- Pindah ke neighbor terbaik ------------------------------------------
        current_route = best_neighbor_route
        current_dist = best_neighbor_dist

        # -- Update tabu list ----------------------------------------------------
        tabu_list.append(best_move)
        tabu_set.add(best_move)
        if len(tabu_list) > tabu_tenure:
            expired = tabu_list.popleft()
            tabu_set.discard(expired)

        # -- Update best ---------------------------------------------------------
        if current_dist < best_dist:
            best_route = current_route[:]
            best_dist = current_dist

        # -- Catat history -------------------------------------------------------
        history.append({
            "iter": iteration + 1,
            "current_dist": round(current_dist, 4),
            "best_dist": round(best_dist, 4),
            "tabu_size": len(tabu_list),
        })

    return best_route, round(best_dist, 4), history


# -- Helper -----------------------------------------------------------------------

def _total_distance(route: list[int], dist_matrix: np.ndarray) -> float:
    n = len(route)
    return sum(
        dist_matrix[route[i]][route[(i + 1) % n]]
        for i in range(n)
    )