import random

def route_distance(route, dist_matrix):
    """Hitung total jarak rute tertutup (kembali ke kota awal)"""
    total = 0.0
    n = len(route)
    for i in range(n):
        a = route[i]
        b = route[(i + 1) % n]
        total += dist_matrix[a][b]
    return total


def nearest_neighbor(dist_matrix, start=0):
    """
    Nearest Neighbor (NN).
    Mulai dari kota 'start', tiap langkah pindah ke kota TERDEKAT yang belum dikunjungi, sampai semua kota habis.
    """
    n = len(dist_matrix)
    unvisited = set(range(n))
    unvisited.remove(start)
    route = [start]
    current = start

    while unvisited:
        next_city = min(unvisited, key=lambda c: dist_matrix[current][c])
        route.append(next_city)
        unvisited.remove(next_city)
        current = next_city

    return route, route_distance(route, dist_matrix)


def farthest_insertion(dist_matrix, start=0):
    """
    Farthest Insertion (FI).
    Mulai dari 1 kota, lalu berulang kali:
      1. cari kota yang PALING JAUH dari rute saat ini
      2. sisipkan kota itu di posisi yang menambah jarak paling sedikit
    Biasanya hasilnya lebih baik dari NN, tapi lebih lambat.
    """
    n = len(dist_matrix)
    route = [start]
    remaining = set(range(n)) - {start}

    if remaining:
        farthest = max(remaining, key=lambda c: dist_matrix[start][c])
        route.append(farthest)
        remaining.remove(farthest)

    while remaining:
        def min_dist_to_route(c):
            return min(dist_matrix[c][r] for r in route)

        next_city = max(remaining, key=min_dist_to_route)

        best_increase = float("inf")
        best_pos = 0
        for i in range(len(route)):
            a = route[i]
            b = route[(i + 1) % len(route)]
            increase = (
                dist_matrix[a][next_city]
                + dist_matrix[next_city][b]
                - dist_matrix[a][b]
            )
            if increase < best_increase:
                best_increase = increase
                best_pos = i + 1

        route.insert(best_pos, next_city)
        remaining.remove(next_city)

    return route, route_distance(route, dist_matrix)


def random_route(dist_matrix, seed=None):
    """Rute acak. Dipakai sebagai baseline pembanding paling sederhana."""
    n = len(dist_matrix)
    route = list(range(n))
    rng = random.Random(seed)
    rng.shuffle(route)
    return route, route_distance(route, dist_matrix)


def load_demo_cities():
    import csv
    import math
    import os

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "..", "..", "data", "City.csv")
    names, coords = [], []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                row = {k.strip().lower(): v.strip() for k, v in row.items()}
                names.append(row["name"])
                coords.append((float(row["x"]), float(row["y"])))
    else:
        names = ["Surabaya", "Sidoarjo", "Gresik", "Mojokerto", "Malang", "Blitar"]
        coords = [(0, 0), (20, 15), (18, 30), (55, 40), (90, 45), (110, 60)]

    dist_matrix = [[math.dist(a, b) for b in coords] for a in coords]
    return names, dist_matrix


if __name__ == "__main__":
    # Demo: tiga metode konstruktif pada data City.csv
    names, D = load_demo_cities()
    print(f"Data: {len(names)} kota\n")
    print(f"{'Metode':<20}{'Jarak':>9}  Rute")
    for label, (route, dist) in [
        ("Nearest Neighbor", nearest_neighbor(D)),
        ("Farthest Insertion", farthest_insertion(D)),
        ("Random (seed=42)", random_route(D, seed=42)),
    ]:
        print(f"{label:<20}{dist:>9.2f}  " + " -> ".join(names[i] for i in route))
