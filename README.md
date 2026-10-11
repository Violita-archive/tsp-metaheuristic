# Perhitungan Manual SA, 2-Opt, dan Tabu Search pada TSP

Laporan ini menunjukkan perhitungan **manual (langkah demi langkah)** tiga metode optimasi pada kasus **Traveling Salesman Problem (TSP)** dengan 5 kota:

1. **2-Opt** (local search)
2. **Tabu Search**
3. **Simulated Annealing (SA)**

> Data pada laporan ini adalah contoh. Ganti matriks jarak dengan data tugasmu, lalu ikuti alur yang sama.

---

## 1. Data Kasus

Kota: **A, B, C, D, E** (simetris, mulai dan berakhir di **A**).

| Jarak | A  | B  | C  | D  | E  |
|:-----:|:--:|:--:|:--:|:--:|:--:|
| **A** | –  | 12 | 29 | 22 | 13 |
| **B** | 12 | –  | 19 | 3  | 25 |
| **C** | 29 | 19 | –  | 21 | 23 |
| **D** | 22 | 3  | 21 | –  | 8  |
| **E** | 13 | 25 | 23 | 8  | –  |

**Solusi awal:** `A → B → C → D → E → A`

```
Cost = AB + BC + CD + DE + EA
     = 12 + 19 + 21 + 8 + 13 = 73
```

**Representasi:** tour `[A, B, C, D, E]` dengan indeks posisi 0–4. Kota A (indeks 0) dikunci, jadi hanya indeks 1–4 yang boleh diubah.

**Neighborhood (2-opt move):** pilih dua posisi `(i, j)` dengan `1 ≤ i < j ≤ 4`, lalu **balik urutan** kota dari posisi `i` sampai `j`. Ada C(4,2) = **6 tetangga** per iterasi.

Contoh: tour `A B C D E`, move `(1,2)` membalik segmen `B C` menjadi `C B`, hasilnya `A C B D E`.

---

## 2. Metode 2-Opt (Best Improvement)

**Aturan:** pada tiap iterasi evaluasi seluruh 6 tetangga, ambil yang cost-nya paling kecil. Jika lebih baik dari solusi sekarang, pindah. Jika tidak ada, **berhenti** (optimum lokal).

### Iterasi 1: tour `A B C D E` (cost 73)

| Move (i,j) | Tetangga     | Cost | Δ vs 73 |
|:----------:|:------------:|:----:|:-------:|
| (1,2)      | A C B D E    | 72   | **-1**  |
| (1,3)      | A D C B E    | 100  | +27     |
| (1,4)      | A E D C B    | 73   | 0       |
| (2,3)      | A B D C E    | 72   | **-1**  |
| (2,4)      | A B E D C    | 95   | +22     |
| (3,4)      | A B C E D    | 84   | +11     |

Terbaik: cost 72 (ada seri antara (1,2) dan (2,3)). Dipilih **(1,2)**, sehingga tour baru `A C B D E` (cost **72**).

Verifikasi: `AC + CB + BD + DE + EA = 29 + 19 + 3 + 8 + 13 = 72` ✓

### Iterasi 2: tour `A C B D E` (cost 72)

| Move (i,j) | Tetangga     | Cost | Δ vs 72 |
|:----------:|:------------:|:----:|:-------:|
| (1,2)      | A B C D E    | 73   | +1      |
| (1,3)      | A D B C E    | 80   | +8      |
| (1,4)      | A E D B C    | 72   | 0       |
| (2,3)      | A C D B E    | 91   | +19     |
| (2,4)      | A C E D B    | 75   | +3      |
| (3,4)      | A C B E D    | 103  | +31     |

Tidak ada tetangga dengan cost < 72 → **berhenti**.

**Hasil 2-Opt:** `A → C → B → D → E → A`, cost = **72**.

---

## 3. Metode Tabu Search

**Parameter:**

- Tabu tenure = **2** iterasi
- Atribut tabu = pasangan kota yang dibalik (mis. `(B,C)`)
- Aspiration: move tabu tetap boleh jika cost-nya **lebih baik dari best global**
- Iterasi maksimum = 5
- Pada tiap iterasi, pilih tetangga **terbaik yang tidak tabu**, **walaupun lebih buruk dari solusi sekarang**

### Iterasi 1: tour `A B C D E` (cost 73), tabu list: ∅

