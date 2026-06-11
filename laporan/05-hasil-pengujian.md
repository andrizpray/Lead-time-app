---
bab: 5
judul: HASIL DAN PEMBAHASAN
---

## Hasil Implementasi

Aplikasi Lead Time Management System berhasil dibangun dengan 16 widget, 3.400+ baris kode, dan 36 automated test yang seluruhnya lulus. Seluruh fitur yang direncanakan telah diimplementasikan sesuai dengan analisis kebutuhan.

## Pengujian Fungsional (Black Box Testing)

### Pengujian Input dan Validasi Data

| No | Skenario | Input | Hasil yang Diharapkan | Status |
|----|----------|-------|----------------------|--------|
| 1 | Input DO valid | Data lengkap dengan jam loading valid | Data tersimpan, lead time dan shift terhitung otomatis | Ya |
| 2 | Input DO duplikat | no_shipment yang sama pada tgl yang sama | Error duplikat, data tidak tersimpan | Ya |
| 3 | Input tanpa jam selesai | Hanya jam mulai | Lead time = 0, shift terdeteksi | Ya |
| 4 | Input loading overnight | Jam mulai 23:00, jam selesai 01:30 | Lead time = 150 menit | Ya |
| 5 | Edit data existing | Ubah jam loading | Lead time dan shift ter-update | Ya |

### Pengujian Dashboard

| No | Skenario | Input | Hasil yang Diharapkan | Status |
|----|----------|-------|----------------------|--------|
| 1 | Dashboard tanpa data | Database kosong | Cards menampilkan 0, chart kosong | Ya |
| 2 | Dashboard dengan data | 100+ record | Cards, 4 chart, top customer tampil | Ya |
| 3 | Filter date range | Pilih rentang 7/30/90 hari | Data terfilter sesuai range | Ya |

### Pengujian Import Excel

| No | Skenario | Input | Hasil yang Diharapkan | Status |
|----|----------|-------|----------------------|--------|
| 1 | Import file valid | File Excel dengan format benar | Data terimport, ringkasan sukses | Ya |
| 2 | Import dengan duplikat | File berisi data yang sudah ada | Duplikat terdeteksi, dilewati | Ya |
| 3 | File tidak valid | File bukan Excel | Error message, proses berhenti | Ya |

### Pengujian Laporan

| No | Skenario | Input | Hasil yang Diharapkan | Status |
|----|----------|-------|----------------------|--------|
| 1 | Laporan harian | Pilih tanggal | Data per shift tampil | Ya |
| 2 | Laporan mingguan | Pilih rentang 2 minggu | Agregat per minggu | Ya |
| 3 | Laporan bulanan | Pilih bulan | Data per shift + per customer | Ya |
| 4 | Export PDF | Klik export PDF | File PDF terdownload | Ya |
| 5 | Export Excel | Klik export Excel | File Excel terdownload | Ya |

### Pengujian Pengaturan

| No | Skenario | Input | Hasil yang Diharapkan | Status |
|----|----------|-------|----------------------|--------|
| 1 | Ubah jadwal shift | Set shift 1: 06:00-13:59 | Shift ter-update di form input | Ya |
| 2 | Backup database | Klik backup | File database tercopy ke lokasi tujuan | Ya |
| 3 | Restore database | Pilih file backup | Database ter-restore | Ya |

### Pengujian Keamanan dan Stabilitas

| No | Skenario | Input | Hasil yang Diharapkan | Status |
|----|----------|-------|----------------------|--------|
| 1 | Crash handling | Raise exception | Error ter-log, database tertutup aman | Ya |
| 2 | Startup dengan db rusak | Hapus tabel | Auto-create tabel baru | Ya |
| 3 | Concurrent read | Buka dashboard + laporan | Kedua query jalan tanpa blocking | Ya |

## Pembahasan

Berdasarkan hasil pengujian, seluruh fitur berjalan sesuai dengan yang diharapkan. Beberapa temuan penting selama pengembangan:

1. **Deteksi Shift Overnight** — Implementasi deteksi shift yang mendukung loading melewati tengah malam memerlukan logika khusus. Pendekatan dengan membandingkan jam mulai dan selesai (jika jam mulai > jam selesai, berarti overnight) terbukti efektif.

2. **Auto-Detect Header Excel** — Algoritma yang membaca 15 baris pertama untuk mendeteksi header secara otomatis memudahkan pengguna dalam mengimpor data dari berbagai format Excel tanpa perlu konfigurasi manual.

3. **Optimasi Query Dashboard** — Penggunaan indeks pada kolom `tgl` dan `no_shipment` serta cache size 64MB memastikan query agregat untuk dashboard berjalan cepat meskipun dengan ribuan record.

4. **Keamanan Data** — Implementasi WAL mode dan `close_db()` handler memberikan jaminan bahwa data tidak akan hilang meskipun aplikasi crash secara tiba-tiba.
