# Perhitungan Manual 2-Opt (TSP)

Dokumen ini menunjukkan perhitungan manual algoritma **2-Opt** pada dataset `City.csv` (6 kota). Semua angka dibulatkan 2 desimal (selisih 0.01 pada penjumlahan bisa muncul karena pembulatan).

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

Contoh: Sidoarjo→Gresik = $\sqrt{(18-20)^2+(30-15)^2}=\sqrt{229}=15.13$

| | Surabaya | Sidoarjo | Gresik | Mojokerto | Malang | Blitar |
|---|---|---|---|---|---|---|
| **Surabaya** | 0.00 | 25.00 | 34.99 | 68.01 | 100.62 | 125.30 |
| **Sidoarjo** | 25.00 | 0.00 | 15.13 | 43.01 | 76.16 | 100.62 |
| **Gresik** | 34.99 | 15.13 | 0.00 | 38.33 | 73.55 | 96.77 |
| **Mojokerto** | 68.01 | 43.01 | 38.33 | 0.00 | 35.36 | 58.52 |
| **Malang** | 100.62 | 76.16 | 73.55 | 35.36 | 0.00 | 25.00 |
| **Blitar** | 125.30 | 100.62 | 96.77 | 58.52 | 25.00 | 0.00 |

## 3. Solusi Awal

Urutan sesuai data (kembali ke kota awal):

`Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya`

Total jarak = 25.00 + 15.13 + 38.33 + 35.36 + 25.00 + 125.30 = **264.12**

## 4. Prinsip 2-Opt

Pilih dua edge `(a,b)` dan `(c,e)`, lalu hapus keduanya dan sambung ulang menjadi `(a,c)` dan `(b,e)` (segmen di antara `b..c` dibalik).

$$\Delta = d(a,c)+d(b,e)-d(a,b)-d(c,e)$$

Jika $\Delta<0$ maka tour lebih pendek → move diterima. Strategi: **best improvement** (ambil $\Delta$ paling negatif tiap iterasi). Posisi `i=0` (Surabaya) dijaga tetap sebagai titik awal.

## 5.1 Iterasi 1

Tour saat ini: `Surabaya → Sidoarjo → Gresik → Mojokerto → Malang → Blitar → Surabaya` (jarak **264.12**)

| Move (i,j) | Edge dihapus | Edge baru | Δ | Keputusan |
|---|---|---|---|---|
| (1,2) | Surabaya-Sidoarjo, Gresik-Mojokerto | Surabaya-Gresik, Sidoarjo-Mojokerto | 34.99+43.01−25.00−38.33 = **14.67** | tolak |
| (1,3) | Surabaya-Sidoarjo, Mojokerto-Malang | Surabaya-Mojokerto, Sidoarjo-Malang | 68.01+76.16−25.00−35.36 = **83.81** | tolak |
| (1,4) | Surabaya-Sidoarjo, Malang-Blitar | Surabaya-Malang, Sidoarjo-Blitar | 100.62+100.62−25.00−25.00 = **151.25** | tolak |
| (2,3) | Sidoarjo-Gresik, Mojokerto-Malang | Sidoarjo-Mojokerto, Gresik-Malang | 43.01+73.55−15.13−35.36 = **66.07** | tolak |
| (2,4) | Sidoarjo-Gresik, Malang-Blitar | Sidoarjo-Malang, Gresik-Blitar | 76.16+96.77−15.13−25.00 = **132.79** | tolak |
| (2,5) | Sidoarjo-Gresik, Blitar-Surabaya | Sidoarjo-Blitar, Gresik-Surabaya | 100.62+34.99−15.13−125.30 = **-4.82** | ✅ terbaik |
| (3,4) | Gresik-Mojokerto, Malang-Blitar | Gresik-Malang, Mojokerto-Blitar | 73.55+58.52−38.33−25.00 = **68.74** | tolak |
| (3,5) | Gresik-Mojokerto, Blitar-Surabaya | Gresik-Blitar, Mojokerto-Surabaya | 96.77+68.01−38.33−125.30 = **1.15** | tolak |
| (4,5) | Mojokerto-Malang, Blitar-Surabaya | Mojokerto-Blitar, Malang-Surabaya | 58.52+100.62−35.36−125.30 = **-1.51** | improve |

Move terbaik **(2,5)** dengan Δ = -4.82. Balik segmen posisi 2..5.

Tour baru: `Surabaya → Sidoarjo → Blitar → Malang → Mojokerto → Gresik → Surabaya`

Jarak baru = jarak lama + Δ = **259.29**

## 5.2 Iterasi 2

Tour saat ini: `Surabaya → Sidoarjo → Blitar → Malang → Mojokerto → Gresik → Surabaya` (jarak **259.29**)