| Move | Pasangan | Tetangga  | Cost | Status |
|:----:|:--------:|:---------:|:----:|:------:|
| (1,2)| (B,C)    | A C B D E | 72   | **terbaik** |
| (1,3)| (B,D)    | A D C B E | 100  |        |
| (1,4)| (B,E)    | A E D C B | 73   |        |
| (2,3)| (C,D)    | A B D C E | 72   | seri   |
| (2,4)| (C,E)    | A B E D C | 95   |        |
| (3,4)| (D,E)    | A B C E D | 84   |        |

Pilih (1,2) → `A C B D E` (72). Tabu list: `{(B,C):2}`. Best global = **72**.

### Iterasi 2: tour `A C B D E` (72), tabu list: `{(B,C):2}`

| Move | Pasangan | Tetangga  | Cost | Status |
|:----:|:--------:|:---------:|:----:|:------:|
| (1,2)| (B,C)    | A B C D E | 73   | **TABU** (73 tidak < 72, aspiration gagal) |
| (1,3)| (C,D)    | A D B C E | 80   |        |
| (1,4)| (C,E)    | A E D B C | 72   | **terbaik** |
| (2,3)| (B,D)    | A C D B E | 91   |        |
| (2,4)| (B,E)    | A C E D B | 75   |        |
| (3,4)| (D,E)    | A C B E D | 103  |        |

Pilih (1,4) → `A E D B C` (72). Tabu list: `{(B,C):1, (C,E):2}`.

### Iterasi 3: tour `A E D B C` (72), tabu list: `{(B,C):1, (C,E):2}`

| Move | Pasangan | Tetangga  | Cost | Status |
|:----:|:--------:|:---------:|:----:|:------:|
| (1,2)| (D,E)    | A D E B C | 103  |        |
| (1,3)| (B,E)    | A B D E C | 75   | **terbaik** (non-tabu) |
| (1,4)| (C,E)    | A C B D E | 72   | **TABU** (72 tidak < 72) |
| (2,3)| (B,D)    | A E B D C | 91   |        |
| (2,4)| (C,D)    | A E C B D | 80   |        |
| (3,4)| (B,C)    | A E D C B | 73   | **TABU** |

Pilih (1,3) → `A B D E C` (**75**, lebih buruk). Ini ciri khas Tabu: boleh turun demi keluar dari optimum lokal. Tabu list: `{(C,E):1, (B,E):2}`.

### Iterasi 4: tour `A B D E C` (75), tabu list: `{(C,E):1, (B,E):2}`

| Move | Pasangan | Tetangga  | Cost | Status |
|:----:|:--------:|:---------:|:----:|:------:|
| (1,2)| (B,D)    | A D B E C | 102  |        |
| (1,3)| (B,E)    | A E D B C | 72   | **TABU** (72 tidak < 72) |
| (1,4)| (B,C)    | A C E D B | 75   | **terbaik** (non-tabu) |
| (2,3)| (D,E)    | A B E D C | 95   |        |
| (2,4)| (C,D)    | A B C E D | 84   |        |
| (3,4)| (C,E)    | A B D C E | 72   | **TABU** |

Pilih (1,4) → `A C E D B` (75). Tabu list: `{(B,E):1, (B,C):2}`.

### Iterasi 5: tour `A C E D B` (75), tabu list: `{(B,E):1, (B,C):2}`

| Move | Pasangan | Tetangga  | Cost | Status |
|:----:|:--------:|:---------:|:----:|:------:|
| (1,2)| (C,E)    | A E C D B | 72   | **terbaik** |
| (1,3)| (C,D)    | A D E C B | 84   |        |
| (1,4)| (B,C)    | A B D E C | 75   | **TABU** |
| (2,3)| (D,E)    | A C D E B | 95   |        |
| (2,4)| (B,E)    | A C B D E | 72   | **TABU** (72 tidak < 72) |
| (3,4)| (B,D)    | A C E B D | 102  |        |

Pilih (1,2) → `A E C D B` (72).

### Ringkasan Tabu Search

| Iter | Move (pasangan) | Tour hasil | Cost | Best global |
|:----:|:---------------:|:----------:|:----:|:-----------:|
| 0    | –               | A B C D E  | 73   | 73          |
| 1    | (B,C)           | A C B D E  | 72   | 72          |
| 2    | (C,E)           | A E D B C  | 72   | 72          |
| 3    | (B,E)           | A B D E C  | 75   | 72          |
| 4    | (B,C)           | A C E D B  | 75   | 72          |
| 5    | (C,E)           | A E C D B  | 72   | 72          |

**Hasil Tabu Search:** best = `A → C → B → D → E → A`, cost = **72**.

---

## 4. Metode Simulated Annealing (SA)

**Parameter:**

