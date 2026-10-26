# Perhitungan Manual Tabu Search (TSP)

Dokumen ini menunjukkan perhitungan manual **Tabu Search** pada dataset `City.csv` (6 kota). Angka dibulatkan 2 desimal.

## 1. Data

| No | Kota | x | y |
|---|---|---|---|
| 0 | Surabaya | 0 | 0 |
| 1 | Sidoarjo | 20 | 15 |
| 2 | Gresik | 18 | 30 |
| 3 | Mojokerto | 55 | 40 |
| 4 | Malang | 90 | 45 |
| 5 | Blitar | 110 | 60 |

## 2. Matriks Jarak Euclidean

Rumus: $d(A,B)=\sqrt{(x_A-x_B)^2+(y_A-y_B)^2}$

Contoh: Surabaya→Sidoarjo = $\sqrt{(20-0)^2+(15-0)^2}=\sqrt{625}=25.00$

| | Surabaya | Sidoarjo | Gresik | Mojokerto | Malang | Blitar |
|---|---|---|---|---|---|---|
| **Surabaya** | 0.00 | 25.00 | 34.99 | 68.01 | 100.62 | 125.30 |
| **Sidoarjo** | 25.00 | 0.00 | 15.13 | 43.01 | 76.16 | 100.62 |
| **Gresik** | 34.99 | 15.13 | 0.00 | 38.33 | 73.55 | 96.77 |
| **Mojokerto** | 68.01 | 43.01 | 38.33 | 0.00 | 35.36 | 58.52 |
| **Malang** | 100.62 | 76.16 | 73.55 | 35.36 | 0.00 | 25.00 |
| **Blitar** | 125.30 | 100.62 | 96.77 | 58.52 | 25.00 | 0.00 |

## 3. Solusi Awal

`Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya`

Total jarak = 25.00 + 15.13 + 38.33 + 35.36 + 25.00 + 125.30 = **264.12**

## 4. Parameter

| Parameter | Nilai |
|---|---|
| Neighborhood | Semua move 2-Opt $(i,j)$, kecuali $(1,5)$ yang hanya membalik seluruh rute |
| Tabu tenure | 3 iterasi |
| Atribut tabu | Pasangan kota di ujung segmen yang dibalik, $\{b,c\}$ |
| Aspirasi | Move tabu boleh dipakai jika menghasilkan jarak < terbaik global |
| Iterasi | 6 |

## 5. Aturan Tabu Search

Neighbor dibangkitkan dengan **move 2-Opt**: pilih posisi `i<j` (posisi 0 = Surabaya tetap), balik segmen `i..j`.

$$\Delta = d(a,c)+d(b,e)-d(a,b)-d(c,e)$$

dengan `a` = kota sebelum posisi i, `b` = kota di posisi i, `c` = kota di posisi j, `e` = kota setelah posisi j (siklik).

Tiap iterasi:

1. Evaluasi semua neighbor.
2. Pilih neighbor dengan Δ terkecil yang **tidak tabu** (atau yang tabu tetapi memenuhi aspirasi), **walaupun Δ positif**.
3. Terapkan move, masukkan pasangan kota `{b,c}` ke tabu list dengan sisa tenure 3, lalu kurangi sisa tenure entri lain 1.

## 6. Iterasi

### Ringkasan

| Iter | Move | Δ | Jarak sekarang | Jarak terbaik |
|---|---|---|---|---|
| 1 | (2,5) | -4.82 | 259.29 | 259.29 |
| 2 | (2,3) | -1.30 | 257.99 | 257.99 |
| 3 | (2,4) | 2.07 | 260.07 | 257.99 |
| 4 | (2,5) | 5.14 | 265.21 | 257.99 |
| 5 | (1,2) | 12.60 | 277.81 | 257.99 |
| 6 | (2,5) | -19.81 | 257.99 | 257.99 |

### Detail per iterasi

### Iterasi 1

Tour: `Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya` (jarak 264.12)

Tabu list awal: (kosong)

