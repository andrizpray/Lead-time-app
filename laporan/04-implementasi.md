---
bab: 4
judul: IMPLEMENTASI
---

## Lingkungan Pengembangan

| Komponen | Spesifikasi |
|----------|-------------|
| Sistem Operasi | Ubuntu 22.04 LTS |
| Bahasa Pemrograman | Python 3.11 |
| Framework UI | PySide6 6.7.2 (Qt6) |
| ORM | Peewee 3.17.5 |
| Database | SQLite 3 (WAL mode) |
| Analisis Data | pandas 2.2.2 |
| Excel | openpyxl 3.1.5 |
| PDF | ReportLab 4.2.2 |
| Build Tool | PyInstaller 6.x |
| Tema | Swiss Modernism, light theme |

## Implementasi Database

### Inisialisasi Database

Database diinisialisasi menggunakan Peewee ORM dengan konfigurasi WAL mode:

```python
database.init(
    path,
    pragmas={
        "journal_mode": "wal",
        "foreign_keys": 1,
        "cache_size": -64000,
        "synchronous": "normal",
        "busy_timeout": 5000,
    },
)
```

Database path dapat dikustomisasi melalui environment variable `LEADTIME_DB_PATH`. Secara default, database disimpan di `data/leadtime.db`.

### Model Data

Model DORecord didefinisikan dengan Peewee. Auto-kalkulasi dilakukan dalam method `save()` yang dioverride:

```python
def save(self, *args, **kwargs):
    if self.loading_mulai and self.loading_selesai:
        self.lead_time_menit = _calc_lead_time(start, end)
        self.shift = _detect_shift(self.tgl, start)
    self.tonase_total = (self.tonase_roll or 0.0) + (self.tonase_sheet or 0.0)
    return super().save(*args, **kwargs)
```

### Auto-Deteksi Shift

Fungsi `_detect_shift` menggunakan konfigurasi jadwal shift dari pengaturan untuk menentukan shift berdasarkan jam mulai loading. Mendukung shift overnight (misal Shift 3: 19:00 - 06:59):

```python
def _in_range(t, start_str, end_str):
    s = _parse(start_str)
    e = _parse(end_str)
    if s <= e:
        return s <= t <= e
    else:
        return t >= s or t <= e
```

## Implementasi Antarmuka

### Main Window

Jendela utama menggunakan QSplitter horizontal dengan sidebar navigasi di kiri (lebar 220px) dan area konten di kanan. Sidebar menggunakan tema gelap (#1e293b) dengan tombol navigasi yang memiliki efek hover dan active state. Enam halaman dapat diakses melalui sidebar atau shortcut keyboard (Ctrl+1 sampai Ctrl+5, Ctrl+N untuk input baru).

### Dashboard

Dashboard menampilkan 3 summary cards:
- **Total DO** — jumlah total DO dalam rentang tanggal
- **Total Tonase** — total tonase dalam kilogram
- **Rata-rata Lead Time** — rata-rata lead time dalam menit

Terdapat juga 4 grafik:
- **Bar Chart** — rata-rata lead time per shift (per hari)
- **Pie Chart** — distribusi DO per shift
- **Line Chart** — tren tonase per hari (dual-axis)
- **Bar Chart** — top 10 customer berdasarkan jumlah DO

### Tabel Data DO

Tabel menampilkan 16 kolom data DO dengan fitur:
- **Filter tanggal** — rentang tanggal yang dapat disesuaikan
- **Search** — pencarian teks di semua field
- **Pagination** — 50/100/200 record per halaman
- **Highlight duplikat** — baris duplikat berwarna kuning
- **Double-click edit** — membuka form edit
- **Toolbar CRUD** — tombol tambah, edit, hapus

### Form Input DO

Form input terdiri dari field-field yang diperlukan dengan validasi real-time. Form melakukan auto-kalkulasi lead time dan deteksi shift saat user mengisi jam loading. Validasi mencakup:
- Field tanggal harus diisi
- Nomor shipment tidak boleh duplikat
- Jam selesai harus setelah jam mulai
- Tonase harus angka positif

### Import Excel Wizard

Wizard import Excel memiliki 3 langkah:
1. **Pilih file** — user memilih file Excel (.xlsx)
2. **Preview** — sistem membaca 15 baris pertama untuk auto-detect header, menampilkan preview data dengan warna validasi (hijau = valid, merah = error, kuning = duplikat)
3. **Import** — sistem mengimpor data yang valid dan menampilkan ringkasan (berhasil, gagal, duplikat)

### Laporan

Widget laporan menyediakan 6 jenis laporan:
1. **Grafik Harian** — chart per shift + tabel detail per DO
2. **Harian** — ringkasan per shift per hari
3. **Mingguan** — agregat per minggu
4. **Bulanan** — agregat per shift + per customer
5. **Per Customer** — total DO dan tonase per customer
6. **Per Ekspedisi** — total DO dan tonase per ekspedisi

Setiap laporan dapat diekspor ke PDF (via ReportLab) dan Excel (via openpyxl).

## Implementasi Keamanan

1. **Close DB Handler** — database ditutup secara aman saat aplikasi exit maupun saat terjadi crash melalui global exception hook:
   ```python
   sys.excepthook = global_excepthook
   ```
2. **WAL Mode** — Write-Ahead Logging untuk mencegah korupsi data.
3. **Logging Bulanan** — semua aktivitas dan error dicatat ke file log dengan rotasi bulanan.
4. **Backup/Restore** — pengaturan memungkinkan backup database ke lokasi yang ditentukan user.
