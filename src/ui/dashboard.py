from datetime import date

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from peewee import fn

from src.core.models import DORecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_date(val) -> date:
    """Normalise a Peewee DateField value (may arrive as date or ISO string)."""
    if isinstance(val, date):
        return val
    return date.fromisoformat(str(val))


def _date_label(val) -> str:
    return _to_date(val).strftime("%d/%m")


def _drop_shadow(widget: QWidget, blur: int = 14, dy: int = 3, alpha: int = 35):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, dy)
    shadow.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(shadow)


# ---------------------------------------------------------------------------
# Summary Card
# ---------------------------------------------------------------------------

class _SummaryCard(QFrame):
    def __init__(self, title: str, icon: str, accent: str, parent=None):
        super().__init__(parent)
        self._accent = accent
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 10px;
                border: 1px solid #E2E8F0;
                border-left: 4px solid #059669;
            }
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(115)
        _drop_shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        # -- header row --
        header = QHBoxLayout()
        header.setSpacing(8)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 22px; color: {accent}; border: none;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600; border: none;")
        header.addWidget(icon_lbl)
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        # -- big value --
        self._value_lbl = QLabel("—")
        self._value_lbl.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #0F172A; border: none;"
        )
        layout.addWidget(self._value_lbl)

        # -- subtitle --
        self._sub_lbl = QLabel("")
        self._sub_lbl.setStyleSheet("color: #64748B; font-size: 11px; border: none;")
        layout.addWidget(self._sub_lbl)

    def set_value(self, value: str, subtitle: str = ""):
        self._value_lbl.setText(value)
        self._sub_lbl.setText(subtitle)


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _chart_frame(chart_view: QChartView) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
    _drop_shadow(frame, blur=10, dy=2, alpha=25)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(6, 6, 6, 6)
    layout.addWidget(chart_view)
    return frame


def _make_chart(title: str, animate: bool = True) -> QChart:
    chart = QChart()
    chart.setTitle(title)
    chart.setTitleFont(_label_font(11, bold=True))
    chart.setBackgroundVisible(False)
    chart.setPlotAreaBackgroundVisible(False)
    if animate:
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
    return chart


def _make_view(chart: QChart) -> QChartView:
    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setStyleSheet("background: transparent;")
    return view


def _label_font(size: int = 10, bold: bool = False):
    from PySide6.QtGui import QFont
    f = QFont()
    f.setPointSize(size)
    f.setBold(bold)
    return f