| Move (i,j) | Segmen ujung {b,c} | Δ | Jarak baru | Status |
|---|---|---|---|---|
| (1,2) | {Sidoarjo, Gresik} | 14.67 | 278.79 | boleh |
| (1,3) | {Sidoarjo, Mojokerto} | 83.81 | 347.93 | boleh |
| (1,4) | {Sidoarjo, Malang} | 151.25 | 415.36 | boleh |
| (2,3) | {Gresik, Mojokerto} | 66.07 | 330.18 | boleh |
| (2,4) | {Gresik, Malang} | 132.79 | 396.91 | boleh |
| (2,5) | {Gresik, Blitar} | -4.82 | 259.29 | boleh ✅ **dipilih** |
| (3,4) | {Mojokerto, Malang} | 68.74 | 332.86 | boleh |
| (3,5) | {Mojokerto, Blitar} | 1.15 | 265.26 | boleh |
| (4,5) | {Malang, Blitar} | -1.51 | 262.61 | boleh |

Move dipilih **(2,5)** dengan Δ = -4.82. Tour baru: `Surabaya → Sidoarjo → Blitar → Malang → Mojokerto → Gresik → Surabaya` (jarak **259.29**). Terbaik sejauh ini: **259.29**. Tambah `{Gresik, Blitar}` ke tabu list (tenure 3).

### Iterasi 2

Tour: `Surabaya → Sidoarjo → Blitar → Malang → Mojokerto → Gresik → Surabaya` (jarak 259.29)

Tabu list awal: {Blitar, Gresik}:3

| Move (i,j) | Segmen ujung {b,c} | Δ | Jarak baru | Status |
|---|---|---|---|---|
| (1,2) | {Sidoarjo, Blitar} | 151.46 | 410.75 | boleh |
| (1,3) | {Sidoarjo, Malang} | 83.28 | 342.57 | boleh |
| (1,4) | {Sidoarjo, Mojokerto} | 19.81 | 279.10 | boleh |
| (2,3) | {Blitar, Malang} | -1.30 | 257.99 | boleh ✅ **dipilih** |
| (2,4) | {Blitar, Mojokerto} | 0.83 | 260.12 | boleh |
| (2,5) | {Blitar, Gresik} | 4.82 | 264.12 | TABU |
| (3,4) | {Malang, Mojokerto} | 68.74 | 328.03 | boleh |
| (3,5) | {Malang, Gresik} | 137.41 | 396.70 | boleh |
| (4,5) | {Mojokerto, Gresik} | 71.21 | 330.50 | boleh |

Move dipilih **(2,3)** dengan Δ = -1.30. Tour baru: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya` (jarak **257.99**). Terbaik sejauh ini: **257.99**. Tambah `{Blitar, Malang}` ke tabu list (tenure 3).

### Iterasi 3

Tour: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya` (jarak 257.99)

Tabu list awal: {Blitar, Gresik}:2, {Blitar, Malang}:3

| Move (i,j) | Segmen ujung {b,c} | Δ | Jarak baru | Status |
|---|---|---|---|---|
| (1,2) | {Sidoarjo, Malang} | 151.25 | 409.24 | boleh |
| (1,3) | {Sidoarjo, Blitar} | 84.79 | 342.78 | boleh |
| (1,4) | {Sidoarjo, Mojokerto} | 19.81 | 277.81 | boleh |
| (2,3) | {Malang, Blitar} | 1.30 | 259.29 | TABU |
| (2,4) | {Malang, Mojokerto} | 2.07 | 260.07 | boleh ✅ **dipilih** |
| (2,5) | {Malang, Gresik} | 4.61 | 262.61 | boleh |
| (3,4) | {Blitar, Mojokerto} | 68.80 | 326.79 | boleh |
| (3,5) | {Blitar, Gresik} | 138.86 | 396.85 | TABU |
| (4,5) | {Mojokerto, Gresik} | 71.27 | 329.26 | boleh |

Move dipilih **(2,4)** dengan Δ = 2.07. Tour baru: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**). Terbaik sejauh ini: **257.99**. Tambah `{Malang, Mojokerto}` ke tabu list (tenure 3).

### Iterasi 4

Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)

Tabu list awal: {Blitar, Gresik}:1, {Blitar, Malang}:2, {Malang, Mojokerto}:3

| Move (i,j) | Segmen ujung {b,c} | Δ | Jarak baru | Status |
|---|---|---|---|---|
| (1,2) | {Sidoarjo, Mojokerto} | 85.11 | 345.17 | boleh |
| (1,3) | {Sidoarjo, Blitar} | 151.46 | 411.52 | boleh |
| (1,4) | {Sidoarjo, Malang} | 17.21 | 277.28 | boleh |
| (2,3) | {Mojokerto, Blitar} | 67.97 | 328.03 | boleh |
| (2,4) | {Mojokerto, Malang} | -2.07 | 257.99 | TABU |
| (2,5) | {Mojokerto, Gresik} | 5.14 | 265.21 | boleh ✅ **dipilih** |
| (3,4) | {Blitar, Malang} | 0.05 | 260.12 | TABU |
| (3,5) | {Blitar, Gresik} | 70.12 | 330.18 | TABU |
| (4,5) | {Malang, Gresik} | 137.41 | 397.47 | boleh |

