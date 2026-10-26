# Perhitungan Manual Simulated Annealing (TSP)

Dokumen ini menunjukkan perhitungan manual **Simulated Annealing (SA)** pada dataset `City.csv` (6 kota). Angka dibulatkan 2 desimal.

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
| Suhu awal $T_0$ | 100 |
| Cooling rate $\alpha$ | 0.85 ($T_{k+1}=\alpha\cdot T_k$) |
| Iterasi | 15 (1 neighbor per iterasi) |
| Seed random | 2 (Python `random.Random(2)`) |

## 5. Aturan SA

Neighbor dibangkitkan dengan **move 2-Opt**: pilih posisi `i<j` (posisi 0 = Surabaya tetap), balik segmen `i..j`.

$$\Delta = d(a,c)+d(b,e)-d(a,b)-d(c,e)$$

dengan `a` = kota sebelum posisi i, `b` = kota di posisi i, `c` = kota di posisi j, `e` = kota setelah posisi j (siklik).

**Aturan penerimaan (Metropolis):**

- Jika $\Delta<0$ → terima.
- Jika $\Delta\ge0$ → hitung $p=e^{-\Delta/T}$, bangkitkan $u\in[0,1)$. Terima jika $u<p$, tolak jika sebaliknya.

Bilangan acak $(i,j)$ dan $u$ sudah ditetapkan di tabel agar perhitungan bisa direproduksi manual.

## 6. Iterasi

### Ringkasan

| Iter | T | Move (i,j) | Δ | p | u | Keputusan | Jarak sekarang | Jarak terbaik |
|---|---|---|---|---|---|---|---|---|
| 1 | 100.00 | (1,3) | 83.81 | 0.4325 | 0.83 | Tolak | 264.12 | 264.12 |
| 2 | 85.00 | (3,5) | 1.15 | 0.9866 | 0.60 | Terima | 265.26 | 264.12 |
| 3 | 72.25 | (2,5) | -5.14 | - | - | Terima | 260.12 | 260.12 |
| 4 | 61.41 | (3,4) | -0.05 | - | - | Terima | 260.07 | 260.07 |
| 5 | 52.20 | (3,4) | 0.05 | 0.9990 | 0.90 | Terima | 260.12 | 260.07 |
| 6 | 44.37 | (1,3) | 151.25 | 0.0331 | 0.46 | Tolak | 260.12 | 260.07 |
| 7 | 37.71 | (3,4) | -0.05 | - | - | Terima | 260.07 | 260.07 |
| 8 | 32.06 | (2,5) | 5.14 | 0.8518 | 0.56 | Terima | 265.21 | 260.07 |
| 9 | 27.25 | (2,5) | -5.14 | - | - | Terima | 260.07 | 260.07 |
| 10 | 23.16 | (2,3) | 67.97 | 0.0532 | 0.13 | Tolak | 260.07 | 260.07 |
| 11 | 19.69 | (3,5) | 70.12 | 0.0284 | 0.99 | Tolak | 260.07 | 260.07 |
| 12 | 16.73 | (2,5) | 5.14 | 0.7354 | 0.99 | Tolak | 260.07 | 260.07 |
| 13 | 14.22 | (4,5) | 137.41 | 0.0001 | 0.73 | Tolak | 260.07 | 260.07 |
| 14 | 12.09 | (3,5) | 70.12 | 0.0030 | 0.36 | Tolak | 260.07 | 260.07 |
| 15 | 10.28 | (2,4) | -2.07 | - | - | Terima | 257.99 | 257.99 |

### Detail per iterasi

### Iterasi 1 (T = 100.00)

- Tour: `Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya` (jarak 264.12)
- Move (i,j) = (1,3): hapus Surabaya-Sidoarjo & Mojokerto-Malang, tambah Surabaya-Mojokerto & Sidoarjo-Malang
- Δ = 68.01 + 76.16 − 25.00 − 35.36 = **83.81**
- Keputusan: u=0.83 ≥ p=0.4325 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya` (jarak **264.12**), terbaik sejauh ini **264.12**

### Iterasi 2 (T = 85.00)

- Tour: `Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya` (jarak 264.12)
- Move (i,j) = (3,5): hapus Gresik-Mojokerto & Blitar-Surabaya, tambah Gresik-Blitar & Mojokerto-Surabaya
- Δ = 96.77 + 68.01 − 38.33 − 125.30 = **1.15**
- Keputusan: u=0.60 < p=0.9866 → terima (uphill)
- Tour sekarang: `Surabaya → Sidoarjo → Gresik → Blitar → Malang → Mojokerto → Surabaya` (jarak **265.26**), terbaik sejauh ini **264.12**

### Iterasi 3 (T = 72.25)

- Tour: `Surabaya → Sidoarjo → Gresik → Blitar → Malang → Mojokerto → Surabaya` (jarak 265.26)
- Move (i,j) = (2,5): hapus Sidoarjo-Gresik & Mojokerto-Surabaya, tambah Sidoarjo-Mojokerto & Gresik-Surabaya
- Δ = 43.01 + 34.99 − 15.13 − 68.01 = **-5.14**
- Keputusan: Δ<0 → terima
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Malang → Blitar → Gresik → Surabaya` (jarak **260.12**), terbaik sejauh ini **260.12**

