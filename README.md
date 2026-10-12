
# TSP Optimizer
### Implementasi Algoritma Simulated Annealing dan Tabu Search dengan Heuristik Konstruktif dan 2-Opt Local Search

**Proyek Mata Kuliah Metode Optimasi Metaheuristik — Kelompok ...**

---

## 1. Deskripsi Proyek

**TSP Optimizer** merupakan aplikasi desktop berbasis Python untuk menyelesaikan permasalahan *Traveling Salesman Problem* (TSP), yaitu pencarian rute perjalanan dengan total jarak minimum. Aplikasi ini memungkinkan pengguna menentukan urutan kunjungan sejumlah kota melalui proses pembentukan solusi awal, optimasi rute, dan visualisasi hasil perhitungan.

Aplikasi menggunakan tiga metode pembentukan solusi awal, yaitu **Nearest Neighbor (NN)**, **Farthest Insertion**, dan **Random**. Proses optimasi dilakukan menggunakan **Simulated Annealing (SA)** atau **Tabu Search (TS)**, dengan **2-Opt Local Search** sebagai tahap perbaikan tambahan yang bersifat opsional. Aplikasi dikembangkan menggunakan **Python** dan **CustomTkinter**, serta mendukung input dataset CSV/Excel, pengaturan parameter algoritma, visualisasi rute, grafik konvergensi, dan ekspor hasil optimasi.

---

## 2. Anggota Kelompok

| No. | Nama Anggota | NIM | Pembagian Tugas |
|:---:|--------------|-----|-----------------|
| 1 | Violita Karina Putri | 5052241009 | [Tugas] |
| 2 | George Eldzen Edison | 5052241024 | [Tugas] |
| 3 | Azizah Adilah | 5052241028 | [Tugas] |
| 4 | Aqila Ikhza Kusumawardani | 5052241032 | [Tugas] |
| 5 | Najwa Aulia | 5052241035 | [Tugas] |

---

## 3. Latar Belakang & Case Study

### 3.1 Latar Belakang

Penentuan rute perjalanan yang efisien menjadi salah satu permasalahan penting dalam bidang transportasi dan logistik. Semakin banyak lokasi yang harus dikunjungi, semakin besar pula kemungkinan urutan perjalanan yang dapat dipilih. Permasalahan ini dikenal sebagai *Traveling Salesman Problem* (TSP), yaitu pencarian rute dengan total jarak minimum, di mana setiap lokasi dikunjungi tepat satu kali sebelum kembali ke titik awal.

Untuk menyelesaikan permasalahan tersebut, proyek ini menerapkan pendekatan heuristik konstruktif dalam membentuk solusi awal serta algoritma metaheuristik untuk memperbaiki kualitas rute. Kombinasi metode ini memungkinkan pencarian solusi yang efisien tanpa harus mengevaluasi seluruh kemungkinan rute secara langsung.

### 3.2 Studi Kasus dan Dataset

Studi kasus menggunakan simulasi perjalanan ke enam kota di Jawa Timur, yaitu **Surabaya, Sidoarjo, Gresik, Mojokerto, Malang, dan Blitar**. Perjalanan dimulai dari Surabaya sebagai titik awal (*depot*), mengunjungi seluruh kota lainnya tepat satu kali, kemudian kembali ke Surabaya.

Dataset yang digunakan berasal dari file [`data/City.csv`](data/City.csv) dalam repository proyek. Data tersebut merupakan koordinat contoh dua dimensi untuk pengujian algoritma, bukan koordinat geografis atau jarak jalan sebenarnya.

| No. | Kota | X | Y |
|:---:|------|---:|---:|
| 1 | Surabaya | 0 | 0 |
| 2 | Sidoarjo | 20 | 15 |
| 3 | Gresik | 18 | 30 |
| 4 | Mojokerto | 55 | 40 |
| 5 | Malang | 90 | 45 |
| 6 | Blitar | 110 | 60 |

### 3.3 Perhitungan Jarak Antarkota

Jarak antarkota dihitung menggunakan **Euclidean Distance**, yaitu jarak garis lurus antara dua titik koordinat.

Rumus:

$$
d(i,j)=\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}
$$

Keterangan:
- \(d(i,j)\): jarak antara kota i dan kota j.
- \(x_i,y_i\): koordinat kota i.
- \(x_j,y_j\): koordinat kota j.

**Contoh:** Jarak Surabaya (0,0) ke Sidoarjo (20,15).

$$
d=\sqrt{(20-0)^2+(15-0)^2}
=\sqrt{625}=25
$$

Hasil perhitungan jarak setiap pasangan kota digunakan untuk membentuk matriks jarak yang menjadi dasar proses optimasi rute.

---