- Suhu awal `T₀ = 20`
- Cooling geometrik: `T(k+1) = α · T(k)`, dengan `α = 0.8`
- Kriteria penerimaan:
  - Jika `Δ = cost(baru) − cost(sekarang) ≤ 0` → **diterima**
  - Jika `Δ > 0` → diterima dengan peluang `P = exp(−Δ / T)`. Bangkitkan bilangan acak `u ∈ [0,1)`; **terima jika `u < P`**
- Pada tiap iterasi hanya **satu** tetangga acak yang dievaluasi
- Move acak `(i,j)` dan nilai `u` ditetapkan di bawah agar perhitungan dapat direproduksi (untuk laporan)

Solusi awal: `A B C D E` (cost 73).

| Iter | T     | Tour sekarang (cost) | Move | Kandidat (cost) | Δ   | P = e^(−Δ/T)  | u    | Keputusan |
|:----:|:-----:|:--------------------:|:----:|:---------------:|:---:|:-------------:|:----:|:---------:|
| 1    | 20.00 | A B C D E (73)       | (2,4)| A B E D C (95)  | +22 | e^(−22/20)=0.3329 | 0.25 | **Terima** (u < P) |
| 2    | 16.00 | A B E D C (95)       | (1,3)| A D E B C (103) | +8  | e^(−8/16)=0.6065  | 0.90 | **Tolak** (u ≥ P) |
| 3    | 12.80 | A B E D C (95)       | (3,4)| A B E C D (103) | +8  | e^(−8/12.8)=0.5353| 0.40 | **Terima** (u < P) |
| 4    | 10.24 | A B E C D (103)      | (2,3)| A B C E D (84)  | −19 | 1 (Δ<0)       | 0.10 | **Terima** (lebih baik) |
| 5    | 8.19  | A B C E D (84)       | (1,2)| A C B E D (103) | +19 | e^(−19/8.19)=0.0983 | 0.60 | **Tolak** (u ≥ P) |
| 6    | 6.55  | A B C E D (84)       | (1,4)| A D E C B (84)  | 0   | 1 (Δ=0)       | 0.30 | **Terima** |

**Contoh hitung Iterasi 1:**

```
Δ = 95 − 73 = 22
P = exp(−22/20) = exp(−1.1) = 0.3329
u = 0.25 < 0.3329  →  solusi lebih buruk tetap DITERIMA
T berikutnya = 20 × 0.8 = 16
```

**Hasil SA (6 iterasi):** solusi akhir `A D E C B` (cost 84, setara tour `A B C E D` yang dibalik). Solusi terbaik yang pernah dikunjungi adalah solusi awal (cost **73**).

> Catatan: SA bersifat stokastik. Dengan hanya 6 iterasi dan satu tetangga per iterasi, hasilnya belum tentu mencapai optimum. Pada implementasi nyata, jumlah iterasi jauh lebih banyak dan suhu diturunkan sampai mendekati nol.

---

## 5. Perbandingan Hasil

| Metode          | Tour terbaik        | Cost | Jumlah iterasi | Keterangan |
|:---------------:|:-------------------:|:----:|:--------------:|:----------:|
| Solusi awal     | A B C D E A         | 73   | –              | – |
| **2-Opt**       | A C B D E A         | 72   | 2              | Berhenti di optimum lokal |
| **Tabu Search** | A C B D E A         | 72   | 5              | Lolos dari optimum lokal lewat tabu list, tetap 72 |
| **SA**          | A B C D E A         | 73   | 6              | Belum membaik (contoh ilustrasi) |

Dengan 5 kota, seluruh 4! = 24 permutasi dapat dicek: cost optimum global = **72** (mis. `A B D C E A` dan `A C B D E A`). Jadi 2-Opt dan Tabu Search sudah mencapai optimum pada contoh ini.

---

## 6. Kesimpulan

- **2-Opt** cepat dan sederhana, tetapi hanya menerima perbaikan sehingga mudah terjebak di optimum lokal.
- **Tabu Search** memakai memori (tabu list) untuk melarang move berulang, sehingga boleh menerima solusi lebih buruk (iterasi 3 dan 4) dan menjelajah lebih luas.
- **Simulated Annealing** menerima solusi lebih buruk secara probabilistik (`e^(−Δ/T)`); semakin kecil suhu, semakin selektif. Hasilnya bergantung pada bilangan acak dan jadwal pendinginan.

---

## 7. Struktur Repo (saran)

```
.
├── README.md        # laporan ini
├── data/            # matriks jarak
└── src/             # (opsional) kode Python untuk verifikasi
```
