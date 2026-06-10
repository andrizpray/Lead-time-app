from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import (
    QAbstractTableModel,
    QDate,
    QModelIndex,
    Qt,
    QTimer,
)
from PySide6.QtGui import QColor

from PySide6.QtWidgets import QFileDialog

from src.ui.do_form import DOFormDialog
from src.utils.excel_exporter import export_table_to_excel


# ─────────────────────────────────────────────────────────────────────────────
class DORecordTableModel(QAbstractTableModel):
    COLUMNS: list[tuple[str, str | None]] = [
        ("No",              None),
        ("Tgl",             "tgl"),
        ("No DO",           "no_do"),
        ("No Shipment",     "no_shipment"),
        ("Customer",        "customer"),
        ("Kota",            "kota_kab"),
        ("Jenis",           "jenis"),
        ("Ekspedisi",       "ekspedisi"),
        ("Truk",            "jenis_truk"),
        ("Loading Mulai",   "loading_mulai"),
        ("Loading Selesai", "loading_selesai"),
        ("Lead Time",       "lead_time_menit"),
        ("Tonase Roll",     "tonase_roll"),
        ("Tonase Sheet",    "tonase_sheet"),
        ("Tonase Total",    "tonase_total"),
        ("Shift",           "shift"),
    ]

    _CENTER_COLS = frozenset({0, 6, 11, 15})
    _RIGHT_COLS  = frozenset({12, 13, 14})
    _HIGHLIGHT   = QColor("#fef9c3")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._records: list = []
        self._page_offset: int = 0
        self._dup_no_do: set[str] = set()

    # ── public ────────────────────────────────────────────────────────────
    def load(
        self,
        records: list,
        page_offset: int = 0,
        dup_no_do: set[str] | None = None,
    ) -> None:
        self.beginResetModel()
        self._records = records
        self._page_offset = page_offset
        self._dup_no_do = dup_no_do if dup_no_do is not None else set()
        self.endResetModel()

    def get_record(self, row: int):
        return self._records[row]

    # ── QAbstractTableModel ───────────────────────────────────────────────
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._records)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._records):
            return None
        record = self._records[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._cell_text(record, col, self._page_offset + row)

        if role == Qt.ItemDataRole.BackgroundRole:
            if record.no_do in self._dup_no_do:
                return self._HIGHLIGHT

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in self._CENTER_COLS:
                return int(Qt.AlignmentFlag.AlignCenter)
            if col in self._RIGHT_COLS:
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.COLUMNS[section][0]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        pass  # DB-level sort handled by DOTableWidget.refresh()

    # ── helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _cell_text(record, col: int, abs_row: int) -> str:
        if col == 0:
            return str(abs_row + 1)
        field = DORecordTableModel.COLUMNS[col][1]
        val = getattr(record, field)
        if val is None:
            return ""
        if col == 1:  # tgl
            return val.strftime("%d/%m/%Y") if isinstance(val, date) else str(val)
        if col in (9, 10):  # loading_mulai / loading_selesai  → "HH:MM"
            s = str(val)
            return s[:5] if len(s) >= 5 else s
        if col in (12, 13, 14):  # tonase
            return f"{float(val):.2f}"
        return str(val)


# ─────────────────────────────────────────────────────────────────────────────
class DOTableWidget(QWidget):
    _PAGE_SIZES = ("50", "100", "200")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_page = 0
        self._total_pages = 1
        self._sort_column = 1  # Tgl
        self._sort_order = Qt.SortOrder.AscendingOrder

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)
        self._debounce.timeout.connect(self._apply_filters)

        self._build_ui()
        self.refresh()

    # ── UI construction ───────────────────────────────────────────────────
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        root.addLayout(self._make_toolbar())
        root.addWidget(self._make_filter_panel())
        root.addWidget(self._make_table())
        root.addLayout(self._make_pagination())

        # Connect sort signal after all UI elements are created
        self._view.horizontalHeader().sortIndicatorChanged.connect(self._on_sort_changed)

    def _make_toolbar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)

        self._btn_refresh = QPushButton("↻ Refresh")
        self._btn_add     = QPushButton("+ Tambah DO")
        self._btn_edit    = QPushButton("✎ Edit")
        self._btn_delete  = QPushButton("✕ Hapus")
        self._btn_export  = QPushButton("⬇ Export Excel")

        self._btn_edit.setEnabled(False)
        self._btn_delete.setEnabled(False)

        for btn in (self._btn_refresh, self._btn_add, self._btn_edit, self._btn_delete):
            btn.setFixedHeight(32)
            layout.addWidget(btn)

        self._btn_delete.setStyleSheet(
            "QPushButton { color: #dc2626; }"
            "QPushButton:hover { background: #450a0a; }"
            "QPushButton:disabled { color: #94a3b8; }"
        )

        self._btn_export.setFixedHeight(32)
        self._btn_export.setStyleSheet(
            "QPushButton { color: #ffffff; background-color: #10b981; border-radius: 4px; padding: 0 10px; }"
            "QPushButton:hover { background-color: #059669; }"
            "QPushButton:pressed { background-color: #047857; }"
        )
        layout.addWidget(self._btn_export)

        layout.addStretch()

        self._btn_refresh.clicked.connect(self.refresh)
        self._btn_add.clicked.connect(self._on_add)
        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_delete.clicked.connect(self._on_delete)
        self._btn_export.clicked.connect(self._on_export_excel)

        return layout

    def _make_filter_panel(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("filterFrame")
        frame.setStyleSheet(
            "#filterFrame {"
            "  border: 1px solid #2a2a4a;"
            "  border-radius: 6px;"
            "}"
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        today = QDate.currentDate()

        self._date_from = QDateEdit(QDate(today.year(), today.month(), 1))
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("dd/MM/yyyy")
        self._date_from.setFixedWidth(110)

        self._date_to = QDateEdit(today)
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("dd/MM/yyyy")
        self._date_to.setFixedWidth(110)

        self._filter_customer = QLineEdit()
        self._filter_customer.setPlaceholderText("Customer")
        self._filter_customer.setFixedWidth(130)
        self._filter_customer.setClearButtonEnabled(True)

        self._filter_shift = QComboBox()
        self._filter_shift.addItems(["All", "1", "2", "3"])
        self._filter_shift.setFixedWidth(65)

        self._filter_jenis = QComboBox()
        self._filter_jenis.addItems(["All", "ROLL", "SHEET"])
        self._filter_jenis.setFixedWidth(75)

        self._search_bar = QLineEdit()
        self._search_bar.setPlaceholderText("Cari No DO / Shipment / Customer…")
        self._search_bar.setClearButtonEnabled(True)
        self._search_bar.setFixedWidth(210)

        btn_reset = QPushButton("Reset")
        btn_reset.setFixedWidth(58)
        btn_reset.clicked.connect(self._reset_filters)

        layout.addWidget(QLabel("Tgl:"))
        layout.addWidget(self._date_from)
        layout.addWidget(QLabel("s/d"))
        layout.addWidget(self._date_to)
        layout.addSpacing(4)
        layout.addWidget(QLabel("Customer:"))
        layout.addWidget(self._filter_customer)
        layout.addWidget(QLabel("Shift:"))
        layout.addWidget(self._filter_shift)
        layout.addWidget(QLabel("Jenis:"))
        layout.addWidget(self._filter_jenis)
        layout.addSpacing(4)
        layout.addWidget(QLabel("Cari:"))
        layout.addWidget(self._search_bar)
        layout.addWidget(btn_reset)
        layout.addStretch()

        self._date_from.dateChanged.connect(self._debounce.start)
        self._date_to.dateChanged.connect(self._debounce.start)
        self._filter_customer.textChanged.connect(self._debounce.start)
        self._filter_shift.currentTextChanged.connect(self._debounce.start)
        self._filter_jenis.currentTextChanged.connect(self._debounce.start)
        self._search_bar.textChanged.connect(self._debounce.start)

        return frame

    def _make_table(self) -> QTableView:
        self._model = DORecordTableModel(self)

        self._view = QTableView()
        self._view.setModel(self._model)
        self._view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._view.setAlternatingRowColors(True)
        self._view.setSortingEnabled(True)
        self._view.setWordWrap(False)
        self._view.verticalHeader().setVisible(False)
        self._view.verticalHeader().setDefaultSectionSize(26)

        hdr = self._view.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setStretchLastSection(True)

        col_widths = [40, 90, 100, 110, 150, 100, 60, 120, 80, 90, 95, 70, 85, 90, 90, 50]
        for i, w in enumerate(col_widths):
            self._view.setColumnWidth(i, w)

        self._view.doubleClicked.connect(self._on_double_click)
        self._view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        return self._view

    def _make_pagination(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)

        layout.addWidget(QLabel("Rows:"))
        self._page_size = QComboBox()
        self._page_size.addItems(self._PAGE_SIZES)
        self._page_size.setCurrentText("50")
        self._page_size.setFixedWidth(65)
        self._page_size.currentTextChanged.connect(self._on_page_size_changed)
        layout.addWidget(self._page_size)

        layout.addSpacing(8)

        self._btn_prev = QPushButton("< Prev")
        self._btn_prev.setFixedWidth(68)
        self._btn_prev.setEnabled(False)
        self._btn_prev.clicked.connect(self._prev_page)
        layout.addWidget(self._btn_prev)

        self._page_label = QLabel("Page 1 of 1")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setFixedWidth(150)
        layout.addWidget(self._page_label)

        self._btn_next = QPushButton("Next >")
        self._btn_next.setFixedWidth(68)
        self._btn_next.setEnabled(False)
        self._btn_next.clicked.connect(self._next_page)
        layout.addWidget(self._btn_next)

        layout.addStretch()

        self._total_label = QLabel("0 records")
        self._total_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self._total_label)

        return layout

    # ── data loading ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        try:
            self._load_data()
        except Exception as exc:
            QMessageBox.critical(self, "Error Database", f"Gagal memuat data:\n{exc}")

    def _load_data(self) -> None:
        from src.core.models import DORecord
        from peewee import fn

        q = self._build_query()
        total = q.count()

        # no_do values that appear more than once in the filtered result set
        dup_q = (
            q.select(DORecord.no_do)
            .group_by(DORecord.no_do)
            .having(fn.COUNT(DORecord.id) > 1)
        )
        dup_no_do = {r.no_do for r in dup_q}

        page_size = int(self._page_size.currentText())
        self._total_pages = max(1, (total + page_size - 1) // page_size)
        if self._current_page >= self._total_pages:
            self._current_page = self._total_pages - 1

        sort_field_name = DORecordTableModel.COLUMNS[self._sort_column][1]
        sort_attr = (
            getattr(DORecord, sort_field_name) if sort_field_name else DORecord.id
        )
        if self._sort_order == Qt.SortOrder.AscendingOrder:
            q = q.order_by(sort_attr.asc())
        else:
            q = q.order_by(sort_attr.desc())

        offset = self._current_page * page_size
        records = list(q.offset(offset).limit(page_size))

        self._model.load(records, page_offset=offset, dup_no_do=dup_no_do)
        self._update_pagination_ui(total)

    def _build_query(self):
        from src.core.models import DORecord

        q = DORecord.select()

        q = q.where(DORecord.tgl >= self._date_from.date().toString("yyyy-MM-dd"))
        q = q.where(DORecord.tgl <= self._date_to.date().toString("yyyy-MM-dd"))

        customer = self._filter_customer.text().strip()
        if customer:
            q = q.where(DORecord.customer.contains(customer))

        shift_text = self._filter_shift.currentText()
        if shift_text != "All":
            q = q.where(DORecord.shift == int(shift_text))

        jenis_text = self._filter_jenis.currentText()
        if jenis_text != "All":
            q = q.where(DORecord.jenis == jenis_text)

        search = self._search_bar.text().strip()
        if search:
            q = q.where(
                DORecord.no_do.contains(search)
                | DORecord.no_shipment.contains(search)
                | DORecord.customer.contains(search)
            )

        return q

    def _update_pagination_ui(self, total: int) -> None:
        self._page_label.setText(f"Page {self._current_page + 1} of {self._total_pages}")
        self._total_label.setText(f"{total:,} records")
        self._btn_prev.setEnabled(self._current_page > 0)
        self._btn_next.setEnabled(self._current_page < self._total_pages - 1)

    # ── filter / pagination slots ─────────────────────────────────────────
    def _apply_filters(self) -> None:
        self._current_page = 0
        self.refresh()

    def _reset_filters(self) -> None:
        today = QDate.currentDate()
        # Block signals while resetting to fire debounce only once at the end
        for w in (
            self._date_from, self._date_to,
            self._filter_customer, self._filter_shift,
            self._filter_jenis, self._search_bar,
        ):
            w.blockSignals(True)

        self._date_from.setDate(QDate(today.year(), today.month(), 1))
        self._date_to.setDate(today)
        self._filter_customer.clear()
        self._filter_shift.setCurrentIndex(0)
        self._filter_jenis.setCurrentIndex(0)
        self._search_bar.clear()

        for w in (
            self._date_from, self._date_to,
            self._filter_customer, self._filter_shift,
            self._filter_jenis, self._search_bar,
        ):
            w.blockSignals(False)

        self._apply_filters()

    def _on_page_size_changed(self) -> None:
        self._current_page = 0
        self.refresh()

    def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self.refresh()

    def _next_page(self) -> None:
        if self._current_page < self._total_pages - 1:
            self._current_page += 1
            self.refresh()

    def _on_sort_changed(self, col: int, order: Qt.SortOrder) -> None:
        self._sort_column = col
        self._sort_order = order
        self._current_page = 0
        self.refresh()

    def _on_selection_changed(self) -> None:
        has_sel = bool(self._view.selectionModel().selectedRows())
        self._btn_edit.setEnabled(has_sel)
        self._btn_delete.setEnabled(has_sel)

    # ── CRUD actions ──────────────────────────────────────────────────────
    def _on_add(self) -> None:
        dlg = DOFormDialog(self)
        if dlg.exec():
            from src.core.models import DORecord
            data = dlg.get_data()
            try:
                DORecord.create(**data)
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan:\n{exc}")

    def _on_edit(self) -> None:
        record = self._selected_record()
        if record is not None:
            self._open_edit_dialog(record)

    def _on_double_click(self, index: QModelIndex) -> None:
        self._open_edit_dialog(self._model.get_record(index.row()))

    def _open_edit_dialog(self, record) -> None:
        dlg = DOFormDialog(self, record=record)
        if dlg.exec():
            data = dlg.get_data()
            try:
                for key, val in data.items():
                    setattr(record, key, val)
                record.save()
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Gagal menyimpan:\n{exc}")

    def _on_delete(self) -> None:
        record = self._selected_record()
        if record is None:
            return
        ans = QMessageBox.question(
            self,
            "Konfirmasi Hapus",
            f"Hapus DO <b>{record.no_do}</b>?<br>Tindakan ini tidak dapat dibatalkan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            try:
                record.delete_instance()
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Gagal menghapus:\n{exc}")

    def _on_export_excel(self) -> None:
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan Excel",
            "Data_DO.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not filepath:
            return
        try:
            from src.core.models import DORecord
            all_records = list(self._build_query().order_by(DORecord.tgl))
            export_table_to_excel(all_records, filepath)
            QMessageBox.information(self, "Export Excel", f"File berhasil disimpan:\n{filepath}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Excel", f"Gagal export:\n{exc}")

    # ── helpers ───────────────────────────────────────────────────────────
    def _selected_record(self):
        rows = self._view.selectionModel().selectedRows()
        if not rows:
            return None
        return self._model.get_record(rows[0].row())