### Iterasi 4 (T = 61.41)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Malang → Blitar → Gresik → Surabaya` (jarak 260.12)
- Move (i,j) = (3,4): hapus Mojokerto-Malang & Blitar-Gresik, tambah Mojokerto-Blitar & Malang-Gresik
- Δ = 58.52 + 73.55 − 35.36 − 96.77 = **-0.05**
- Keputusan: Δ<0 → terima
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 5 (T = 52.20)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (3,4): hapus Mojokerto-Blitar & Malang-Gresik, tambah Mojokerto-Malang & Blitar-Gresik
- Δ = 35.36 + 96.77 − 58.52 − 73.55 = **0.05**
- Keputusan: u=0.90 < p=0.9990 → terima (uphill)
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Malang → Blitar → Gresik → Surabaya` (jarak **260.12**), terbaik sejauh ini **260.07**

### Iterasi 6 (T = 44.37)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Malang → Blitar → Gresik → Surabaya` (jarak 260.12)
- Move (i,j) = (1,3): hapus Surabaya-Sidoarjo & Malang-Blitar, tambah Surabaya-Malang & Sidoarjo-Blitar
- Δ = 100.62 + 100.62 − 25.00 − 25.00 = **151.25**
- Keputusan: u=0.46 ≥ p=0.0331 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Malang → Blitar → Gresik → Surabaya` (jarak **260.12**), terbaik sejauh ini **260.07**

### Iterasi 7 (T = 37.71)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Malang → Blitar → Gresik → Surabaya` (jarak 260.12)
- Move (i,j) = (3,4): hapus Mojokerto-Malang & Blitar-Gresik, tambah Mojokerto-Blitar & Malang-Gresik
- Δ = 58.52 + 73.55 − 35.36 − 96.77 = **-0.05**
- Keputusan: Δ<0 → terima
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 8 (T = 32.06)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (2,5): hapus Sidoarjo-Mojokerto & Gresik-Surabaya, tambah Sidoarjo-Gresik & Mojokerto-Surabaya
- Δ = 15.13 + 68.01 − 43.01 − 34.99 = **5.14**
- Keputusan: u=0.56 < p=0.8518 → terima (uphill)
- Tour sekarang: `Surabaya → Sidoarjo → Gresik → Malang → Blitar → Mojokerto → Surabaya` (jarak **265.21**), terbaik sejauh ini **260.07**

### Iterasi 9 (T = 27.25)

- Tour: `Surabaya → Sidoarjo → Gresik → Malang → Blitar → Mojokerto → Surabaya` (jarak 265.21)
- Move (i,j) = (2,5): hapus Sidoarjo-Gresik & Mojokerto-Surabaya, tambah Sidoarjo-Mojokerto & Gresik-Surabaya
- Δ = 43.01 + 34.99 − 15.13 − 68.01 = **-5.14**
- Keputusan: Δ<0 → terima
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 10 (T = 23.16)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (2,3): hapus Sidoarjo-Mojokerto & Blitar-Malang, tambah Sidoarjo-Blitar & Mojokerto-Malang
- Δ = 100.62 + 35.36 − 43.01 − 25.00 = **67.97**
- Keputusan: u=0.13 ≥ p=0.0532 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 11 (T = 19.69)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (3,5): hapus Mojokerto-Blitar & Gresik-Surabaya, tambah Mojokerto-Gresik & Blitar-Surabaya
- Δ = 38.33 + 125.30 − 58.52 − 34.99 = **70.12**
- Keputusan: u=0.99 ≥ p=0.0284 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 12 (T = 16.73)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (2,5): hapus Sidoarjo-Mojokerto & Gresik-Surabaya, tambah Sidoarjo-Gresik & Mojokerto-Surabaya
- Δ = 15.13 + 68.01 − 43.01 − 34.99 = **5.14**
- Keputusan: u=0.99 ≥ p=0.7354 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 13 (T = 14.22)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (4,5): hapus Blitar-Malang & Gresik-Surabaya, tambah Blitar-Gresik & Malang-Surabaya
- Δ = 96.77 + 100.62 − 25.00 − 34.99 = **137.41**
- Keputusan: u=0.73 ≥ p=0.0001 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 14 (T = 12.09)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (3,5): hapus Mojokerto-Blitar & Gresik-Surabaya, tambah Mojokerto-Gresik & Blitar-Surabaya
- Δ = 38.33 + 125.30 − 58.52 − 34.99 = **70.12**
- Keputusan: u=0.36 ≥ p=0.0030 → tolak
- Tour sekarang: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak **260.07**), terbaik sejauh ini **260.07**

### Iterasi 15 (T = 10.28)

- Tour: `Surabaya → Sidoarjo → Mojokerto → Blitar → Malang → Gresik → Surabaya` (jarak 260.07)
- Move (i,j) = (2,4): hapus Sidoarjo-Mojokerto & Malang-Gresik, tambah Sidoarjo-Malang & Mojokerto-Gresik
- Δ = 76.16 + 38.33 − 43.01 − 73.55 = **-2.07**
- Keputusan: Δ<0 → terima
- Tour sekarang: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya` (jarak **257.99**), terbaik sejauh ini **257.99**

## 7. Hasil Akhir

- Rute terbaik: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya`
- Total jarak terbaik: **257.99**
- Peningkatan dari solusi awal: 264.12 → 257.99 (hemat 6.12, 2.32%)

Catatan: SA bersifat stokastik, sehingga hasil bergantung pada bilangan acak. Dengan seed lain hasil bisa berbeda. Untuk 6 kota, nilai 257.99 sama dengan optimum global hasil brute force.
