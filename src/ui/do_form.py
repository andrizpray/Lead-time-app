from datetime import time as _time

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QDate, QTime, Qt


class DOFormDialog(QDialog):
    def __init__(self, parent=None, record=None):
        super().__init__(parent)
        self.setWindowTitle("Input DO" if record is None else "Edit DO")
        self.setMinimumWidth(480)
        self._build_ui()
        if record:
            self._populate(record)

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        # tgl
        self.tgl = QDateEdit(QDate.currentDate())
        self.tgl.setCalendarPopup(True)
        self.tgl.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Tanggal *", self.tgl)

        # no_do
        self.no_do = QLineEdit()
        self.no_do.setPlaceholderText("Nomor DO")
        form.addRow("No. DO *", self.no_do)

        # no_shipment
        self.no_shipment = QLineEdit()
        self.no_shipment.setPlaceholderText("Nomor Shipment")
        form.addRow("No. Shipment *", self.no_shipment)

        # customer
        self.customer = QLineEdit()
        form.addRow("Customer", self.customer)

        # kota_kab
        self.kota_kab = QLineEdit()
        form.addRow("Kota/Kab", self.kota_kab)

        # jenis
        self.jenis = QComboBox()
        self.jenis.addItems(["ROLL", "SHEET"])
        form.addRow("Jenis", self.jenis)

        # ekspedisi
        self.ekspedisi = QLineEdit()
        form.addRow("Ekspedisi", self.ekspedisi)

        # jenis_truk
        self.jenis_truk = QLineEdit()
        form.addRow("Jenis Truk", self.jenis_truk)

        # nomor_fk
        self.nomor_fk = QLineEdit()
        form.addRow("Nomor FK", self.nomor_fk)

        # loading_mulai
        self.loading_mulai = QTimeEdit(QTime(6, 0))
        self.loading_mulai.setDisplayFormat("HH:mm")
        form.addRow("Loading Mulai", self.loading_mulai)

        # loading_selesai
        self.loading_selesai = QTimeEdit(QTime(7, 0))
        self.loading_selesai.setDisplayFormat("HH:mm")
        form.addRow("Loading Selesai", self.loading_selesai)

        # tonase_roll
        self.tonase_roll = QDoubleSpinBox()
        self.tonase_roll.setRange(0, 9999.99)
        self.tonase_roll.setDecimals(2)
        self.tonase_roll.setSuffix(" ton")
        form.addRow("Tonase Roll", self.tonase_roll)

        # tonase_sheet
        self.tonase_sheet = QDoubleSpinBox()
        self.tonase_sheet.setRange(0, 9999.99)
        self.tonase_sheet.setDecimals(2)
        self.tonase_sheet.setSuffix(" ton")
        form.addRow("Tonase Sheet", self.tonase_sheet)

        root.addLayout(form)

        # auto-calculated read-only display
        info_row = QHBoxLayout()
        self.lbl_lead = QLabel("Lead time: — menit")
        self.lbl_shift = QLabel("Shift: —")
        for lbl in (self.lbl_lead, self.lbl_shift):
            lbl.setStyleSheet("color: #64748b; font-size: 12px;")
        info_row.addWidget(self.lbl_lead)
        info_row.addStretch()
        info_row.addWidget(self.lbl_shift)
        root.addLayout(info_row)

        # buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        # wire realtime recalc
        self.loading_mulai.timeChanged.connect(self._recalc)
        self.loading_selesai.timeChanged.connect(self._recalc)
        self._recalc()

    # ------------------------------------------------------------------
    def _recalc(self):
        start = self.loading_mulai.time()
        end = self.loading_selesai.time()

        s = start.hour() * 60 + start.minute()
        e = end.hour() * 60 + end.minute()
        delta = e - s
        if delta < 0:
            delta += 24 * 60
        self.lbl_lead.setText(f"Lead time: {delta} menit")

        h = start.hour()
        if 6 <= h < 14:
            shift = 1
        elif 14 <= h < 22:
            shift = 2
        else:
            shift = 3
        self.lbl_shift.setText(f"Shift: {shift}")

    # ------------------------------------------------------------------
    def _on_save(self):
        missing = []
        if not self.no_do.text().strip():
            missing.append("No. DO")
        if not self.no_shipment.text().strip():
            missing.append("No. Shipment")

        if missing:
            QMessageBox.warning(
                self,
                "Validasi",
                "Field wajib belum diisi:\n• " + "\n• ".join(missing),
            )
            return

        self.accept()

    # ------------------------------------------------------------------
    def get_data(self) -> dict:
        start = self.loading_mulai.time()
        end = self.loading_selesai.time()

        s = start.hour() * 60 + start.minute()
        e = end.hour() * 60 + end.minute()
        delta = e - s
        if delta < 0:
            delta += 24 * 60

        h = start.hour()
        if 6 <= h < 14:
            shift = 1
        elif 14 <= h < 22:
            shift = 2
        else:
            shift = 3

        return {
            "tgl": self.tgl.date().toString("yyyy-MM-dd"),
            "no_do": self.no_do.text().strip(),
            "no_shipment": self.no_shipment.text().strip(),
            "customer": self.customer.text().strip(),
            "kota_kab": self.kota_kab.text().strip(),
            "jenis": self.jenis.currentText(),
            "ekspedisi": self.ekspedisi.text().strip(),
            "jenis_truk": self.jenis_truk.text().strip(),
            "nomor_fk": self.nomor_fk.text().strip() or None,
            "loading_mulai": self.loading_mulai.time().toString("HH:mm"),
            "loading_selesai": self.loading_selesai.time().toString("HH:mm"),
            "lead_time_menit": delta,
            "shift": shift,
            "tonase_roll": self.tonase_roll.value(),
            "tonase_sheet": self.tonase_sheet.value(),
        }

    # ------------------------------------------------------------------
    def _populate(self, record):
        self.tgl.setDate(QDate.fromString(str(record.tgl), "yyyy-MM-dd"))
        self.no_do.setText(record.no_do)
        self.no_shipment.setText(record.no_shipment)
        self.customer.setText(record.customer)
        self.kota_kab.setText(record.kota_kab)
        idx = self.jenis.findText(record.jenis)
        if idx >= 0:
            self.jenis.setCurrentIndex(idx)
        self.ekspedisi.setText(record.ekspedisi)
        self.jenis_truk.setText(record.jenis_truk)
        self.nomor_fk.setText(record.nomor_fk or "")
        self.loading_mulai.setTime(QTime.fromString(str(record.loading_mulai)[:5], "HH:mm"))
        self.loading_selesai.setTime(QTime.fromString(str(record.loading_selesai)[:5], "HH:mm"))
        self.tonase_roll.setValue(record.tonase_roll)
        self.tonase_sheet.setValue(record.tonase_sheet)
