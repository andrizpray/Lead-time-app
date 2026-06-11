---
bab: 1
judul: PENDAHULUAN
---

## Latar Belakang

PT Eco Paper Indonesia merupakan perusahaan manufaktur kertas yang memiliki operasional loading barang setiap harinya. Proses loading DO (Delivery Order) melibatkan banyak pihak seperti operator, ekspedisi, dan customer. Setiap truk yang datang untuk melakukan loading perlu dipantau waktu prosesnya agar efisien dan sesuai target operasional. Lead time loading menjadi salah satu indikator kunci kinerja (KPI) yang perlu dimonitor secara real-time.

Sebelum adanya aplikasi ini, pencatatan dan pelaporan lead time loading masih dilakukan secara manual menggunakan spreadsheet. Proses ini rentan terhadap kesalahan input, tidak memiliki validasi data, serta menyulitkan dalam pembuatan laporan agregat per shift, per customer, maupun per periode waktu. Data yang tersebar di banyak file spreadsheet juga menyulitkan dalam analisis tren dan pengambilan keputusan operasional.

Oleh karena itu, dikembangkanlah aplikasi **Lead Time Management System** berbasis desktop yang mampu melakukan pencatatan, monitoring, dan pelaporan lead time loading DO secara terpusat. Aplikasi ini dibangun menggunakan framework PySide6 (Qt6 for Python) dengan basis data SQLite, sehingga dapat berjalan secara mandiri tanpa memerlukan server atau koneksi internet.

## Rumusan Masalah

Berdasarkan latar belakang di atas, rumusan masalah dalam pengembangan aplikasi ini adalah:

1. Bagaimana merancang sistem pencatatan lead time loading DO yang terstruktur dan terpusat?
2. Bagaimana mengimplementasikan sistem yang mampu mendeteksi shift secara otomatis berdasarkan jadwal yang dapat dikonfigurasi?
3. Bagaimana menyediakan fitur dashboard dan laporan yang informatif untuk memantau kinerja operasional loading?
4. Bagaimana mengimplementasikan impor data dari Excel untuk memudahkan migrasi data lama?
5. Bagaimana memastikan data aman dengan adanya mekanisme backup dan restore?

## Tujuan

Tujuan dari pengembangan aplikasi ini adalah:

1. Menyediakan sistem pencatatan lead time loading DO yang terstruktur dengan database terpusat.
2. Mengimplementasikan deteksi shift otomatis yang mendukung jadwal dinamis dan shift overnight.
3. Menyediakan dashboard visual dengan grafik dan laporan dalam berbagai format (PDF, Excel).
4. Mengimplementasikan wizard impor Excel yang mampu mendeteksi header secara otomatis.
5. Menyediakan fitur backup dan restore database untuk keamanan data.

## Manfaat

Manfaat dari aplikasi ini adalah:

1. Memudahkan operator dalam mencatat data loading DO dengan form yang tervalidasi.
2. Mempercepat proses pembuatan laporan harian, mingguan, bulanan, per customer, dan per ekspedisi.
3. Membantu manajemen dalam memantau kinerja loading melalui dashboard visual.
4. Mengurangi risiko kehilangan data dengan adanya sistem database terpusat dan backup.
5. Meningkatkan akurasi data dengan validasi input dan deteksi duplikat otomatis.

## Batasan Masalah

Batasan masalah dalam pengembangan aplikasi ini adalah:

1. Aplikasi berjalan secara desktop menggunakan PySide6, bukan berbasis web.
2. Basis data menggunakan SQLite yang bersifat single-user, bukan database server.
3. Aplikasi dirancang khusus untuk operasional loading PT Eco Paper Indonesia.
4. Format ekspor laporan terbatas pada PDF dan Excel.
5. Tidak ada integrasi dengan sistem ERP atau sistem eksternal lainnya.
