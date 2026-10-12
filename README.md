# TSP Optimizer
### Implementasi Algoritma Heuristik dan Metaheuristik untuk Optimasi Rute Perjalanan

**Proyek Mata Kuliah Metode Optimasi Metaheuristik — Kelompok ...**

---

# tsp-metaheuristic

## 1. Deskripsi Proyek

**TSP Optimizer** merupakan aplikasi desktop berbasis Python yang dikembangkan untuk menyelesaikan permasalahan *Traveling Salesman Problem* (TSP), yaitu pencarian rute perjalanan dengan total jarak minimum. Aplikasi ini dirancang sebagai sarana implementasi dan pengujian algoritma optimasi untuk menentukan urutan kunjungan sejumlah kota secara efisien. Setiap kota direpresentasikan menggunakan data koordinat yang kemudian diolah untuk menghitung jarak antarkota. Melalui aplikasi ini, pengguna dapat melakukan proses pembentukan rute awal, optimasi perjalanan, serta melihat hasil perhitungan dalam satu antarmuka.

Dalam proses optimasi, TSP Optimizer menggunakan tiga metode pembentukan solusi awal, yaitu **Nearest Neighbor (NN)**, **Farthest Insertion**, dan **Random**. Ketiga metode tersebut digunakan untuk menghasilkan rute awal berdasarkan pendekatan yang berbeda. Selanjutnya, proses pencarian solusi dilakukan menggunakan algoritma metaheuristik **Simulated Annealing (SA)** atau **Tabu Search (TS)**. Aplikasi juga menyediakan metode **2-Opt Local Search** sebagai tahap perbaikan tambahan untuk mengurangi total jarak perjalanan setelah proses optimasi metaheuristik selesai.

Aplikasi ini dibangun menggunakan bahasa pemrograman **Python** dengan antarmuka grafis berbasis **CustomTkinter**. Pengguna dapat mengunggah dataset dalam format CSV atau Excel, memilih metode pembentukan solusi awal, menentukan algoritma metaheuristik, serta menyesuaikan parameter optimasi. Hasil perhitungan ditampilkan dalam bentuk informasi jarak awal dan akhir, visualisasi rute perjalanan, grafik konvergensi, serta rincian urutan kunjungan kota. Selain itu, tersedia fitur ekspor hasil ke format CSV atau Excel untuk mendukung dokumentasi dan analisis pengujian.

Pengembangan TSP Optimizer bertujuan untuk menerapkan konsep algoritma heuristik, metaheuristik, dan pencarian lokal dalam penyelesaian masalah optimasi rute. Melalui kombinasi metode yang tersedia, pengguna dapat mengamati pengaruh pembentukan solusi awal dan strategi pencarian terhadap kualitas rute yang dihasilkan. Aplikasi ini juga memungkinkan perbandingan hasil optimasi berdasarkan total jarak perjalanan dan persentase perbaikan solusi. Dengan demikian, TSP Optimizer dapat digunakan sebagai media pembelajaran sekaligus alat eksperimen sederhana dalam memahami penerapan algoritma optimasi pada permasalahan Traveling Salesman Problem.
