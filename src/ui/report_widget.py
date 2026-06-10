from datetime import date, datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QValueAxis,
)

from src.core.report import ReportGenerator
from src.utils.excel_exporter import export_report_to_excel
from src.utils.pdf_generator import export_report_to_pdf

_COMPANY_NAME = "PT Eco Paper Indonesia"


# ---------------------------------------------------------------------------
# Helpers shared with dashboard style
# ---------------------------------------------------------------------------

def _drop_shadow(widget: QWidget, blur: int = 14, dy: int = 3, alpha: int = 35):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, dy)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


def _fmt_lt(minutes: float) -> str:
    m = int(minutes)
    h, rem = divmod(m, 60)
    return f"{h}j {rem}m" if h else f"{rem} mnt"


# ---------------------------------------------------------------------------
# Small summary card (mirrors DashboardWidget cards)
# ---------------------------------------------------------------------------

class _Card(QFrame):
    def __init__(self, title: str, icon: str, accent: str, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border-radius: 12px;
                border-top: 4px solid {accent};
                border-left: none; border-right: none; border-bottom: none;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(100)
        _drop_shadow(self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 20px; color: {accent}; border: none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; border: none;")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        lay.addLayout(header)

        self._val = QLabel("—")
        self._val.setStyleSheet(f"color: {accent}; font-size: 24px; font-weight: bold; border: none;")
        lay.addWidget(self._val)

    def set_value(self, text: str):
        self._val.setText(text)


# ---------------------------------------------------------------------------
# ReportWidget
# ---------------------------------------------------------------------------

_REPORT_TYPES = [
    "Grafik Harian",
    "Harian",
    "Mingguan",
    "Bulanan",
    "Per Customer",
    "Per Ekspedisi",
]

# Columns per report type: (header, data_key)
_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "Harian": [
        ("Shift", "shift"),
        ("Jumlah DO", "count_do"),
        ("Total Tonase (kg)", "total_tonase"),
        ("Avg Lead Time", "avg_lead_time"),
    ],
    "Mingguan": [
        ("Minggu Ke", "minggu_ke"),
        ("Tgl Mulai", "tgl_mulai"),
        ("Tgl Akhir", "tgl_akhir"),
        ("Total DO", "total_do"),
        ("Total Tonase (kg)", "total_tonase"),
        ("Avg Lead Time", "avg_lead_time"),
        ("Shift 1", "shift_1_count"),
        ("Shift 2", "shift_2_count"),
        ("Shift 3", "shift_3_count"),
    ],
    "Bulanan": [
        ("Customer", "customer"),
        ("Jumlah DO", "count"),
        ("Total Tonase (kg)", "tonase"),
        ("Avg Lead Time", "avg_lead_time"),
    ],
    "Per Customer": [
        ("Customer", "customer"),
        ("Jumlah DO", "count_do"),
        ("Total Tonase (kg)", "total_tonase"),
        ("Avg Lead Time", "avg_lead_time"),
    ],
    "Per Ekspedisi": [
        ("Ekspedisi", "ekspedisi"),
        ("Jumlah DO", "count_do"),
        ("Total Tonase (kg)", "total_tonase"),
        ("Avg Lead Time", "avg_lead_time"),
    ],
}


class ReportWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_data: dict | list | None = None
        self._last_type: str = ""
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: #F5F7FA; }")

        inner = QWidget()
        inner.setStyleSheet("background: #F5F7FA;")
        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.setSpacing(16)

        vbox.addWidget(self._build_filter_panel())
        vbox.addLayout(self._build_cards_row())
        vbox.addWidget(self._build_table_section())
        vbox.addWidget(self._build_chart_section())   # grafik harian
        vbox.addLayout(self._build_export_row())
        vbox.addStretch()

        scroll.setWidget(inner)
        root.addWidget(scroll)

        self._on_type_changed(self._combo_type.currentText())

    def _build_chart_section(self) -> QWidget:
        """Container untuk tiga grafik (DO per Shift, Tonase per Shift, Trend Delivery)."""
        self._chart_container = QWidget()
        self._chart_container.setVisible(False)

        vbox = QVBoxLayout(self._chart_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(16)

        # --- Grafik 1: DO per Shift (kiri) + Tonase per Shift (kanan) ---
        frame1 = QFrame()
        frame1.setStyleSheet("QFrame { background:#FFFFFF; border-radius:10px; border:1px solid #E2E8F0; }")
        _drop_shadow(frame1, blur=10, dy=2, alpha=25)
        lay1 = QHBoxLayout(frame1)
        lay1.setContentsMargins(8, 8, 8, 8)
        lay1.setSpacing(8)

        # -- kiri: DO Count per Shift --
        self._chart_shift_do = QChart()
        self._chart_shift_do.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._chart_shift_do.setBackgroundVisible(False)
        self._view_shift_do = QChartView(self._chart_shift_do)
        self._view_shift_do.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view_shift_do.setMinimumHeight(360)
        self._view_shift_do.setStyleSheet("background: transparent;")
        lay1.addWidget(self._view_shift_do, 50)

        # -- kanan: Tonase per Shift --
        self._chart_shift_ton = QChart()
        self._chart_shift_ton.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._chart_shift_ton.setBackgroundVisible(False)
        self._view_shift_ton = QChartView(self._chart_shift_ton)
        self._view_shift_ton.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view_shift_ton.setMinimumHeight(360)
        self._view_shift_ton.setStyleSheet("background: transparent;")
        lay1.addWidget(self._view_shift_ton, 50)

        vbox.addWidget(frame1)

        # --- Grafik 2: Trend Delivery ---
        frame2 = QFrame()
        frame2.setStyleSheet("QFrame { background:#FFFFFF; border-radius:10px; border:1px solid #E2E8F0; }")
        _drop_shadow(frame2, blur=10, dy=2, alpha=25)
        lay2 = QVBoxLayout(frame2)
        lay2.setContentsMargins(8, 8, 8, 8)

        self._chart_trend = QChart()
        self._chart_trend.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self._chart_trend.setBackgroundVisible(False)

        self._view_trend = QChartView(self._chart_trend)
        self._view_trend.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view_trend.setMinimumHeight(340)
        self._view_trend.setStyleSheet("background: transparent;")
        lay2.addWidget(self._view_trend)
        vbox.addWidget(frame2)

        return self._chart_container

    def _build_filter_panel(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        _drop_shadow(frame, blur=8, dy=2, alpha=20)

        row = QHBoxLayout(frame)
        row.setContentsMargins(16, 12, 16, 12)
        row.setSpacing(12)

        lbl_style = "color: #0F172A; font-size: 12px; font-weight: 600;"

        # Jenis laporan
        jenis_lbl = QLabel("Laporan:")
        jenis_lbl.setStyleSheet(lbl_style)
        row.addWidget(jenis_lbl)

        self._combo_type = QComboBox()
        self._combo_type.addItems(_REPORT_TYPES)
        self._combo_type.setFixedWidth(150)
        row.addWidget(self._combo_type)

        row.addSpacing(8)

        # Date inputs (shown/hidden depending on type)
        self._lbl_tgl = QLabel("Tanggal:")
        self._lbl_tgl.setStyleSheet(lbl_style)
        row.addWidget(self._lbl_tgl)

        self._date_single = QDateEdit()
        self._date_single.setCalendarPopup(True)
        self._date_single.setDisplayFormat("dd/MM/yyyy")
        # Default: latest date from DB
        try:
            from src.core.models import DORecord
            from peewee import fn as _fn
            db_last = DORecord.select(_fn.MAX(DORecord.tgl)).scalar()
            if db_last:
                self._date_single.setDate(QDate(db_last.year, db_last.month, db_last.day))
            else:
                self._date_single.setDate(QDate.currentDate())
        except Exception:
            self._date_single.setDate(QDate.currentDate())
        row.addWidget(self._date_single)

        self._lbl_dari = QLabel("Dari:")
        self._lbl_dari.setStyleSheet(lbl_style)
        row.addWidget(self._lbl_dari)

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("dd/MM/yyyy")
        self._date_from.setDate(QDate.currentDate().addDays(-29))
        row.addWidget(self._date_from)

        self._lbl_sampai = QLabel("Sampai:")
        self._lbl_sampai.setStyleSheet(lbl_style)
        row.addWidget(self._lbl_sampai)

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("dd/MM/yyyy")
        self._date_to.setDate(QDate.currentDate())
        row.addWidget(self._date_to)

        # Month/year for Bulanan
        self._lbl_bulan = QLabel("Bulan:")
        self._lbl_bulan.setStyleSheet(lbl_style)
        row.addWidget(self._lbl_bulan)

        self._spin_bulan = QSpinBox()
        self._spin_bulan.setRange(1, 12)
        self._spin_bulan.setValue(QDate.currentDate().month())
        self._spin_bulan.setFixedWidth(55)
        row.addWidget(self._spin_bulan)

        self._lbl_tahun = QLabel("Tahun:")
        self._lbl_tahun.setStyleSheet(lbl_style)
        row.addWidget(self._lbl_tahun)

        self._spin_tahun = QSpinBox()
        self._spin_tahun.setRange(2000, 2100)
        self._spin_tahun.setValue(QDate.currentDate().year())
        self._spin_tahun.setFixedWidth(70)
        row.addWidget(self._spin_tahun)

        row.addStretch()

        btn_gen = QPushButton("Generate")
        btn_gen.setFixedWidth(100)
        btn_gen.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
        """)
        btn_gen.clicked.connect(self._generate)
        row.addWidget(btn_gen)

        self._combo_type.currentTextChanged.connect(self._on_type_changed)

        return frame

    def _build_cards_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        self._card_do = _Card("Total DO", "📦", "#3b82f6")
        self._card_tonase = _Card("Total Tonase", "⚖️", "#10b981")
        self._card_lt = _Card("Rata-rata Lead Time", "⏱️", "#f59e0b")
        for c in (self._card_do, self._card_tonase, self._card_lt):
            row.addWidget(c)
        return row

    def _build_table_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        _drop_shadow(frame, blur=10, dy=2, alpha=25)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._table.setStyleSheet("""
            QTableWidget {
                border: none;
                border-radius: 10px;
                font-size: 12px;
                gridline-color: #E2E8F0;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                color: #059669;
                font-weight: 600;
                font-size: 12px;
                padding: 8px;
                border-bottom: 2px solid #059669;
                border-right: 1px solid #E2E8F0;
            }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
            QTableWidget::item:selected { background-color: #D1FAE5; color: #0F172A; }
        """)

        lay.addWidget(self._table)
        return frame

    def _build_export_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addStretch()

        btn_excel = QPushButton("Export Excel")
        btn_excel.setFixedWidth(130)
        btn_excel.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #059669; }
            QPushButton:pressed { background-color: #047857; }
        """)
        btn_excel.clicked.connect(self._export_excel)
        row.addWidget(btn_excel)

        btn_pdf = QPushButton("Export PDF")
        btn_pdf.setFixedWidth(130)
        btn_pdf.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #dc2626; }
            QPushButton:pressed { background-color: #b91c1c; }
        """)
        btn_pdf.clicked.connect(self._export_pdf)
        row.addWidget(btn_pdf)

        return row

    # ------------------------------------------------------------------
    # Filter visibility
    # ------------------------------------------------------------------

    def _on_type_changed(self, rtype: str):
        is_grafik = rtype == "Grafik Harian"
        is_harian = rtype == "Harian"
        is_bulanan = rtype == "Bulanan"
        is_range = rtype in ("Grafik Harian", "Mingguan", "Per Customer", "Per Ekspedisi")

        self._lbl_tgl.setVisible(is_harian)
        self._date_single.setVisible(is_harian)
        self._lbl_dari.setVisible(is_range)
        self._date_from.setVisible(is_range)
        self._lbl_sampai.setVisible(is_range)
        self._date_to.setVisible(is_range)
        self._lbl_bulan.setVisible(is_bulanan)
        self._spin_bulan.setVisible(is_bulanan)
        self._lbl_tahun.setVisible(is_bulanan)
        self._spin_tahun.setVisible(is_bulanan)

        # Grafik hanya tampil untuk tipe Grafik Harian
        if hasattr(self, "_chart_container"):
            self._chart_container.setVisible(is_grafik)

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def _generate(self):
        rtype = self._combo_type.currentText()

        try:
            if rtype == "Grafik Harian":
                tgl_a = self._date_from.date().toPython()
                tgl_b = self._date_to.date().toPython()
                self._show_grafik_harian(tgl_a, tgl_b)

            elif rtype == "Harian":
                tgl = self._date_single.date().toPython()
                self._show_harian(tgl)

            elif rtype == "Mingguan":
                tgl_a = self._date_from.date().toPython()
                tgl_b = self._date_to.date().toPython()
                self._show_mingguan(tgl_a, tgl_b)

            elif rtype == "Bulanan":
                self._show_bulanan(self._spin_tahun.value(), self._spin_bulan.value())

            elif rtype == "Per Customer":
                tgl_a = self._date_from.date().toPython()
                tgl_b = self._date_to.date().toPython()
                self._show_customer(tgl_a, tgl_b)

            elif rtype == "Per Ekspedisi":
                tgl_a = self._date_from.date().toPython()
                tgl_b = self._date_to.date().toPython()
                self._show_ekspedisi(tgl_a, tgl_b)

            self._last_type = rtype

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Gagal mengambil data:\n{exc}")

    # ------------------------------------------------------------------
    # Grafik Harian — tabel detail + 2 grafik
    # ------------------------------------------------------------------

    _DETAIL_COLS = [
        ("TGL",         "tgl"),
        ("DO",          "no_do"),
        ("No Shipment", "no_shipment"),
        ("Customer",    "customer"),
        ("Kota/Kab",    "kota_kab"),
        ("Jenis",       "jenis"),
        ("Tonase (kg)", "tonase_total"),
        ("Shift",       "shift"),
    ]

    def _show_grafik_harian(self, tgl_awal: date, tgl_akhir: date):
        data = ReportGenerator.daily_detail_report(tgl_awal, tgl_akhir)
        self._last_data = data

        self._update_cards(data["total_do"], data["total_ton"], 0.0)

        # Calculate avg lead time from records
        records = data["records"]
        if records:
            total_lt = sum(r.lead_time_menit for r in records if r.lead_time_menit)
            avg_lt = total_lt / len(records) if records else 0.0
            h, m_desc = divmod(int(avg_lt), 60)
            lt_str = f"{h}j {m_desc}m" if h else f"{m_desc} mnt"
            self._card_lt.set_value(lt_str)
        else:
            self._card_lt.set_value("—")

        # --- isi tabel detail ---
        records = data["records"]
        cols = self._DETAIL_COLS
        self._table.clear()
        self._table.setColumnCount(len(cols))
        self._table.setRowCount(len(records) + 1)  # +1 baris TOTAL
        self._table.setHorizontalHeaderLabels([c[0] for c in cols])

        jenis_colors = {"ROLL": QColor("#FFF9C4"), "SHEET": QColor("#E8F5E9")}
        dup_no_do: set[str] = set()
        # tandai no_do duplikat
        from collections import Counter
        no_do_counts = Counter(r.no_do for r in records)
        dup_no_do = {nd for nd, cnt in no_do_counts.items() if cnt > 1}

        for row_idx, rec in enumerate(records):
            for col_idx, (_, key) in enumerate(cols):
                val = getattr(rec, key, "")
                if key == "tgl":
                    text = val.strftime("%d/%m/%Y") if hasattr(val, "strftime") else str(val)
                elif key == "tonase_total":
                    text = f"{float(val):,.2f}"
                elif key == "shift":
                    text = f"Shift {val}"
                else:
                    text = str(val) if val is not None else "—"

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # highlight: no_do duplikat → kuning
                if rec.no_do in dup_no_do:
                    item.setBackground(QColor("#FFF59D"))
                # warna kolom Jenis
                elif key == "jenis":
                    item.setBackground(jenis_colors.get(str(val).upper(), QColor("#FFFFFF")))

                self._table.setItem(row_idx, col_idx, item)

        # baris TOTAL
        total_row = len(records)
        total_font = QFont()
        total_font.setBold(True)
        for col_idx, (_, key) in enumerate(cols):
            if key == "kota_kab":
                text = "TOTAL DO"
            elif key == "tonase_total":
                text = f"{data['total_ton']:,.2f}"
            elif key == "shift":
                text = str(data["total_do"])
            else:
                text = ""
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setBackground(QColor("#FFF176"))
            item.setFont(total_font)
            self._table.setItem(total_row, col_idx, item)

        self._table.resizeColumnsToContents()

        # --- render kedua grafik ---
        daily = data["daily_stats"]
        date_labels = [
            d["tgl"].strftime("%d/%m/%y") if hasattr(d["tgl"], "strftime") else str(d["tgl"])
            for d in daily
        ]
        self._render_shift_do_chart(daily, date_labels, tgl_awal, tgl_akhir)
        self._render_shift_ton_chart(daily, date_labels, tgl_awal, tgl_akhir)
        self._render_trend_chart(daily, date_labels, tgl_awal, tgl_akhir)

    def _render_shift_do_chart(self, daily: list, labels: list, tgl_awal, tgl_akhir):
        """Grafik bar: DO Count per Shift (SHIFT 1 biru, SHIFT 2 abu, SHIFT 3 oranye)."""
        chart = self._chart_shift_do
        chart.removeAllSeries()
        for ax in chart.axes():
            chart.removeAxis(ax)

        tgl_str = f"{tgl_awal.strftime('%d/%m/%y')} – {tgl_akhir.strftime('%d/%m/%y')}"
        chart.setTitle(f"DO COUNT PER SHIFT\n{tgl_str}")
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        chart.setTitleFont(f)

        set_s1 = QBarSet("SHIFT 1")
        set_s1.setColor(QColor("#2196F3"))
        set_s2 = QBarSet("SHIFT 2")
        set_s2.setColor(QColor("#9E9E9E"))
        set_s3 = QBarSet("SHIFT 3")
        set_s3.setColor(QColor("#FF9800"))

        for d in daily:
            set_s1.append(d["shift_1_do"])
            set_s2.append(d["shift_2_do"])
            set_s3.append(d["shift_3_do"])

        series = QBarSeries()
        series.append(set_s1)
        series.append(set_s2)
        series.append(set_s3)
        series.setLabelsVisible(True)
        series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        lf = QFont(); lf.setPointSize(8)
        axis_x.setLabelsFont(lf)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Jumlah DO")
        tf = QFont(); tf.setPointSize(9)
        axis_y.setTitleFont(tf)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

    def _render_shift_ton_chart(self, daily: list, labels: list, tgl_awal, tgl_akhir):
        """Grafik bar: Tonase per Shift (SHIFT 1 merah, SHIFT 2 kuning, SHIFT 3 coklat)."""
        chart = self._chart_shift_ton
        chart.removeAllSeries()
        for ax in chart.axes():
            chart.removeAxis(ax)

        tgl_str = f"{tgl_awal.strftime('%d/%m/%y')} – {tgl_akhir.strftime('%d/%m/%y')}"
        chart.setTitle(f"TONASE PER SHIFT\n{tgl_str}")
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        chart.setTitleFont(f)

        set_s1 = QBarSet("SHIFT 1 QTY")
        set_s1.setColor(QColor("#F44336"))
        set_s2 = QBarSet("SHIFT 2 QTY")
        set_s2.setColor(QColor("#FFEB3B"))
        set_s3 = QBarSet("SHIFT 3 QTY")
        set_s3.setColor(QColor("#795548"))

        for d in daily:
            set_s1.append(d["shift_1_ton"])
            set_s2.append(d["shift_2_ton"])
            set_s3.append(d["shift_3_ton"])

        series = QBarSeries()
        series.append(set_s1)
        series.append(set_s2)
        series.append(set_s3)
        series.setLabelsVisible(True)
        series.setLabelsPosition(QBarSeries.LabelsPosition.LabelsOutsideEnd)

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        lf = QFont(); lf.setPointSize(8)
        axis_x.setLabelsFont(lf)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Tonase (kg)")
        tf = QFont(); tf.setPointSize(9)
        axis_y.setTitleFont(tf)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

    def _render_trend_chart(self, daily: list, labels: list, tgl_awal, tgl_akhir):
        """Grafik line: total DO per hari dengan label nilai merah di setiap titik."""
        chart = self._chart_trend
        chart.removeAllSeries()
        for ax in chart.axes():
            chart.removeAxis(ax)

        tgl_str = f"{tgl_awal.strftime('%d/%m/%y')} – {tgl_akhir.strftime('%d/%m/%y')}"
        chart.setTitle(f"TREND DELIVERY GRAPH\n{tgl_str}")
        f = QFont()
        f.setPointSize(11)
        f.setBold(True)
        chart.setTitleFont(f)

        series = QLineSeries()
        series.setName("Total DO")
        pen = QPen(QColor("#1565C0"))
        pen.setWidth(2)
        series.setPen(pen)

        for i, d in enumerate(daily):
            series.append(i, d["total_do"])

        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        lf = QFont(); lf.setPointSize(9)
        axis_x.setLabelsFont(lf)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        all_do = [d["total_do"] for d in daily]
        max_do = max(all_do) if all_do else 10
        axis_y = QValueAxis()
        axis_y.setRange(0, max_do * 1.25)
        axis_y.setTickCount(6)
        tf = QFont(); tf.setPointSize(9)
        axis_y.setTitleFont(tf)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        # Tampilkan label nilai di setiap titik (merah & tebal)
        series.setPointLabelsVisible(True)
        series.setPointLabelsColor(QColor("#E53935"))
        lbl_font = QFont()
        lbl_font.setPointSize(9)
        lbl_font.setBold(True)
        series.setPointLabelsFont(lbl_font)
        series.setPointLabelsFormat("@yPoint")

        chart.legend().hide()

    # ------------------------------------------------------------------
    # Report renderers (existing)
    # ------------------------------------------------------------------

    def _show_harian(self, tgl: date):
        data = ReportGenerator.daily_report(tgl)
        self._last_data = data

        total = data["total"]
        self._update_cards(total["count_do"], total["total_tonase"], total["avg_lead_time"])

        cols = _COLUMNS["Harian"]
        rows = [
            {"shift": "Shift 1", **data["shift_1"]},
            {"shift": "Shift 2", **data["shift_2"]},
            {"shift": "Shift 3", **data["shift_3"]},
            {"shift": "TOTAL", **total},
        ]
        self._fill_table(cols, rows, total_row_idx=3)

    def _show_mingguan(self, tgl_awal: date, tgl_akhir: date):
        rows = ReportGenerator.weekly_report(tgl_awal, tgl_akhir)
        self._last_data = rows

        total_do = sum(r["total_do"] for r in rows)
        total_ton = sum(r["total_tonase"] for r in rows)
        avg_lt = sum(r["avg_lead_time"] * r["total_do"] for r in rows) / total_do if total_do else 0.0
        self._update_cards(total_do, total_ton, avg_lt)

        cols = _COLUMNS["Mingguan"]
        self._fill_table(cols, rows)

    def _show_bulanan(self, tahun: int, bulan: int):
        data = ReportGenerator.monthly_report(tahun, bulan)
        self._last_data = data

        self._update_cards(data["total_do"], data["total_tonase"], data["avg_lead_time"])

        cols = _COLUMNS["Bulanan"]
        self._fill_table(cols, data["per_customer"])

    def _show_customer(self, tgl_awal: date, tgl_akhir: date):
        rows = ReportGenerator.customer_report(tgl_awal, tgl_akhir)
        self._last_data = rows

        total_do = sum(r["count_do"] for r in rows)
        total_ton = sum(r["total_tonase"] for r in rows)
        avg_lt = sum(r["avg_lead_time"] * r["count_do"] for r in rows) / total_do if total_do else 0.0
        self._update_cards(total_do, total_ton, avg_lt)

        cols = _COLUMNS["Per Customer"]
        self._fill_table(cols, rows)

    def _show_ekspedisi(self, tgl_awal: date, tgl_akhir: date):
        rows = ReportGenerator.expedition_report(tgl_awal, tgl_akhir)
        self._last_data = rows

        total_do = sum(r["count_do"] for r in rows)
        total_ton = sum(r["total_tonase"] for r in rows)
        avg_lt = sum(r["avg_lead_time"] * r["count_do"] for r in rows) / total_do if total_do else 0.0
        self._update_cards(total_do, total_ton, avg_lt)

        cols = _COLUMNS["Per Ekspedisi"]
        self._fill_table(cols, rows)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_cards(self, count_do: int, total_tonase: float, avg_lt: float):
        self._card_do.set_value(str(count_do))
        self._card_tonase.set_value(f"{total_tonase:,.1f} kg")
        self._card_lt.set_value(_fmt_lt(avg_lt))

    def _fill_table(self, cols: list[tuple[str, str]], rows: list[dict], total_row_idx: int = -1):
        self._table.clear()
        self._table.setColumnCount(len(cols))
        self._table.setRowCount(len(rows))
        self._table.setHorizontalHeaderLabels([c[0] for c in cols])

        for row_idx, row in enumerate(rows):
            for col_idx, (_, key) in enumerate(cols):
                val = row.get(key, "")
                if isinstance(val, float):
                    if "lead_time" in key or "avg_lt" in key:
                        text = _fmt_lt(val)
                    else:
                        text = f"{val:,.2f}"
                elif isinstance(val, int):
                    text = str(val)
                else:
                    text = str(val) if val is not None else "—"

                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if row_idx == total_row_idx:
                    item.setBackground(QColor("#dbeafe"))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self._table.setItem(row_idx, col_idx, item)

        self._table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Export actions
    # ------------------------------------------------------------------

    def _export_excel(self):
        if self._last_data is None or not self._last_type:
            QMessageBox.warning(self, "Export Excel", "Generate laporan terlebih dahulu.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Excel",
            f"Laporan_{self._last_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not filepath:
            return
        try:
            export_report_to_excel(self._last_data, self._last_type, filepath)
            QMessageBox.information(self, "Export Excel", f"File berhasil disimpan:\n{filepath}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Excel", f"Gagal export:\n{exc}")

    def _export_pdf(self):
        if self._last_data is None or not self._last_type:
            QMessageBox.warning(self, "Export PDF", "Generate laporan terlebih dahulu.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan PDF",
            f"Laporan_{self._last_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)",
        )
        if not filepath:
            return
        try:
            export_report_to_pdf(self._last_data, self._last_type, _COMPANY_NAME, filepath)
            QMessageBox.information(self, "Export PDF", f"File berhasil disimpan:\n{filepath}")
        except Exception as exc:
            QMessageBox.critical(self, "Export PDF", f"Gagal export:\n{exc}")

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def refresh(self):
        self._generate()
