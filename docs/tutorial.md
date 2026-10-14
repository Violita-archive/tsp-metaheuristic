# Tutorial: Perhitungan Manual TSP (2-Opt, Simulated Annealing, Tabu Search)

Folder `docs` berisi perhitungan manual tiga metode heuristik untuk *Traveling Salesman Problem* (TSP) pada dataset `City.csv`.

## Isi Dokumen

| File | Isi |
|---|---|
| [manual-2opt.md](manual-2opt.md) | Local search 2-Opt, best improvement, sampai konvergen |
| [manual-sa.md](manual-sa.md) | Simulated Annealing, 15 iterasi, bilangan acak ditetapkan (seed 2) |
| [manual-tabu.md](manual-tabu.md) | Tabu Search, 6 iterasi, tenure 3, aspirasi |
| tutorial.md | Panduan ini |

## Dataset

`City.csv` berisi 6 kota dengan koordinat (x, y):

| No | Kota | x | y |
|---|---|---|---|
| 0 | Surabaya | 0 | 0 |
| 1 | Sidoarjo | 20 | 15 |
| 2 | Gresik | 18 | 30 |
| 3 | Mojokerto | 55 | 40 |
| 4 | Malang | 90 | 45 |
| 5 | Blitar | 110 | 60 |

Jarak antar kota memakai Euclidean: $d(A,B)=\sqrt{(x_A-x_B)^2+(y_A-y_B)^2}$.
Rute berupa siklus tertutup: kota terakhir kembali ke Surabaya.

## Solusi Awal (sama untuk semua metode)

`Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya` dengan total jarak **264.12**.

## Notasi Move 2-Opt

Tour disimpan sebagai daftar posisi 0..5, posisi 0 (Surabaya) tidak dipindah. Move `(i,j)` membalik segmen dari posisi `i` sampai `j`.

- `a` = kota di posisi `i-1`, `b` = kota di posisi `i`
- `c` = kota di posisi `j`, `e` = kota di posisi `j+1` (siklik)

$$\Delta = d(a,c)+d(b,e)-d(a,b)-d(c,e)$$

$\Delta<0$ berarti rute makin pendek. Move `(1,5)` dilewati karena hanya membalik arah seluruh rute (Δ = 0).

## Cara Membaca Dokumen

1. Mulai dari `manual-2opt.md`, karena move dan Δ dijelaskan paling lengkap di sana.
2. Di `manual-sa.md`, satu iterasi = satu move acak. Lihat kolom Δ, p, dan u untuk mengerti kenapa move yang lebih buruk kadang diterima.
3. Di `manual-tabu.md`, satu iterasi = evaluasi semua move, pilih yang terbaik yang tidak tabu, termasuk yang memperburuk jarak.

## Perbandingan Hasil

| Metode | Rute akhir | Jarak | Catatan |
|---|---|---|---|
| Solusi awal | Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya | 264.12 | - |
| 2-Opt | Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya | 257.99 | Konvergen di iterasi 3 |
| Simulated Annealing | Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya | 257.99 | Bergantung seed |
| Tabu Search | Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya | 257.99 | Optimum ditemukan di iterasi 2 |

Untuk 6 kota, brute force (5! = 120 rute) menunjukkan **257.99 adalah optimum global**, jadi ketiga metode mencapainya.

## Verifikasi dengan Python

```python
import csv, math, itertools

rows = list(csv.DictReader(open("City.csv")))
P = [(float(r["x"]), float(r["y"])) for r in rows]
n = len(P)
d = [[math.dist(P[i], P[j]) for j in range(n)] for i in range(n)]

def total(t):
    return sum(d[t[i]][t[(i + 1) % n]] for i in range(n))

best = min(itertools.permutations(range(1, n)), key=lambda p: total([0, *p]))
print([rows[k]["name"] for k in [0, *best]], round(total([0, *best]), 2))
```

## Catatan Penulisan

- Rumus memakai LaTeX (`$...$` dan `$$...$$`), yang dirender langsung oleh GitHub.
- Angka dibulatkan 2 desimal, jadi penjumlahan manual bisa berbeda 0.01 dari nilai yang tertulis.
- Hasil SA bergantung bilangan acak. Dokumen memakai `random.Random(2)` agar bisa direproduksi.
