# TSP Optimizer
### **Proyek Mata Kuliah Metode Optimasi Metaheuristik — Kelompok ...**

---

## 1. Deskripsi Proyek

**TSP Optimizer** merupakan aplikasi desktop berbasis Python yang dikembangkan untuk menyelesaikan permasalahan *Traveling Salesman Problem* (TSP), yaitu pencarian rute perjalanan dengan total jarak minimum. Aplikasi ini dirancang sebagai sarana implementasi dan pengujian algoritma optimasi untuk menentukan urutan kunjungan sejumlah kota secara efisien. Setiap kota direpresentasikan menggunakan data koordinat yang kemudian diolah untuk menghitung jarak antarkota. Melalui aplikasi ini, pengguna dapat melakukan proses pembentukan rute awal, optimasi perjalanan, serta melihat hasil perhitungan dalam satu antarmuka.

Dalam proses optimasi, TSP Optimizer menggunakan tiga metode pembentukan solusi awal, yaitu **Nearest Neighbor (NN)**, **Farthest Insertion**, dan **Random**. Ketiga metode tersebut digunakan untuk menghasilkan rute awal berdasarkan pendekatan yang berbeda. Selanjutnya, proses pencarian solusi dilakukan menggunakan algoritma metaheuristik **Simulated Annealing (SA)** atau **Tabu Search (TS)**. Aplikasi juga menyediakan metode **2-Opt Local Search** sebagai tahap perbaikan tambahan untuk mengurangi total jarak perjalanan setelah proses optimasi metaheuristik selesai.

Aplikasi ini dibangun menggunakan bahasa pemrograman **Python** dengan antarmuka grafis berbasis **CustomTkinter**. Pengguna dapat mengunggah dataset dalam format CSV atau Excel, memilih metode pembentukan solusi awal, menentukan algoritma metaheuristik, serta menyesuaikan parameter optimasi. Hasil perhitungan ditampilkan dalam bentuk informasi jarak awal dan akhir, visualisasi rute perjalanan, grafik konvergensi, serta rincian urutan kunjungan kota. Selain itu, tersedia fitur ekspor hasil ke format CSV atau Excel untuk mendukung dokumentasi dan analisis pengujian.

Pengembangan TSP Optimizer bertujuan untuk menerapkan konsep algoritma heuristik, metaheuristik, dan pencarian lokal dalam penyelesaian masalah optimasi rute. Melalui kombinasi metode yang tersedia, pengguna dapat mengamati pengaruh pembentukan solusi awal dan strategi pencarian terhadap kualitas rute yang dihasilkan. Aplikasi ini juga memungkinkan perbandingan hasil optimasi berdasarkan total jarak perjalanan dan persentase perbaikan solusi. Dengan demikian, TSP Optimizer dapat digunakan sebagai media pembelajaran sekaligus alat eksperimen sederhana dalam memahami penerapan algoritma optimasi pada permasalahan Traveling Salesman Problem.


## 2. Anggota Kelompok

Proyek **TSP Optimizer** dikembangkan secara berkelompok sebagai bagian dari tugas Mata Kuliah Metaheuristik. Setiap anggota kelompok berkontribusi dalam proses pengembangan aplikasi, implementasi algoritma, penyusunan dokumentasi, serta pengujian untuk memastikan aplikasi dapat berjalan sesuai dengan tujuan yang telah ditentukan.

Berikut merupakan daftar anggota kelompok beserta pembagian tugasnya:

| No. | Nama Anggota | NIM | Pembagian Tugas |
|:---:|--------------|-----|-----------------|
| 1 | Violita Karina Putri | 5052241009 | [Tugas] |
| 2 | George Eldzen Edison | 5052241024 | [Tugas] |
| 3 | Azizah Adilah | 5052241028 | [Tugas] |
| 4 | Aqila Ikhza Kusumawardani | 5052241032 | [Tugas] |
| 5 | Najwa Aulia | 5052241035 | [Tugas] |



## 3. Latar Belakang & Case Study

### 3.1 Latar Belakang

