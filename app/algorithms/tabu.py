"""
app/algorithms/tabu.py
Tabu Search untuk TSP.

Alur:
    1. Mulai dari initial_route (hasil constructive), posisi 0 = depot tetap
    2. Tiap iterasi: evaluasi neighbor sesuai move operator
       (semua move, atau sampel acak sebanyak `n_candidates`)
    3. Pilih neighbor terbaik yang TIDAK tabu, walaupun delta positif
       -- kecuali memenuhi aspiration criterion (lebih baik dari best global)
    4. Atribut move (pasangan kota) dimasukkan ke tabu list selama `tabu_tenure` iterasi
    5. Berhenti jika iterasi habis, best tidak membaik selama `stall_limit`
       iterasi, atau semua move tabu

Input:
    dist_matrix    : matriks jarak NxN
    initial_route  : list[int] dari constructive
    tabu_tenure    : lama sebuah atribut dilarang (None = max(5, N//2))
    max_iter       : batas iterasi
    move           : "swap" | "2opt" | "insertion"
    stall_limit    : 0 = nonaktif
    n_candidates   : 0 = semua neighbor dievaluasi
    aspiration     : aktif/nonaktif aspiration criterion
    seed           : untuk sampling kandidat
    names          : opsional, nama kota untuk teks log

Output:
    best_route, best_distance, history (+ info jika return_info=True)
"""

import random
import time

try:
    from .moves import (all_moves, delta as move_delta, apply_move, move_attr,
                        move_text, route_length)
except ImportError:
    from moves import (all_moves, delta as move_delta, apply_move, move_attr,
                       move_text, route_length)


def tabu_search(
    dist_matrix,
    initial_route,
    tabu_tenure=None,
    max_iter=500,
    move="swap",
    stall_limit=0,
    n_candidates=0,
    aspiration=True,
    seed=None,
    names=None,
    return_info=False,
):
    t0 = time.perf_counter()
    rng = random.Random(seed)
    d = dist_matrix
    n = len(initial_route)
    if tabu_tenure is None:
        tabu_tenure = max(5, n // 2)
    tabu_tenure = int(tabu_tenure)

    current = list(initial_route)
    current_dist = route_length(current, d)
    best, best_dist = current[:], current_dist

    moves = all_moves(n, move)
    # tabu_until[atribut] = iterasi terakhir atribut tersebut masih tabu
    tabu_until = {}
    history = [{
        "iter": 0, "move": "-", "delta": None, "aspiration": False,
        "current_dist": round(current_dist, 4), "best_dist": round(best_dist, 4),
        "tabu_size": 0, "tabu_list": "",
    }]
    stop_reason = "Iterasi maksimum tercapai"
    stall = 0
    it = 0
    if not moves:
        stop_reason = "Jumlah kota terlalu sedikit"
        max_iter = 0

    for it in range(1, int(max_iter) + 1):
        if n_candidates and n_candidates < len(moves):
            cand = rng.sample(moves, int(n_candidates))
        else:
            cand = moves

        best_move, best_dlt, used_asp = None, float("inf"), False
        for (i, j) in cand:
            dlt = move_delta(current, d, move, i, j)
            if dlt >= best_dlt:
                continue
            attr = move_attr(current, move, i, j)
            is_tabu = tabu_until.get(attr, 0) >= it
            if is_tabu:
                if not (aspiration and current_dist + dlt < best_dist - 1e-12):
                    continue
            best_move, best_dlt, used_asp = (i, j), dlt, is_tabu

        if best_move is None:
            it -= 1
            stop_reason = "Semua move berstatus tabu"
            break

        i, j = best_move
        attr = move_attr(current, move, i, j)
        label = move_text(current, move, i, j, names)
        current = apply_move(current, move, i, j)
        current_dist += best_dlt
        tabu_until[attr] = it + tabu_tenure

        if current_dist < best_dist - 1e-12:
            best, best_dist = current[:], current_dist
            stall = 0
        else:
            stall += 1

        active = {a: t for a, t in tabu_until.items() if t > it}
        tabu_until = active
        tabu_txt = ""
        if names is not None and len(active) <= 30:
            tabu_txt = ", ".join(
                "{" + ",".join(sorted(names[c] for c in a)) + "}:" + str(t - it)
                for a, t in sorted(active.items(), key=lambda kv: kv[1])
            )

        history.append({
            "iter": it, "move": label, "delta": round(best_dlt, 4),
            "aspiration": used_asp,
            "current_dist": round(current_dist, 4), "best_dist": round(best_dist, 4),
            "tabu_size": len(active), "tabu_list": tabu_txt,
        })

        if stall_limit and stall >= stall_limit:
            stop_reason = f"Tidak ada perbaikan selama {stall_limit} iterasi"
            break

    best_dist = route_length(best, d)
    info = {"stop_reason": stop_reason, "iterations": it,
            "time": time.perf_counter() - t0, "tenure": tabu_tenure}
    if return_info:
        return best, round(best_dist, 4), history, info
    return best, round(best_dist, 4), history