Move dipilih **(2,5)** dengan Δ = 5.14. Tour baru: `Surabaya → Sidoarjo → Gresik → Malang → Blitar → Mojokerto → Surabaya` (jarak **265.21**). Terbaik sejauh ini: **257.99**. Tambah `{Mojokerto, Gresik}` ke tabu list (tenure 3).

### Iterasi 5

Tour: `Surabaya → Sidoarjo → Gresik → Malang → Blitar → Mojokerto → Surabaya` (jarak 265.21)

Tabu list awal: {Blitar, Malang}:1, {Malang, Mojokerto}:2, {Gresik, Mojokerto}:3

| Move (i,j) | Segmen ujung {b,c} | Δ | Jarak baru | Status |
|---|---|---|---|---|
| (1,2) | {Sidoarjo, Gresik} | 12.60 | 277.81 | boleh ✅ **dipilih** |
| (1,3) | {Sidoarjo, Malang} | 151.25 | 416.46 | boleh |
| (1,4) | {Sidoarjo, Blitar} | 84.79 | 350.00 | boleh |
| (2,3) | {Gresik, Malang} | 132.79 | 398.00 | boleh |
| (2,4) | {Gresik, Blitar} | 65.29 | 330.50 | boleh |
| (2,5) | {Gresik, Mojokerto} | -5.14 | 260.07 | TABU |
| (3,4) | {Malang, Blitar} | 0.05 | 265.26 | TABU |
| (3,5) | {Malang, Mojokerto} | -2.60 | 262.61 | TABU |
| (4,5) | {Blitar, Mojokerto} | 67.65 | 332.86 | boleh |

Move dipilih **(1,2)** dengan Δ = 12.60. Tour baru: `Surabaya → Gresik → Sidoarjo → Malang → Blitar → Mojokerto → Surabaya` (jarak **277.81**). Terbaik sejauh ini: **257.99**. Tambah `{Sidoarjo, Gresik}` ke tabu list (tenure 3).

### Iterasi 6

Tour: `Surabaya → Gresik → Sidoarjo → Malang → Blitar → Mojokerto → Surabaya` (jarak 277.81)

Tabu list awal: {Malang, Mojokerto}:1, {Gresik, Mojokerto}:2, {Gresik, Sidoarjo}:3

| Move (i,j) | Segmen ujung {b,c} | Δ | Jarak baru | Status |
|---|---|---|---|---|
| (1,2) | {Gresik, Sidoarjo} | -12.60 | 265.21 | TABU |
| (1,3) | {Gresik, Malang} | 137.41 | 415.21 | boleh |
| (1,4) | {Gresik, Blitar} | 70.12 | 347.93 | boleh |
| (2,3) | {Sidoarjo, Malang} | 134.04 | 411.84 | boleh |
| (2,4) | {Sidoarjo, Blitar} | 66.12 | 343.93 | boleh |
| (2,5) | {Sidoarjo, Mojokerto} | -19.81 | 257.99 | boleh ✅ **dipilih** |
| (3,4) | {Malang, Blitar} | 1.30 | 279.10 | boleh |
| (3,5) | {Malang, Mojokerto} | -0.53 | 277.28 | TABU |
| (4,5) | {Blitar, Mojokerto} | 67.65 | 345.45 | boleh |

Move dipilih **(2,5)** dengan Δ = -19.81. Tour baru: `Surabaya → Gresik → Mojokerto → Blitar → Malang → Sidoarjo → Surabaya` (jarak **257.99**). Terbaik sejauh ini: **257.99**. Tambah `{Sidoarjo, Mojokerto}` ke tabu list (tenure 3).

## 7. Hasil Akhir

- Rute terbaik: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya`
- Total jarak terbaik: **257.99**
- Peningkatan dari solusi awal: 264.12 → 257.99 (hemat 6.12, 2.32%)

Catatan: tabu list membuat pencarian bisa melewati local optimum dengan menerima move yang memperburuk jarak sementara (lihat iterasi dengan Δ positif), sambil mencegah kembali ke move yang baru saja dilakukan.
