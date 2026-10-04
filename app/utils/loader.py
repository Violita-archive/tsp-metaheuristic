"""
app/utils/loader.py
Load city data from CSV or Excel.

Expected format:
    name, x, y
    Surabaya, 0, 0
    Malang, 90, 45
    ...
"""

import csv
import os


def load_cities(filepath: str) -> list[dict]:
    """
    Load cities from CSV or Excel file.

    Returns:
        List of dicts: [{"name": str, "x": float, "y": float}, ...]

    Raises:
        FileNotFoundError: file tidak ada
        ValueError: format kolom salah / file extension tidak support
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File tidak ditemukan: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".csv":
        return _load_csv(filepath)
    elif ext in (".xlsx", ".xls"):
        return _load_excel(filepath)
    else:
        raise ValueError(f"Format tidak support: {ext}. Gunakan .csv / .xlsx / .xls")


def _load_csv(filepath: str) -> list[dict]:
    cities = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        _validate_headers(reader.fieldnames, filepath)
        for i, row in enumerate(reader, start=2):  # baris 2 = setelah header
            try:
                cities.append({
                    "name": row["name"].strip(),
                    "x": float(row["x"]),
                    "y": float(row["y"]),
                })
            except (KeyError, ValueError) as e:
                raise ValueError(f"Error di baris {i}: {e}")
    if len(cities) < 3:
        raise ValueError("Minimal 3 kota untuk TSP.")
    return cities


def _load_excel(filepath: str) -> list[dict]:
    try:
        import openpyxl
    except ImportError:
        raise ImportError("Install openpyxl dulu: pip install openpyxl")

    wb = openpyxl.load_workbook(filepath, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    if not rows:
        raise ValueError("File Excel kosong.")

    headers = [str(h).strip().lower() for h in rows[0]]
    _validate_headers(headers, filepath)

    cities = []
    for i, row in enumerate(rows[1:], start=2):
        try:
            name_idx = headers.index("name")
            x_idx = headers.index("x")
            y_idx = headers.index("y")
            cities.append({
                "name": str(row[name_idx]).strip(),
                "x": float(row[x_idx]),
                "y": float(row[y_idx]),
            })
        except (IndexError, TypeError, ValueError) as e:
            raise ValueError(f"Error di baris {i}: {e}")

    if len(cities) < 3:
        raise ValueError("Minimal 3 kota untuk TSP.")
    return cities


def _validate_headers(headers, filepath):
    if headers is None:
        raise ValueError(f"File kosong atau header tidak terbaca: {filepath}")
    headers_lower = [h.strip().lower() for h in headers]
    required = {"name", "x", "y"}
    missing = required - set(headers_lower)
    if missing:
        raise ValueError(
            f"Kolom tidak lengkap. Butuh: {required}. "
            f"Tidak ada: {missing}. Yang ada: {set(headers_lower)}"
        )


# ── Helpers untuk algoritma ────────────────────────────────────────────────

def get_coords(cities: list[dict]) -> list[tuple[float, float]]:
    """Return list of (x, y) tuples — dipakai buat distance_matrix."""
    return [(c["x"], c["y"]) for c in cities]


def get_names(cities: list[dict]) -> list[str]:
    """Return list of city names — dipakai buat display route."""
    return [c["name"] for c in cities]


def route_to_names(route: list[int], cities: list[dict]) -> list[str]:
    """Convert route (list of indices) → list of city names."""
    names = get_names(cities)
    return [names[i] for i in route]