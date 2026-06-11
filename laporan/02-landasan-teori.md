---
bab: 2
judul: LANDASAN TEORI
---

## Konsep Lead Time dalam Logistik

Lead time dalam konteks logistik dan supply chain management adalah waktu yang dibutuhkan sejak suatu proses dimulai hingga selesai. Dalam operasional loading DO (Delivery Order), lead time loading dihitung dari jam mulai loading hingga jam selesai loading untuk setiap truk. Menurut Christopher (2016), manajemen lead time yang efektif dapat meningkatkan efisiensi operasional dan kepuasan pelanggan.

## Python

Python adalah bahasa pemrograman tingkat tinggi yang mendukung berbagai paradigma pemrograman termasuk pemrograman berorientasi objek, fungsional, dan prosedural. Python 3.11+ digunakan sebagai bahasa utama dalam pengembangan aplikasi ini karena memiliki ekosistem library yang kaya untuk pengembangan aplikasi desktop, pengolahan data, dan pembuatan laporan (Lutz, 2013).

## PySide6 (Qt6 for Python)

PySide6 adalah binding resmi Qt6 untuk Python yang dikembangkan oleh Qt Company. Framework ini menyediakan akses penuh ke Qt6 API untuk pengembangan aplikasi desktop multiplatform. Komponen utama yang digunakan dalam aplikasi ini meliputi:

1. **QtWidgets** — untuk pembuatan antarmuka pengguna seperti jendela, tombol, tabel, dialog, dan form.
2. **QtCharts** — untuk pembuatan grafik dan chart visual seperti bar chart, pie chart, dan line chart.
3. **QtCore** — untuk manajemen sinyal, slot, shortcut keyboard, dan threading.
4. **QtGui** — untuk pengaturan ikon, font, dan style sheet.

## Peewee ORM

Peewee adalah Object-Relational Mapping (ORM) library untuk Python yang ringan dan ekspresif. Peewee mendukung berbagai database relasional termasuk SQLite, MySQL, dan PostgreSQL. Fitur-fitur Peewee yang digunakan dalam aplikasi ini meliputi:

1. **Model definitions** — mendefinisikan struktur tabel DORecord dengan 17 field.
2. **Query builder** — untuk pembuatan query agregat seperti COUNT, SUM, AVG.
3. **Indexes** — untuk optimasi pencarian berdasarkan tgl dan no_shipment.
4. **Migrations** — untuk upgrade skema database secara bertahap.

## SQLite dan WAL Mode

SQLite adalah database relasional embedded yang ringan, tidak memerlukan server terpisah, dan menyimpan data dalam satu file. Aplikasi ini menggunakan SQLite dengan WAL (Write-Ahead Logging) mode yang memberikan keuntungan:

1. **Concurrent reads** — reader tidak memblokir reader lain.
2. **Write performance** — write operation lebih cepat karena menggunakan append-only log.
3. **Crash safety** — WAL mode lebih tahan terhadap kerusakan data akibat crash.
4. **Cache optimization** — menggunakan cache size 64MB untuk mempercepat query agregat.

## pandas dan openpyxl

pandas adalah library analisis data untuk Python yang menyediakan struktur data DataFrame untuk manipulasi data tabular. openpyxl adalah library untuk membaca dan menulis file Excel (.xlsx). Kedua library ini digunakan dalam aplikasi untuk:

1. **Import Excel** — membaca data dari file Excel, mendeteksi header, dan memproses baris data.
2. **Export laporan** — menulis hasil laporan ke format Excel dengan format yang rapi.

## ReportLab

ReportLab adalah library pembuatan PDF untuk Python yang menyediakan API untuk menghasilkan dokumen PDF secara programatik. ReportLab digunakan dalam aplikasi untuk mengekspor laporan ke format PDF dengan layout yang terstruktur.

## PyInstaller

PyInstaller adalah tool untuk mengemas aplikasi Python menjadi executable standalone. PyInstaller menganalisis dependensi aplikasi dan menggabungkannya menjadi satu file atau folder yang dapat dijalankan tanpa memerlukan Python interpreter terpisah.