| Move (i,j) | Edge dihapus | Edge baru | Δ | Keputusan |
|---|---|---|---|---|
| (1,2) | Surabaya-Sidoarjo, Blitar-Malang | Surabaya-Blitar, Sidoarjo-Malang | 125.30+76.16−25.00−25.00 = **151.46** | tolak |
| (1,3) | Surabaya-Sidoarjo, Malang-Mojokerto | Surabaya-Malang, Sidoarjo-Mojokerto | 100.62+43.01−25.00−35.36 = **83.28** | tolak |
| (1,4) | Surabaya-Sidoarjo, Mojokerto-Gresik | Surabaya-Mojokerto, Sidoarjo-Gresik | 68.01+15.13−25.00−38.33 = **19.81** | tolak |
| (2,3) | Sidoarjo-Blitar, Malang-Mojokerto | Sidoarjo-Malang, Blitar-Mojokerto | 76.16+58.52−100.62−35.36 = **-1.30** | ✅ terbaik |
| (2,4) | Sidoarjo-Blitar, Mojokerto-Gresik | Sidoarjo-Mojokerto, Blitar-Gresik | 43.01+96.77−100.62−38.33 = **0.83** | tolak |
| (2,5) | Sidoarjo-Blitar, Gresik-Surabaya | Sidoarjo-Gresik, Blitar-Surabaya | 15.13+125.30−100.62−34.99 = **4.82** | tolak |
| (3,4) | Blitar-Malang, Mojokerto-Gresik | Blitar-Mojokerto, Malang-Gresik | 58.52+73.55−25.00−38.33 = **68.74** | tolak |
| (3,5) | Blitar-Malang, Gresik-Surabaya | Blitar-Gresik, Malang-Surabaya | 96.77+100.62−25.00−34.99 = **137.41** | tolak |
| (4,5) | Malang-Mojokerto, Gresik-Surabaya | Malang-Gresik, Mojokerto-Surabaya | 73.55+68.01−35.36−34.99 = **71.21** | tolak |

Move terbaik **(2,3)** dengan Δ = -1.30. Balik segmen posisi 2..3.

Tour baru: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya`

Jarak baru = jarak lama + Δ = **257.99**

## 5.3 Iterasi 3

Tour saat ini: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya` (jarak **257.99**)

| Move (i,j) | Edge dihapus | Edge baru | Δ | Keputusan |
|---|---|---|---|---|
| (1,2) | Surabaya-Sidoarjo, Malang-Blitar | Surabaya-Malang, Sidoarjo-Blitar | 100.62+100.62−25.00−25.00 = **151.25** | tolak |
| (1,3) | Surabaya-Sidoarjo, Blitar-Mojokerto | Surabaya-Blitar, Sidoarjo-Mojokerto | 125.30+43.01−25.00−58.52 = **84.79** | tolak |
| (1,4) | Surabaya-Sidoarjo, Mojokerto-Gresik | Surabaya-Mojokerto, Sidoarjo-Gresik | 68.01+15.13−25.00−38.33 = **19.81** | tolak |
| (2,3) | Sidoarjo-Malang, Blitar-Mojokerto | Sidoarjo-Blitar, Malang-Mojokerto | 100.62+35.36−76.16−58.52 = **1.30** | tolak |
| (2,4) | Sidoarjo-Malang, Mojokerto-Gresik | Sidoarjo-Mojokerto, Malang-Gresik | 43.01+73.55−76.16−38.33 = **2.07** | tolak |
| (2,5) | Sidoarjo-Malang, Gresik-Surabaya | Sidoarjo-Gresik, Malang-Surabaya | 15.13+100.62−76.16−34.99 = **4.61** | tolak |
| (3,4) | Malang-Blitar, Mojokerto-Gresik | Malang-Mojokerto, Blitar-Gresik | 35.36+96.77−25.00−38.33 = **68.80** | tolak |
| (3,5) | Malang-Blitar, Gresik-Surabaya | Malang-Gresik, Blitar-Surabaya | 73.55+125.30−25.00−34.99 = **138.86** | tolak |
| (4,5) | Blitar-Mojokerto, Gresik-Surabaya | Blitar-Gresik, Mojokerto-Surabaya | 96.77+68.01−58.52−34.99 = **71.27** | tolak |

Tidak ada move dengan Δ < 0 → **konvergen (local optimum)**.

## 6. Hasil Akhir

- Rute: `Surabaya → Sidoarjo → Malang → Blitar → Mojokerto → Gresik → Surabaya`
- Total jarak: **257.99**
- Peningkatan dari solusi awal: 264.12 → 257.99 (hemat 6.12, 2.32%)

Untuk 6 kota, hasil ini sudah dicek dengan brute force (5! = 120 kemungkinan rute) dan merupakan **solusi optimal global**.
