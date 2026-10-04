"""
app/algorithms/constructive.py
Heuristik konstruktif untuk solusi awal TSP.

Semua fungsi:
    Input  : dist_matrix (np.ndarray, shape NxN), start (int, default 0)
    Output : route (list[int]) — urutan kota, panjang N, belum include kembali ke start
             total_distance (float)

Gunakan distance_matrix() dari utils/distance.py untuk membuat dist_matrix.
"""

import random
import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# 1. Nearest Neighbor (NN)
# ══════════════════════════════════════════════════════════════════════════════

def nearest_neighbor(dist_matrix: np.ndarray, start: int = 0) -> tuple[list[int], float]:
    """
    Nearest Neighbor Heuristic.

    Mulai dari `start`, selalu pergi ke kota terdekat yang belum dikunjungi.

    Args:
        dist_matrix : matriks jarak NxN
        start       : indeks kota awal (default 0)

    Returns:
        route          : list of indices, panjang N
        total_distance : total jarak rute (termasuk balik ke start)
    """
    n = len(dist_matrix)
    unvisited = set(range(n))
    route = [start]
    unvisited.remove(start)

    current = start
    while unvisited:
        # cari kota terdekat dari current yang belum dikunjungi
        nearest = min(unvisited, key=lambda city: dist_matrix[current][city])
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    total_distance = _calc_total_distance(route, dist_matrix)
    return route, total_distance


# ══════════════════════════════════════════════════════════════════════════════
# 2. Farthest Insertion
# ══════════════════════════════════════════════════════════════════════════════

def farthest_insertion(dist_matrix: np.ndarray) -> tuple[list[int], float]:
    """
    Farthest Insertion Heuristic.

    Mulai dari pasangan kota paling jauh, lalu insert kota yang paling
    jauh dari subtour saat ini ke posisi yang paling murah.

    Args:
        dist_matrix : matriks jarak NxN

    Returns:
        route          : list of indices, panjang N
        total_distance : total jarak rute (termasuk balik ke start)
    """
    n = len(dist_matrix)

    # Step 1: mulai dari pasangan paling jauh
    max_dist = -1
    city_a, city_b = 0, 1
    for i in range(n):
        for j in range(i + 1, n):
            if dist_matrix[i][j] > max_dist:
                max_dist = dist_matrix[i][j]
                city_a, city_b = i, j

    tour = [city_a, city_b]
    remaining = set(range(n)) - {city_a, city_b}

    while remaining:
        # Step 2: pilih kota paling jauh dari tour saat ini
        farthest = max(
            remaining,
            key=lambda c: min(dist_matrix[c][t] for t in tour)
        )

        # Step 3: insert farthest ke posisi yang paling murah (cheapest insertion)
        best_pos = 0
        best_cost = float("inf")
        for i in range(len(tour)):
            j = (i + 1) % len(tour)
            # biaya = d(tour[i], farthest) + d(farthest, tour[j]) - d(tour[i], tour[j])
            cost = (
                dist_matrix[tour[i]][farthest]
                + dist_matrix[farthest][tour[j]]
                - dist_matrix[tour[i]][tour[j]]
            )
            if cost < best_cost:
                best_cost = cost
                best_pos = i + 1

        tour.insert(best_pos, farthest)
        remaining.remove(farthest)

    total_distance = _calc_total_distance(tour, dist_matrix)
    return tour, total_distance


# ══════════════════════════════════════════════════════════════════════════════
# 3. Random Tour
# ══════════════════════════════════════════════════════════════════════════════

def random_tour(dist_matrix: np.ndarray, seed: int | None = None) -> tuple[list[int], float]:
    """
    Random Tour — baseline perbandingan.

    Shuffle semua kota secara acak.

    Args:
        dist_matrix : matriks jarak NxN
        seed        : opsional, untuk reproduksi hasil

    Returns:
        route          : list of indices, panjang N (random order)
        total_distance : total jarak rute (termasuk balik ke start)
    """
    n = len(dist_matrix)
    route = list(range(n))
    rng = random.Random(seed)
    rng.shuffle(route)

    total_distance = _calc_total_distance(route, dist_matrix)
    return route, total_distance


# ══════════════════════════════════════════════════════════════════════════════
# Helper
# ══════════════════════════════════════════════════════════════════════════════

def _calc_total_distance(route: list[int], dist_matrix: np.ndarray) -> float:
    """Hitung total jarak rute, termasuk kembali ke kota awal."""
    total = 0.0
    n = len(route)
    for i in range(n):
        total += dist_matrix[route[i]][route[(i + 1) % n]]
    return round(total, 4)