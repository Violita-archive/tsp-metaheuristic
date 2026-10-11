"""
app/algorithms/sa.py
Simulated Annealing (SA) untuk TSP.

Alur:
    1. Mulai dari initial_route (hasil constructive)
    2. Tiap iterasi: swap 2 kota acak -> hitung delta jarak
    3. Terima solusi baru jika lebih baik, atau dengan probabilitas e^(-delta/T)
    4. Turunkan suhu: T = T * cooling_rate
    5. Berhenti saat T < T_min atau iterasi habis

Input:
    dist_matrix    : np.ndarray (NxN)
    initial_route  : list[int] dari constructive
    T_start        : suhu awal (default 1000)
    T_min          : suhu batas bawah (default 1e-3)
    cooling_rate   : laju pendinginan (default 0.995)
    max_iter       : batas iterasi (default 10000)
    seed           : opsional, untuk reproduksi

Output:
    best_route     : list[int]
    best_distance  : float
    history        : list[dict] -- untuk plot konvergensi
"""

import math
import random
import numpy as np


def simulated_annealing(
    dist_matrix: np.ndarray,
    initial_route: list[int],
    T_start: float = 1000.0,
    T_min: float = 1e-3,
    cooling_rate: float = 0.995,
    max_iter: int = 10000,
    seed: int | None = None,
) -> tuple[list[int], float, list[dict]]:
    """
    Simulated Annealing untuk TSP.

    Returns:
        best_route     : rute terbaik (list of indices)
        best_distance  : jarak terbaik
        history        : list of {"iter": int, "temperature": float,
                                  "current_dist": float, "best_dist": float}
                         -- dicatat setiap 100 iterasi, untuk grafik konvergensi
    """
    rng = random.Random(seed)

    current_route = initial_route[:]
    current_dist = _total_distance(current_route, dist_matrix)

    best_route = current_route[:]
    best_dist = current_dist

    T = T_start
    history = []

    for iteration in range(max_iter):
        if T < T_min:
            break

        # -- Neighbourhood: swap 2 posisi acak ------------------------------------
        i, j = sorted(rng.sample(range(len(current_route)), 2))
        neighbor = current_route[:]
        neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
        neighbor_dist = _total_distance(neighbor, dist_matrix)

        # -- Acceptance criterion -------------------------------------------------
        delta = neighbor_dist - current_dist
        if delta < 0 or rng.random() < math.exp(-delta / T):
            current_route = neighbor
            current_dist = neighbor_dist

        # -- Update best ----------------------------------------------------------
        if current_dist < best_dist:
            best_route = current_route[:]
            best_dist = current_dist

        # -- Cooling --------------------------------------------------------------
        T *= cooling_rate

        # -- Catat history setiap 100 iterasi ------------------------------------
        if iteration % 100 == 0:
            history.append({
                "iter": iteration,
                "temperature": round(T, 6),
                "current_dist": round(current_dist, 4),
                "best_dist": round(best_dist, 4),
            })

    # catat kondisi akhir
    history.append({
        "iter": iteration,
        "temperature": round(T, 6),
        "current_dist": round(current_dist, 4),
        "best_dist": round(best_dist, 4),
    })

    return best_route, round(best_dist, 4), history


# -- Helper -----------------------------------------------------------------------

def _total_distance(route: list[int], dist_matrix: np.ndarray) -> float:
    n = len(route)
    return sum(
        dist_matrix[route[i]][route[(i + 1) % n]]
        for i in range(n)
    )