---
bab: 3
judul: ANALISIS DAN PERANCANGAN
---

## Analisis Kebutuhan

### Kebutuhan Fungsional

Berdasarkan analisis kebutuhan operasional loading DO di PT Eco Paper Indonesia, kebutuhan fungsional sistem adalah sebagai berikut:

1. **Manajemen Data DO** — sistem mampu mencatat, mengedit, menghapus, dan menampilkan data DO dengan 17 field informasi.
2. **Deteksi Shift Otomatis** — sistem mampu mendeteksi shift (1, 2, atau 3) secara otomatis berdasarkan jam mulai loading dan jadwal shift yang dapat dikonfigurasi.
3. **Kalkulasi Lead Time** — sistem mampu menghitung lead time secara otomatis dari selisih jam mulai dan selesai loading, termasuk menangani loading yang melewati tengah malam (overnight).
4. **Dashboard Visual** — sistem mampu menampilkan ringkasan data dalam bentuk cards dan grafik (bar chart, pie chart, line chart).
5. **Laporan** — sistem mampu menghasilkan laporan dalam 6 jenis (grafik harian, harian, mingguan, bulanan, per customer, per ekspedisi) dengan ekspor ke PDF dan Excel.
6. **Import Excel** — sistem mampu mengimpor data dari file Excel dengan deteksi header otomatis dan validasi data.
7. **Pengaturan Shift** — sistem mampu menyimpan jadwal shift per tanggal dengan dukungan shift overnight.
8. **Backup dan Restore** — sistem mampu melakukan backup dan restore database.

### Kebutuhan Non-Fungsional

1. **Performa** — query agregat untuk dashboard harus selesai dalam waktu kurang dari 5 detik untuk 10.000+ record.
2. **Keamanan** — data tetap aman meskipun aplikasi crash dengan implementasi WAL mode dan close_db handler.
3. **Usability** — antarmuka menggunakan tema light dengan navigasi sidebar yang intuitif.
4. **Portabilitas** — aplikasi dapat dibangun menjadi executable standalone dengan PyInstaller.
5. **Reliabilitas** — logging bulanan untuk memudahkan debugging dan audit.

## Perancangan Sistem

### Arsitektur Sistem

Aplikasi menggunakan arsitektur three-tier sederhana yang terdiri dari:

1. **Presentation Layer** — modul `src/ui/` berisi widget-widget PySide6 untuk antarmuka pengguna.
2. **Business Logic Layer** — modul `src/core/` berisi model, database, report generator, dan settings.
3. **Data Layer** — SQLite database dengan Peewee ORM sebagai jembatan antara business logic dan database.

### Arsitektur Modul

```
LeadTimeAppPython/
-- src/
    -- main.py                   -- Entry point, logging, crash handler
    -- core/
        -- database.py           -- SQLite WAL init, koneksi, close_db
        -- models.py             -- DORecord model + auto-calc lead time & shift
        -- report.py             -- 6 jenis laporan (daily, weekly, monthly, dll)
        -- settings.py           -- Config JSON, shift schedule, backup/restore
        -- migration.py          -- Versioning skema database
    -- ui/
        -- main_window.py        -- Main window, sidebar navigasi, styling
        -- dashboard.py          -- Dashboard dengan 4 chart + 3 card
        -- do_table.py           -- Tabel data DO dengan filter, search, pagination
        -- do_form.py            -- Form input/edit DO dengan validasi
        -- import_wizard.py      -- Wizard import Excel 3 langkah
        -- report_widget.py      -- 6 jenis laporan + export PDF/Excel
        -- settings_widget.py    -- Settings: shift schedule, backup/restore
        -- loading_overlay.py    -- Overlay animasi loading
    -- utils/
        -- excel_handler.py      -- Parser dan auto-detect header Excel
        -- excel_exporter.py     -- Export report ke .xlsx
        -- pdf_generator.py      -- Export report ke PDF via ReportLab
```

### Entity Relationship Diagram

Aplikasi menggunakan satu tabel utama dengan struktur sebagai berikut:

**Tabel: do_records**

| Field | Tipe Data | Keterangan |
|-------|-----------|------------|
| id | Integer (PK) | Primary key, auto-increment |
| tgl | Date | Tanggal DO |
| no_do | String(50) | Nomor Delivery Order |
| no_shipment | String(50) | Nomor shipment (unique key + tgl) |
| customer | String(100) | Nama customer |
| kota_kab | String(100) | Kota/Kabupaten tujuan |
| jenis | String(50) | Tipe produk: ROLL / SHEET |
| ekspedisi | String(100) | Nama ekspedisi |
| jenis_truk | String(50) | Tipe truk |
| nomor_fk | String(50) | Nomor FK (nullable) |
| loading_mulai | Time | Jam mulai loading |
| loading_selesai | Time | Jam selesai loading |
| lead_time_menit | Integer | Auto-calc dari selisih jam |
| tonase_roll | Float | Tonase ROLL (kg) |
| tonase_sheet | Float | Tonase SHEET (kg) |
| tonase_total | Float | Auto-calc: roll + sheet |
| shift | Integer | Auto-detect: 1, 2, atau 3 |
| created_at | DateTime | Timestamp pembuatan record |

### Alur Utama Aplikasi

1. **Input DO** — User mengisi form input DO (tanggal, customer, waktu loading, tonase, dll) → sistem auto-kalkulasi lead time dan shift → data disimpan ke database.
2. **Import Excel** — User memilih file Excel → sistem membaca 15 baris pertama untuk auto-detect header → preview data dengan warna validasi → user konfirmasi → data diimpor.
3. **Dashboard** — Sistem membaca data dari database → menghitung agregat per shift/hari → menampilkan 3 summary cards, bar chart lead time, pie chart shift, dan line chart tonase.
4. **Laporan** — User memilih jenis laporan dan rentang tanggal → sistem menjalankan query agregat → menampilkan hasil di tabel dan chart → user dapat ekspor ke PDF/Excel.
