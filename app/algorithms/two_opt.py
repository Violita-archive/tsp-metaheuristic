ry:
    from .constructive import route_distance
except ImportError:
    from constructive import route_distance


def _reverse_segment(route, i, j):
    """Balik segmen route[i : j+1]. Ini operasi inti dari 2-opt."""
    return route[:i] + route[i:j + 1][::-1] + route[j + 1:]


def two_opt(route, dist_matrix, max_iter=1000):
    """
    2-opt: coba semua pasangan edge (i, j). Klo membalik segmen diantara keduanya menghasilkan rute lebih pendek, pakai rute baru itu.
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
    # example: NN dulu, baru diperbaiki pakai 2-opt.
    from constructive import nearest_neighbor

    demo_matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    initial_route, initial_dist = nearest_neighbor(demo_matrix)
    print("Awal (NN):", initial_route, initial_dist)

    final_route, final_dist, hist = two_opt(initial_route, demo_matrix)
    print("Setelah 2-opt:", final_route, final_dist)
    print("History:", hist)
