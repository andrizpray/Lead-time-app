# Lead Time Management System

Aplikasi desktop **Lead Time** untuk **PT Eco Paper Indonesia** — tracking, analisis, dan pelaporan waktu lead time (loading) DO (Delivery Order) dengan antarmuka grafis Python.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![PySide6](https://img.shields.io/badge/UI-PySide6_Qt6-41CD52?logo=qt)
![SQLite](https://img.shields.io/badge/DB-SQLite+Peewee-003B57?logo=sqlite)
![PyInstaller](https://img.shields.io/badge/Build-PyInstaller-5C3D2E)
![Tests](https://img.shields.io/badge/Tests-36/36-brightgreen)

---

## Fitur

### 📥 Input & Import Data
- **Input Manual** — Form dialog untuk menambah/edit data DO dengan validasi real-time
- **Auto-kalkulasi** — Lead time (menit), shift (date-aware configurable), dan tonase total otomatis
- **Import Excel** — Wizard 3 langkah: pilih file → preview → insert dengan error summary
- **Auto-detect header** — Scan 15 baris pertama untuk header, handle berbagai format Excel
- **Dynamic tonase range** — Spinbox otomatis adjust sesuai nilai di database (hingga 999.999 kg)

### 📊 Tabel Data DO
- 16 kolom (Tanggal, No DO, No Shipment, Customer, Ekspedisi, Lead Time, Tonase, Shift, dll.)
- Filter panel — filter tanggal, customer, shift, jenis + search bar
- Pagination (50/100/200 baris per halaman)
- Highlight baris duplikat (DO sama) dengan warna kuning
- Double-click edit, toolbar add/edit/delete

### 📈 Dashboard
- **3 Summary Cards** — Total DO, Total Tonase, Rata-rata Lead Time
- **Bar Chart** — Lead time rata-rata per hari
- **Pie Chart** — Distribusi shift
- **Dual Y-Axis Line Chart** — Tren tonase Roll (kiri) + Sheet (kanan)
- **Top 10 Customer Table** — Nama customer + total tonase
- Date range filter (7/30/90 hari + Custom) + auto-refresh

### 📋 Laporan
- **6 jenis laporan**: Grafik Harian, Harian (per shift), Mingguan, Bulanan, Per Customer, Per Ekspedisi
- **Grafik Harian** — 2 bar chart side-by-side (DO Count + Tonase per Shift) + Trend Delivery line chart + tabel detail per DO
- Summary cards (total DO, total tonase, rata-rata LT)
- **Export Excel** (.xlsx) dengan timestamp filename
- **Export PDF** (ReportLab) dengan kop perusahaan + timestamp filename

### ⚙️ Pengaturan
- **Profil Perusahaan** — Nama perusahaan
- **Jadwal Shift per Tanggal** — Konfigurasi shift bisa berbeda per rentang tanggal, support overnight (misal 19:00–06:59), re-kalkulasi otomatis
- **Backup Database** — Backup ke `~/.leadtime/backups/` dengan timestamp
- **Restore Database** — Pilih file backup, konfirmasi overwrite

### 🔒 Production Hardening
- **Logging** — File log bulanan + stdout
- **Global exception hook** — Crash handler dengan error dialog + auto close DB
- **DB WAL mode** — Write-Ahead Logging untuk performa + durability
- **Safe close** — `close_db()` dipanggil saat exit normal maupun crash

---

## Tech Stack

| Komponen | Teknologi |
|---|---|
| **UI Framework** | PySide6 (Qt for Python 6) |
| **Charts** | PySide6.QtCharts |
| **ORM Database** | Peewee 3.x |
| **Database** | SQLite (WAL mode) |
| **Excel Export** | pandas + openpyxl |
| **PDF Export** | ReportLab 4.x |
| **Import Excel** | openpyxl langsung |
| **Packaging** | PyInstaller 6.x |

---

## Struktur Proyek

```
LeadTimeAppPython/
├── src/
│   ├── main.py                      # Entry point + logging + exception hook
│   ├── core/
│   │   ├── database.py              # Koneksi SQLite + WAL mode
│   │   ├── models.py                # Model DORecord (Peewee ORM, auto-calc)
│   │   ├── report.py                # Report generator (6 jenis laporan)
│   │   ├── settings.py              # Config manager (JSON) + backup/restore
│   │   └── migration.py             # Schema migration dengan playhouse
│   ├── ui/
│   │   ├── main_window.py           # Main window + sidebar navigasi
│   │   ├── do_form.py               # Form input/edit DO + validasi
│   │   ├── import_wizard.py         # Import wizard Excel 3 langkah
│   │   ├── do_table.py              # Tabel data DO + filter + pagination
│   │   ├── dashboard.py             # Dashboard dengan charts QtCharts
│   │   ├── report_widget.py         # Laporan + Grafik Harian + export
│   │   ├── settings_widget.py       # Pengaturan + shift schedule table
│   │   └── loading_overlay.py       # Loading overlay untuk operasi berat
│   └── utils/
│       ├── excel_exporter.py        # Export report/table ke Excel
│       ├── pdf_generator.py         # Export report ke PDF
│       └── excel_handler.py         # Handler import Excel + auto-detect
├── data/
│   └── leadtime.db                  # Database SQLite (auto-created)
├── build.sh                         # Build script PyInstaller (one-click)
├── leadtime.spec                    # PyInstaller spec
└── requirements.txt                 # Dependencies Python
```

---

## Instalasi & Menjalankan

### Prasyarat
- Python 3.11+
- pip

### 1. Clone & Setup

```bash
git clone https://github.com/andrizpray/Lead-time-app.git
cd Lead-time-app
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 2. Jalankan Aplikasi

```bash
python src/main.py
```

### 3. Build Executable (One-Click)

```bash
bash build.sh          # Incremental build (cepat)
bash build.sh --clean  # Fresh build dari awal
```

**Output:**
- **Linux:** `dist/LeadTimeApp` (single binary)
- **Windows:** `dist/LeadTimeApp.exe` (single executable)

---

## Database

- **Lokasi default:** `data/leadtime.db` (relatif ke root proyek)
- **Mode:** SQLite WAL — performa baca/tulis optimal, durable
- **Backup:** Menu Pengaturan → Backup Database → `~/.leadtime/backups/leadtime_YYYYMMDD_HHMMSS.db`

**Model `DORecord` — 17 fields:**
- `tgl`, `no_shipment` — composite unique key
- `customer`, `kota_kab`, `jenis`, `ekspedisi`, `jenis_truk`, `nomor_fk`
- `loading_mulai`, `loading_selesai` → auto-calc `lead_time_menit`
- `tonase_roll`, `tonase_sheet` → auto-calc `tonase_total`
- `shift` (1/2/3) — date-aware detection dari configurable schedule
- `created_at` — timestamp

---

## Pengembangan

### Testing

```bash
# Full test suite (36 test)
python3 /tmp/test_all_features.py
```

### Code Style
- Python type hints
- Docstrings dalam Bahasa Indonesia
- Nama fungsi/variabel: snake_case
- Nama class: PascalCase

---

## Lisensi

Proyek internal **PT Eco Paper Indonesia**.

---

*Dibangun dengan Python + PySide6 + SQLite. Siap produksi.*