Penentuan rute perjalanan yang efisien merupakan salah satu permasalahan penting dalam bidang transportasi, distribusi, dan logistik. Dalam kegiatan yang melibatkan kunjungan ke beberapa lokasi, urutan perjalanan dapat memengaruhi total jarak yang harus ditempuh. Pemilihan rute yang kurang tepat berpotensi mengakibatkan perjalanan menjadi lebih panjang dan kurang efisien. Permasalahan tersebut semakin kompleks ketika jumlah lokasi bertambah karena terdapat lebih banyak kemungkinan urutan kunjungan yang perlu dipertimbangkan.

Salah satu model optimasi yang dapat digunakan untuk menyelesaikan permasalahan tersebut adalah *Traveling Salesman Problem* (TSP). TSP bertujuan menentukan rute dengan total jarak minimum, di mana setiap lokasi harus dikunjungi tepat satu kali sebelum perjalanan kembali ke titik awal. Dalam penyelesaiannya, jumlah kemungkinan rute meningkat secara faktorial seiring bertambahnya jumlah lokasi. Oleh karena itu, diperlukan pendekatan komputasional yang mampu menghasilkan solusi berkualitas baik tanpa harus memeriksa seluruh kemungkinan rute secara langsung.

Pendekatan heuristik dan metaheuristik menjadi salah satu alternatif dalam penyelesaian TSP. Metode heuristik konstruktif dapat digunakan untuk membentuk solusi awal, sedangkan algoritma metaheuristik melakukan pencarian lebih lanjut untuk memperoleh solusi yang lebih baik. Penggunaan metode *Nearest Neighbor*, *Farthest Insertion*, dan *Random* memungkinkan pembentukan rute awal melalui strategi yang berbeda. Selanjutnya, algoritma *Simulated Annealing* dan *Tabu Search* digunakan untuk melakukan optimasi, dengan *2-Opt Local Search* sebagai metode perbaikan tambahan.

Berdasarkan permasalahan tersebut, proyek TSP Optimizer dikembangkan untuk mengimplementasikan dan membandingkan berbagai pendekatan optimasi rute dalam satu aplikasi desktop. Pengembangan ini berfokus pada proses pembentukan solusi awal, pencarian rute terbaik, serta evaluasi perubahan total jarak setelah optimasi dilakukan. Melalui penerapan algoritma pada dataset koordinat kota, aplikasi dapat digunakan untuk mengamati bagaimana perbedaan metode dan parameter pencarian memengaruhi kualitas solusi yang dihasilkan.

### 3.2 Studi Kasus

Studi kasus dalam proyek ini menggunakan simulasi perjalanan yang melibatkan enam kota di wilayah Jawa Timur, yaitu Surabaya, Sidoarjo, Gresik, Mojokerto, Malang, dan Blitar. Dalam skenario tersebut, seorang pelaku perjalanan diasumsikan berangkat dari Surabaya untuk mengunjungi seluruh kota lainnya tepat satu kali, kemudian kembali ke Surabaya sebagai titik awal perjalanan.

Permasalahan utama dalam studi kasus ini adalah menentukan urutan kunjungan yang menghasilkan total jarak perjalanan paling minimum. Setiap perubahan urutan kota dapat menghasilkan total jarak yang berbeda sehingga diperlukan proses optimasi untuk menemukan rute yang lebih efisien. Penyelesaian dilakukan dengan membentuk rute awal melalui salah satu metode konstruktif, kemudian memperbaikinya menggunakan algoritma metaheuristik dan, apabila diaktifkan, metode 2-Opt.

Studi kasus ini merupakan simulasi optimasi berbasis koordinat dua dimensi. Oleh karena itu, jarak yang digunakan adalah jarak geometris antartitik, bukan jarak aktual melalui jaringan jalan. Hasil optimasi digunakan untuk mengevaluasi kemampuan algoritma dalam meminimalkan total jarak berdasarkan dataset yang tersedia.

### 3.3 Dataset yang Digunakan

Dataset yang digunakan dalam pengujian awal aplikasi adalah `City.csv`, yang tersedia pada direktori `data/` dalam repository proyek. Dataset tersebut memuat enam kota dengan informasi nama kota dan koordinat dua dimensi yang direpresentasikan melalui atribut `x` dan `y`.

