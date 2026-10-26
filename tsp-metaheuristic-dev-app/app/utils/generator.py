"""
app/utils/generator.py
Pembangkit data kota acak dan template file input.

generate_cities(n, seed, pola, x_max, y_max) -> list of dict {"no","name","x","y"}
    pola "Uniform"   : titik tersebar merata
    pola "Cluster"   : titik berkelompok di beberapa pusat
    pola "Lingkaran" : titik pada lingkaran (rute optimal = keliling poligon,
                       dipakai untuk validasi algoritma)
write_template(path) -> file template .csv / .xlsx
"""
import math
import os
import random

PATTERNS = ["Uniform", "Cluster", "Lingkaran"]


def _name(i):
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if i == 0:
        return "Depot"
    return f"Kota {letters[(i - 1) % 26]}{'' if i <= 26 else (i - 1) // 26}"


def generate_cities(n, seed=None, pattern="Uniform", x_max=100.0, y_max=100.0):
    n = int(n)
    if n < 3:
        raise ValueError("Minimal 3 kota.")
    rng = random.Random(seed)
    pts = []
    if pattern == "Cluster":
        k = max(2, min(6, n // 8 + 2))
        centers = [(rng.uniform(0.15, 0.85) * x_max, rng.uniform(0.15, 0.85) * y_max)
                   for _ in range(k)]
        sx, sy = 0.08 * x_max, 0.08 * y_max
        for i in range(n):
            cx, cy = centers[i % k]
            x = min(max(rng.gauss(cx, sx), 0), x_max)
            y = min(max(rng.gauss(cy, sy), 0), y_max)
            pts.append((x, y))
        rng.shuffle(pts)
    elif pattern == "Lingkaran":
        r = 0.45 * min(x_max, y_max)
        cx, cy = x_max / 2, y_max / 2
        order = list(range(n))
        rng.shuffle(order)
        for k in order:
            a = 2 * math.pi * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    else:
        pts = [(rng.uniform(0, x_max), rng.uniform(0, y_max)) for _ in range(n)]

    return [{"no": i + 1, "name": _name(i), "x": round(x, 2), "y": round(y, 2)}
            for i, (x, y) in enumerate(pts)]


def circle_optimum(n, x_max=100.0, y_max=100.0):
    """Panjang rute optimal untuk pola Lingkaran (keliling poligon beraturan)."""
    r = 0.45 * min(x_max, y_max)
    return n * 2 * r * math.sin(math.pi / n)


TEMPLATE_ROWS = [
    (1, "Surabaya", 0, 0),
    (2, "Sidoarjo", 20, 15),
    (3, "Gresik", 18, 30),
    (4, "Mojokerto", 55, 40),
    (5, "Malang", 90, 45),
    (6, "Blitar", 110, 60),
]


def write_template(path):
    """Tulis template input (baris pertama = depot)."""
    import pandas as pd
    df = pd.DataFrame(TEMPLATE_ROWS, columns=["no", "name", "x", "y"])
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        df.to_csv(path, index=False)
    else:
        df.to_excel(path, index=False, sheet_name="Data Kota")
    return path


def save_cities(path, cities):
    """Simpan data kota (mis. hasil generate) ke .csv / .xlsx."""
    import pandas as pd
    df = pd.DataFrame(cities)[["no", "name", "x", "y"]]
    if os.path.splitext(path)[1].lower() == ".csv":
        df.to_csv(path, index=False)
    else:
        df.to_excel(path, index=False, sheet_name="Data Kota")
    return path