# ---------------------------------------------------------------------------
# DashboardWidget
# ---------------------------------------------------------------------------

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._building = True
        self._build_ui()
        self._building = False
        self.refresh()

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

        vbox.addLayout(self._build_cards_row())
        vbox.addWidget(self._build_filter_row())
        vbox.addLayout(self._build_row3())
        vbox.addLayout(self._build_row4())
        vbox.addStretch()

        scroll.setWidget(inner)
        root.addWidget(scroll)

    def _build_cards_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(16)
        self._card_do = _SummaryCard("Total DO", "📦", "#3b82f6")
        self._card_tonase = _SummaryCard("Total Tonase", "⚖️", "#10b981")
        self._card_leadtime = _SummaryCard("Rata-rata Lead Time", "⏱️", "#f59e0b")
        for card in (self._card_do, self._card_tonase, self._card_leadtime):
            row.addWidget(card)
        return row

    def _build_filter_row(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        _drop_shadow(frame, blur=8, dy=2, alpha=20)

        row = QHBoxLayout(frame)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(10)

        lbl_style = "color: #0F172A; font-size: 12px; font-weight: 600;"

        dari_lbl = QLabel("Dari:")
        dari_lbl.setStyleSheet(lbl_style)
        row.addWidget(dari_lbl)

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("dd/MM/yyyy")
        row.addWidget(self._date_from)

        sampai_lbl = QLabel("Sampai:")
        sampai_lbl.setStyleSheet(lbl_style)
        row.addWidget(sampai_lbl)

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("dd/MM/yyyy")
        row.addWidget(self._date_to)

        self._combo_preset = QComboBox()
        self._combo_preset.addItems(["7 Hari", "30 Hari", "90 Hari", "Custom"])
        self._combo_preset.setFixedWidth(110)
        row.addWidget(self._combo_preset)

        row.addStretch()

        # defaults: ambil dari range data di DB, fallback 30 hari
        today = QDate.currentDate()
        try:
            db_first = DORecord.select(fn.MIN(DORecord.tgl)).scalar()
            db_last = DORecord.select(fn.MAX(DORecord.tgl)).scalar()
            if db_first and db_last:
                self._date_from.setDate(QDate(db_first.year, db_first.month, db_first.day))
                self._date_to.setDate(QDate(db_last.year, db_last.month, db_last.day))
            else:
                self._date_to.setDate(today)
                self._date_from.setDate(today.addDays(-29))
        except Exception:
            self._date_to.setDate(today)
            self._date_from.setDate(today.addDays(-29))
        self._combo_preset.setCurrentText("Custom")

        self._combo_preset.currentTextChanged.connect(self._on_preset_changed)
        self._date_from.dateChanged.connect(self._on_custom_date_changed)
        self._date_to.dateChanged.connect(self._on_custom_date_changed)

        return frame

    def _build_row3(self) -> QHBoxLayout:
        # Lead time bar (60%) | Shift pie (40%)
        row = QHBoxLayout()
        row.setSpacing(16)

        self._chart_lt = _make_chart("Lead Time Rata-rata per Hari")
        self._view_lt = _make_view(self._chart_lt)
        left = _chart_frame(self._view_lt)
        left.setMinimumHeight(280)

        self._chart_shift = _make_chart("Distribusi Shift")
        self._view_shift = _make_view(self._chart_shift)
        right = _chart_frame(self._view_shift)
        right.setMinimumHeight(280)

        row.addWidget(left, 60)
        row.addWidget(right, 40)
        return row

    def _build_row4(self) -> QHBoxLayout:
        # Tonase line (60%) | Top customer table (40%)
        row = QHBoxLayout()
        row.setSpacing(16)

        self._chart_tonase = _make_chart("Tren Tonase per Hari")
        self._view_tonase = _make_view(self._chart_tonase)
        left = _chart_frame(self._view_tonase)
        left.setMinimumHeight(280)

        # --- tabel top 10 customer ---
        right = QFrame()
        right.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 10px; border: 1px solid #E2E8F0; }")
        _drop_shadow(right, blur=10, dy=2, alpha=25)
        right.setMinimumHeight(280)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(12, 10, 12, 10)
        right_lay.setSpacing(6)

        title_lbl = QLabel("Top 10 Customer (Tonase)")
        title_lbl.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #0F172A; border: none;"
        )
        right_lay.addWidget(title_lbl)

        self._tbl_customer = QTableWidget()
        self._tbl_customer.setColumnCount(2)
        self._tbl_customer.setHorizontalHeaderLabels(["Customer", "Tonase (kg)"])
        self._tbl_customer.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl_customer.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._tbl_customer.setShowGrid(True)
        self._tbl_customer.verticalHeader().setVisible(False)
        self._tbl_customer.verticalHeader().setDefaultSectionSize(22)
        self._tbl_customer.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._tbl_customer.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tbl_customer.setStyleSheet("""
            QTableWidget {
                border: none;
                font-size: 11px;
                gridline-color: #E2E8F0;
            }
            QHeaderView::section {
                background-color: #F1F5F9;
                color: #059669;
                font-weight: 600;
                font-size: 11px;
                padding: 4px;
                border-bottom: 2px solid #059669;
                border-right: 1px solid #E2E8F0;
            }
            QTableWidget::item:alternate { background-color: #F8FAFC; }
        """)
        self._tbl_customer.setAlternatingRowColors(True)
        right_lay.addWidget(self._tbl_customer)

        row.addWidget(left, 60)
        row.addWidget(right, 40)
        return row

    # ------------------------------------------------------------------
    # Filter slots
    # ------------------------------------------------------------------

    def _on_preset_changed(self, text: str):
        if self._building:
            return
        today = QDate.currentDate()
        self._date_from.blockSignals(True)
        self._date_to.blockSignals(True)

        if text == "7 Hari":
            self._date_from.setDate(today.addDays(-6))
            self._date_to.setDate(today)
        elif text == "30 Hari":
            self._date_from.setDate(today.addDays(-29))
            self._date_to.setDate(today)
        elif text == "90 Hari":
            self._date_from.setDate(today.addDays(-89))
            self._date_to.setDate(today)

        self._date_from.blockSignals(False)
        self._date_to.blockSignals(False)

        if text != "Custom":
            self._load_data()

    def _on_custom_date_changed(self):
        if self._building:
            return
        self._combo_preset.blockSignals(True)
        self._combo_preset.setCurrentText("Custom")
        self._combo_preset.blockSignals(False)
        self._load_data()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh(self):
        self._load_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _date_range(self) -> tuple[date, date]:
        return self._date_from.date().toPython(), self._date_to.date().toPython()

    def _load_data(self):
        d_from, d_to = self._date_range()

        # --- cards ---
        do_total = (
            DORecord.select(fn.COUNT(DORecord.id))
            .where(DORecord.tgl.between(d_from, d_to))
            .scalar() or 0
        )
        self._card_do.set_value(
            str(do_total),
            f"{d_from.strftime('%d %b')} – {d_to.strftime('%d %b %Y')}",
        )

        total_tonase = (
            DORecord.select(fn.SUM(DORecord.tonase_total))
            .where(DORecord.tgl.between(d_from, d_to))
            .scalar() or 0.0
        )
        self._card_tonase.set_value(
            f"{total_tonase:,.1f} kg",
            f"{d_from.strftime('%d %b')} – {d_to.strftime('%d %b %Y')}",
        )

        avg_lt = (
            DORecord.select(fn.AVG(DORecord.lead_time_menit))
            .where(DORecord.tgl.between(d_from, d_to))
            .scalar() or 0.0
        )
        h, m = divmod(int(avg_lt), 60)
        lt_str = f"{h}j {m}m" if h else f"{m} mnt"
        self._card_leadtime.set_value(lt_str, f"Rata-rata {avg_lt:.0f} menit")

        # --- aggregate per day ---
        daily = list(
            DORecord.select(
                DORecord.tgl,
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
                fn.SUM(DORecord.tonase_roll).alias("sum_roll"),
                fn.SUM(DORecord.tonase_sheet).alias("sum_sheet"),
            )
            .where(DORecord.tgl.between(d_from, d_to))
            .group_by(DORecord.tgl)
            .order_by(DORecord.tgl)
            .namedtuples()
        )

        # --- shift distribution ---
        shifts = list(
            DORecord.select(
                DORecord.shift,
                fn.COUNT(DORecord.id).alias("cnt"),
            )
            .where(DORecord.tgl.between(d_from, d_to))
            .group_by(DORecord.shift)
            .order_by(DORecord.shift)
            .namedtuples()
        )

        # --- top 10 customer ---
        customers = list(
            DORecord.select(
                DORecord.customer,
                fn.SUM(DORecord.tonase_total).alias("total"),
            )
            .where(DORecord.tgl.between(d_from, d_to))
            .group_by(DORecord.customer)
            .order_by(fn.SUM(DORecord.tonase_total).desc())
            .limit(10)
            .namedtuples()
        )

        self._render_leadtime_chart(daily)
        self._render_shift_chart(shifts)
        self._render_tonase_chart(daily)
        self._render_customer_table(customers)

    # ------------------------------------------------------------------
    # Chart renderers
    # ------------------------------------------------------------------

    def _clear_chart(self, chart: QChart):
        chart.removeAllSeries()
        for ax in chart.axes():
            chart.removeAxis(ax)

    def _render_leadtime_chart(self, rows):
        chart = self._chart_lt
        self._clear_chart(chart)

        if not rows:
            return

        bar_set = QBarSet("Lead Time (mnt)")
        bar_set.setColor(QColor("#3b82f6"))
        categories = []

        for r in rows:
            categories.append(_date_label(r.tgl))
            bar_set.append(float(r.avg_lt or 0))

        series = QBarSeries()
        series.append(bar_set)
        chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsFont(_label_font(8))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Menit")
        axis_y.setTitleFont(_label_font(9))
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().hide()

    def _render_shift_chart(self, rows):
        chart = self._chart_shift
        self._clear_chart(chart)

        series = QPieSeries()
        _shift_colors = {1: "#3b82f6", 2: "#10b981", 3: "#f59e0b"}
        _shift_labels = {1: "Shift 1", 2: "Shift 2", 3: "Shift 3"}

        total = sum(r.cnt for r in rows) or 1
        for r in rows:
            shift = r.shift or 0
            label = _shift_labels.get(shift, f"Shift {shift}")
            pct = r.cnt / total * 100
            slc = series.append(f"{label}\n{pct:.1f}%", r.cnt)
            slc.setColor(QColor(_shift_colors.get(shift, "#94a3b8")))
            slc.setLabelVisible(True)

        chart.addSeries(series)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

    def _render_tonase_chart(self, rows):
        chart = self._chart_tonase
        self._clear_chart(chart)

        if not rows:
            return

        series_roll = QLineSeries()
        series_roll.setName("Tonase Roll")
        pen_roll = QPen(QColor("#3b82f6"))
        pen_roll.setWidth(2)
        series_roll.setPen(pen_roll)

        series_sheet = QLineSeries()
        series_sheet.setName("Tonase Sheet")
        pen_sheet = QPen(QColor("#10b981"))
        pen_sheet.setWidth(2)
        series_sheet.setPen(pen_sheet)

        categories = []
        max_roll_val = 0.0
        max_sheet_val = 0.0
        for i, r in enumerate(rows):
            categories.append(_date_label(r.tgl))
            rv = float(r.sum_roll or 0)
            sv = float(r.sum_sheet or 0)
            series_roll.append(i, rv)
            series_sheet.append(i, sv)
            max_roll_val = max(max_roll_val, rv)
            max_sheet_val = max(max_sheet_val, sv)

        chart.addSeries(series_roll)
        chart.addSeries(series_sheet)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsFont(_label_font(8))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series_roll.attachAxis(axis_x)
        series_sheet.attachAxis(axis_x)

        # --- Left Y-axis (Roll) ---
        axis_y_roll = QValueAxis()
        axis_y_roll.setTitleText("Roll (kg)")
        axis_y_roll.setTitleFont(_label_font(9))
        axis_y_roll.setLabelFormat("%.0f")
        axis_y_roll.setRange(0, max_roll_val * 1.1)
        chart.addAxis(axis_y_roll, Qt.AlignmentFlag.AlignLeft)
        series_roll.attachAxis(axis_y_roll)

        # --- Right Y-axis (Sheet) ---
        axis_y_sheet = QValueAxis()
        axis_y_sheet.setTitleText("Sheet (kg)")
        axis_y_sheet.setTitleFont(_label_font(9))
        axis_y_sheet.setLabelFormat("%.0f")
        axis_y_sheet.setRange(0, max(max_sheet_val * 1.1, 1.0))
        chart.addAxis(axis_y_sheet, Qt.AlignmentFlag.AlignRight)
        series_sheet.attachAxis(axis_y_sheet)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

    def _render_customer_table(self, rows):
        tbl = self._tbl_customer
        tbl.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            name = str(r.customer) if r.customer else "—"
            tonase = float(r.total or 0)
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_ton = QTableWidgetItem(f"{tonase:,.2f}")
            item_ton.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tbl.setItem(row_idx, 0, item_name)
            tbl.setItem(row_idx, 1, item_ton)