Struktur dataset terdiri atas tiga kolom utama:

- `name`: nama kota yang menjadi lokasi kunjungan.
- `x`: koordinat horizontal suatu kota.
- `y`: koordinat vertikal suatu kota.

Berikut merupakan isi dataset yang digunakan dalam proyek:

| No. | Nama Kota | Koordinat X | Koordinat Y |
|:---:|-----------|------------:|------------:|
| 1 | Surabaya | 0 | 0 |
| 2 | Sidoarjo | 20 | 15 |
| 3 | Gresik | 18 | 30 |
| 4 | Mojokerto | 55 | 40 |
| 5 | Malang | 90 | 45 |
| 6 | Blitar | 110 | 60 |

**Sumber dataset:** File `data/City.csv` pada repository TSP Optimizer kelompok.

Dataset yang tersedia merupakan data koordinat contoh untuk simulasi pengujian algoritma. Nilai koordinat tidak dinyatakan sebagai data geografis aktual, sehingga tidak dapat langsung digunakan untuk menggambarkan jarak tempuh sebenarnya antarkota.

Dalam implementasi aplikasi, kota pada baris pertama dataset ditetapkan sebagai titik awal dan akhir perjalanan. Dengan demikian, Surabaya berperan sebagai depot, sedangkan lima kota lainnya menjadi lokasi yang harus dikunjungi.

### 3.4 Perhitungan Jarak Antarkota

Jarak antarkota dalam aplikasi dihitung menggunakan metode *Euclidean Distance*, yaitu pengukuran jarak garis lurus antara dua titik pada bidang dua dimensi. Metode ini digunakan karena dataset merepresentasikan setiap kota melalui pasangan koordinat `x` dan `y`.

Rumus Euclidean Distance adalah:

**d(i,j) = √[(xᵢ − xⱼ)² + (yᵢ − yⱼ)²]**

Keterangan:

- `d(i,j)` = jarak antara kota i dan kota j.
- `xᵢ, yᵢ` = koordinat kota i.
- `xⱼ, yⱼ` = koordinat kota j.

Sebagai contoh, Surabaya memiliki koordinat (0,0), sedangkan Sidoarjo memiliki koordinat (20,15). Berdasarkan rumus Euclidean Distance, jarak antara kedua kota tersebut adalah:

```text
d(Surabaya, Sidoarjo)
= √[(20 - 0)² + (15 - 0)²]
= √(400 + 225)
= √625
= 25 satuan jarak
```

Perhitungan tersebut diterapkan pada setiap pasangan kota untuk membentuk matriks jarak. Matriks ini kemudian digunakan oleh algoritma pembentukan solusi awal dan algoritma optimasi dalam mengevaluasi total jarak setiap rute.

Karena menggunakan jarak Euclidean, matriks jarak yang dihasilkan bersifat simetris, yaitu jarak dari kota A ke kota B sama dengan jarak dari kota B ke kota A.

### 3.5 Tujuan Optimasi pada Studi Kasus

Berdasarkan dataset dan skenario perjalanan yang digunakan, proses optimasi dilakukan untuk mencapai beberapa tujuan berikut:

1. Menentukan urutan kunjungan enam kota dengan total jarak perjalanan seminimal mungkin.
2. Membandingkan kualitas solusi awal yang dihasilkan melalui Nearest Neighbor, Farthest Insertion, dan Random.
3. Mengoptimalkan rute menggunakan algoritma Simulated Annealing atau Tabu Search.
4. Mengevaluasi pengaruh penerapan 2-Opt Local Search terhadap hasil optimasi metaheuristik.
5. Menganalisis perubahan total jarak sebelum dan sesudah optimasi sebagai indikator kualitas solusi.

Melalui studi kasus ini, setiap algoritma dapat diuji menggunakan data yang sama sehingga hasil perhitungan dapat dibandingkan berdasarkan total jarak perjalanan. Perbandingan tersebut menjadi dasar untuk mengevaluasi kinerja metode optimasi yang diimplementasikan dalam aplikasi TSP Optimizer.

