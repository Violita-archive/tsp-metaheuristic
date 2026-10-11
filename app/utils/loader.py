"""
app/utils/loader.py
Membaca dataset kota (CSV / Excel) untuk TSP Optimizer.

Format kolom : name (atau Nama), x, y   -- kolom No/ID opsional
Baris pertama = depot (index 0).

Representasi "cities" = list of dict:
    [{"no": 1, "name": "Surabaya", "x": 0.0, "y": 0.0}, ...]

Fungsi yang dipakai main.py:
    load_cities(path), get_coords(cities), get_names(cities), route_to_names(cities, route)
"""
import os
import pandas as pd

# folder data di root repo:  app/utils/ -> app/ -> root -> data/
DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
)

_ALIAS = {
    "nama": "name", "name": "name", "kota": "name", "city": "name",
    "x": "x", "lon": "x", "lng": "x", "longitude": "x",
    "y": "y", "lat": "y", "latitude": "y",
    "no": "no", "id": "no",
}


def list_datasets(folder=DATA_DIR):
    """Daftar file dataset (.csv/.xls/.xlsx) di folder data."""
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder)
                  if f.lower().endswith((".csv", ".xls", ".xlsx")))


def load_cities(path):
    """Baca file CSV/Excel -> list of dict {"no","name","x","y"}."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File tidak ditemukan: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        # sep=None -> otomatis deteksi koma / titik koma; utf-8-sig buang BOM Excel
        df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Format '{ext}' tidak didukung. Pakai .csv / .xls / .xlsx")

    df.columns = [_ALIAS.get(str(c).strip().lower(), str(c).strip().lower())
                  for c in df.columns]
    missing = [c for c in ("name", "x", "y") if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom wajib tidak ada: {missing}. "
                         "Dibutuhkan: name/Nama, x/X, y/Y (No opsional).")

    df = df.dropna(subset=["name", "x", "y"]).reset_index(drop=True)
    try:
        df["x"] = pd.to_numeric(df["x"])
        df["y"] = pd.to_numeric(df["y"])
    except (ValueError, TypeError):
        raise ValueError("Kolom x dan y harus berisi angka.")
    if len(df) < 3:
        raise ValueError("Minimal 3 kota untuk TSP.")

    return [
        {"no": i + 1, "name": str(r["name"]).strip(),
         "x": float(r["x"]), "y": float(r["y"])}
        for i, r in df.iterrows()
    ]


def get_coords(cities):
    """List of (x, y)."""
    return [(c["x"], c["y"]) for c in cities]


def get_names(cities):
    """List nama kota."""
    return [c["name"] for c in cities]


def route_to_names(cities, route):
    """Ubah rute (list index) -> list nama kota."""
    return [cities[i]["name"] for i in route]
