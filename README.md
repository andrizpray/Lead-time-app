# Lead Time Management System

Aplikasi desktop **Lead Time** untuk **PT Eco Paper Indonesia** — tracking, analisis, dan pelaporan waktu lead time (loading) DO (Delivery Order) dengan antarmuka grafis Python.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![PySide6](https://img.shields.io/badge/UI-PySide6_Qt6-41CD52?logo=qt)
![SQLite](https://img.shields.io/badge/DB-SQLite+Peewee-003B57?logo=sqlite)
![PyInstaller](https://img.shields.io/badge/Build-PyInstaller-5C3D2E)

---

## Fitur

### 📥 Input & Import Data
- **Input Manual** — Form dialog untuk menambah/edit data DO dengan validasi real-time
- **Auto-kalkulasi** — Lead time (menit), shift (1/2/3), dan tonase total otomatis
- **Import Excel** — Wizard 3 langkah: pilih file → preview dengan highlight warna → insert dengan progress bar

### 📊 Tabel Data DO
- 16 kolom (Tanggal, No DO, No Shipment, Customer, Ekspedisi, Lead Time, Tonase, Shift, dll.)
- Filter panel — filter berdasarkan tanggal, customer, ekspedisi, shift
- Pagination (50/100/200 baris per halaman)
- Highlight baris duplikat (DO sama) dengan warna kuning
- Double-click edit, toolbar add/edit/delete

### 📈 Dashboard
- Ringkasan 3 kartu: **Total DO**, **Rata-rata Lead Time**, **Total Tonase**
- **Bar Chart** — Lead time per hari
- **Pie Chart** — Distribusi shift
- **Line Chart** — Tonase Roll & Sheet dual line
- **Top 10 Customer** — Bar chart customer dengan DO terbanyak
- Date range filter + auto-refresh

### 📋 Laporan
- **5 jenis laporan**: Harian (per shift), Mingguan, Bulanan (per customer), Per Customer, Per Ekspedisi
- Summary cards (total DO, rata-rata LT, total tonase)
- Tabel detail dinamis
- **Export Excel** (.xlsx) dengan header biru, auto-fit kolom, border rapi
- **Export PDF** (ReportLab) dengan kop perusahaan, header abu-abu, nomor halaman

### ⚙️ Pengaturan
- Nama perusahaan — disimpan di `~/.leadtime/config.json`
- **Backup Database** — backup ke `~/.leadtime/backups/` dengan timestamp
- **Restore Database** — pilih file backup, konfirmasi overwrite
- Buka folder backup via file manager

### 🚀 Build Mandiri
- Build dengan PyInstaller → satu binary executable (Linux `.desktop` / Windows `.exe`)
- Ukuran ~113MB (Linux), ~80MB (Windows after UPX)

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
| **Testing** | pytest + unittest |

---

## Struktur Proyek

```
LeadTimeAppPython/
├── src/
│   ├── main.py                      # Entry point aplikasi
│   ├── core/
│   │   ├── database.py              # Koneksi SQLite + WAL mode
│   │   ├── models.py                # Model DORecord (Peewee ORM)
│   │   ├── report.py                # Report generator (5 jenis laporan)
│   │   └── settings.py              # Config manager (JSON) + backup/restore DB
│   ├── ui/
│   │   ├── main_window.py           # Main window + sidebar navigasi
│   │   ├── input_widget.py          # Form input manual DO
│   │   ├── import_widget.py         # Import wizard Excel
│   │   ├── do_table.py              # Tabel data DO dengan filter & pagination
│   │   ├── dashboard_widget.py      # Dashboard dengan charts QtCharts
│   │   ├── report_widget.py         # Halaman laporan + export
│   │   └── settings_widget.py       # Halaman pengaturan
│   └── utils/
│       ├── excel_exporter.py        # Export report/table ke Excel
│       ├── pdf_generator.py         # Export report ke PDF
│       └── excel_handler.py         # Handler import Excel
├── data/
│   └── leadtime.db                  # Database SQLite (auto-created)
├── tests/                           # Unit tests
├── build.sh                         # Build script PyInstaller
├── leadtime.spec                    # PyInstaller spec
└── requirements.txt                 # Dependencies Python
```

---

## Instalasi & Menjalankan

### Prasyarat
- Python 3.11+
- pip / uv

### 1. Clone & Setup

```bash
git clone https://github.com/andrizpray/Lead-time-app.git
cd Lead-time-app
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# atau venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Jalankan Aplikasi

```bash
python -m src.main
```

Atau langsung:
```bash
python src/main.py
```

### 3. Build Executable

**Linux/macOS:**
```bash
bash build.sh
```

**Windows (manual):**
```powershell
pip install pyinstaller
pyinstaller leadtime.spec --noconfirm --clean
```

Output: `dist/LeadTimeApp/` (Linux) atau `dist/LeadTimeApp.exe` (Windows).

---

## Screenshots

| Halaman | Deskripsi |
|---|---|
| **Dashboard** | Grafik batang lead time, pie shift, line tonase, top 10 customer |
| **Data DO** | Tabel dengan filter, pagination, highlight duplikat |
| **Input** | Form dialog input/edit DO dengan validasi real-time |
| **Import** | Wizard preview Excel dengan progress bar |
| **Laporan** | 5 jenis laporan + export Excel/PDF |
| **Pengaturan** | Profil perusahaan, backup/restore database |

> *(Screenshot menyusul — jalankan aplikasi untuk preview langsung)*

---

## Database

- **Lokasi default:** `data/leadtime.db` (relatif ke root proyek)
- **Mode:** SQLite WAL (Write-Ahead Logging) — performa baca/tulis optimal
- **Backup:** Manual via menu Pengaturan → Backup Database → `~/.leadtime/backups/leadtime_YYYYMMDD_HHMMSS.db`
- **Field utama model `DORecord`:**
  - `tgl`, `no_shipment` (composite unique key)
  - `customer`, `ekspedisi`, `jenis_truk`
  - `loading_mulai`, `loading_selesai` → auto-calc `lead_time_menit`
  - `tonase_roll`, `tonase_sheet` → auto-calc `tonase_total`
  - `shift` (1/2/3) — terdeteksi otomatis dari jam loading

---

## Pengembangan

### Menambah Fitur Baru

1. **Model** → tambah field di `src/core/models.py`
2. **Database** → migrasi di `src/core/database.py` (create table otomatis via `Peewee.create_table`)
3. **UI** → tambah widget di `src/ui/` dan daftarkan di `main_window.py`
4. **Export** → tambah fungsi di `src/utils/`

### Testing

```bash
pytest tests/ -v
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

*Dibangun dengan Python + PySide6 + SQLite.*
