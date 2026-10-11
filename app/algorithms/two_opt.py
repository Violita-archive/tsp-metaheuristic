try:
    from .constructive import route_distance
except ImportError:
    from constructive import route_distance


def _reverse_segment(route, i, j):
    """operasi inti dari 2-opt(balik segmen route[i : j+1])"""
    return route[:i] + route[i:j + 1][::-1] + route[j + 1:]


def two_opt(route, dist_matrix, max_iter=1000):
    """
    2-opt: coba semua pasangan edge (i, j). Kalau membalik segmen diantara keduanya menghasilkan rute lebih pendek, pakai rute baru itu.
    Ulangi sampai tidak ada perbaikan lagi (converge) atau max_iter habis.
    """
    best_route = route[:]
    best_distance = route_distance(best_route, dist_matrix)
    history = [best_distance]

    n = len(route)
    improved = True
    iterations = 0

    while improved and iterations < max_iter:
        improved = False
        for i in range(n - 1):
            for j in range(i + 1, n):
                new_route = _reverse_segment(best_route, i, j)
                new_distance = route_distance(new_route, dist_matrix)
                if new_distance < best_distance:
                    best_route = new_route
                    best_distance = new_distance
                    history.append(best_distance)
                    improved = True
        iterations += 1

    return best_route, best_distance, history


if __name__ == "__main__":
    from constructive import (nearest_neighbor, farthest_insertion,
                              random_route, load_demo_cities)

    names, D = load_demo_cities()
    print(f"Data: {len(names)} kota\n")
    print(f"{'Kombinasi':<26}{'Jarak':>9}  Rute")

    konstruksi = [
        ("NN", nearest_neighbor(D)),
        ("FI", farthest_insertion(D)),
        ("Random (seed=42)", random_route(D, seed=42)),
    ]
    for label, (route, dist) in konstruksi:
        print(f"{label:<26}{dist:>9.2f}  " + " -> ".join(names[i] for i in route))

        route2, dist2, hist = two_opt(route, D)
        print(f"{label + ' -> 2-Opt':<26}{dist2:>9.2f}  "
              + " -> ".join(names[i] for i in route2)
              + f"   (history: {[round(h, 2) for h in hist]})")
