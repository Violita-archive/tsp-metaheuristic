"""
app/algorithms/sa.py
Simulated Annealing (SA) untuk TSP.

Alur:
    1. Mulai dari initial_route (hasil constructive), posisi 0 = depot tetap
    2. Tiap iterasi: bangkitkan 1 neighbor acak sesuai move operator
    3. Terima jika delta < 0, atau jika u < e^(-delta/T)
    4. Setiap L iterasi, suhu diturunkan: T = alpha * T
    5. Berhenti jika T < T_min, iterasi habis, atau best tidak membaik
       selama `stall_limit` iterasi

Input:
    dist_matrix    : matriks jarak NxN
    initial_route  : list[int] dari constructive
    T_start        : suhu awal T0
    T_min          : suhu batas bawah
    cooling_rate   : alpha (0 < alpha < 1)
    max_iter       : batas iterasi
    seed           : opsional, untuk reproduksi
    move           : "swap" | "2opt" | "insertion"
    iter_per_temp  : L, banyak iterasi pada satu suhu
    stall_limit    : 0 = nonaktif
    names          : opsional, nama kota untuk teks log

Output:
    best_route, best_distance, history (+ info jika return_info=True)
"""

import math
import random
import time

try:
    from .moves import random_move, delta as move_delta, apply_move, move_text, route_length
except ImportError:
    from moves import random_move, delta as move_delta, apply_move, move_text, route_length


def estimate_T0(dist_matrix, route, move="swap", p0=0.8, samples=300, seed=None):
    """
    Estimasi suhu awal sehingga peluang menerima move memburuk rata-rata = p0.
    T0 = -mean(delta+) / ln(p0), delta+ = delta positif dari sampel move acak.
    """
    rng = random.Random(seed)
    n = len(route)
    if n < 4:
        return 1.0
    pos = []
    for _ in range(samples):
        i, j = random_move(rng, n, move)
        dlt = move_delta(route, dist_matrix, move, i, j)
        if dlt > 0:
            pos.append(dlt)
    if not pos:
        return 1.0
    return -(sum(pos) / len(pos)) / math.log(p0)


def iterations_to_Tmin(T_start, T_min, cooling_rate, iter_per_temp=1):
    """Banyak iterasi sampai T < T_min (untuk informasi stopping criteria)."""
    if not (0 < cooling_rate < 1) or T_start <= 0 or T_min <= 0 or T_start < T_min:
        return None
    k = math.ceil(math.log(T_min / T_start) / math.log(cooling_rate))
    return k * max(1, int(iter_per_temp))


def simulated_annealing(
    dist_matrix,
    initial_route,
    T_start=1000.0,
    T_min=1e-3,
    cooling_rate=0.995,
    max_iter=10000,
    seed=None,
    move="swap",
    iter_per_temp=1,
    stall_limit=0,
    names=None,
    log_every=1,
    return_info=False,
):
    rng = random.Random(seed)
    t0 = time.perf_counter()
    d = dist_matrix
    n = len(initial_route)

    current = list(initial_route)
    current_dist = route_length(current, d)
    best, best_dist = current[:], current_dist

    T = float(T_start)
    L = max(1, int(iter_per_temp))
    history = [{
        "iter": 0, "temperature": round(T, 6), "move": "-", "delta": None,
        "prob": None, "u": None, "accepted": None,
        "current_dist": round(current_dist, 4), "best_dist": round(best_dist, 4),
    }]
    stop_reason = "Iterasi maksimum tercapai"
    stall = 0
    it = 0

    if n < 4 and move == "2opt" or n < 3:
        stop_reason = "Jumlah kota terlalu sedikit"
        max_iter = 0

    for it in range(1, int(max_iter) + 1):
        if T < T_min:
            it -= 1
            stop_reason = "Suhu minimum tercapai"
            break

        i, j = random_move(rng, n, move)
        dlt = move_delta(current, d, move, i, j)
        u = rng.random()
        prob = None
        if dlt < 0:
            accepted = True
        else:
            prob = math.exp(-dlt / T) if T > 0 else 0.0
            accepted = u < prob

        label = move_text(current, move, i, j, names)
        if accepted:
            current = apply_move(current, move, i, j)
            current_dist += dlt

        if current_dist < best_dist - 1e-12:
            best, best_dist = current[:], current_dist
            stall = 0
        else:
            stall += 1

        if it % log_every == 0 or it == max_iter:
            history.append({
                "iter": it, "temperature": round(T, 6), "move": label,
                "delta": round(dlt, 4), "prob": None if prob is None else round(prob, 4),
                "u": round(u, 4), "accepted": accepted,
                "current_dist": round(current_dist, 4), "best_dist": round(best_dist, 4),
            })

        if it % L == 0:
            T *= cooling_rate

        if stall_limit and stall >= stall_limit:
            stop_reason = f"Tidak ada perbaikan selama {stall_limit} iterasi"
            break

    # jarak dihitung ulang supaya bebas akumulasi galat pembulatan
    best_dist = route_length(best, d)
    info = {"stop_reason": stop_reason, "iterations": it,
            "time": time.perf_counter() - t0, "final_T": T}
    if return_info:
        return best, round(best_dist, 4), history, info
    return best, round(best_dist, 4), history
