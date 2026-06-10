from __future__ import annotations

from datetime import date, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_HEADER_BG  = colors.HexColor("#6b7280")   # abu-abu header tabel
_GRID_COLOR = colors.HexColor("#d1d5db")
_ACCENT     = colors.HexColor("#1e3a5f")    # judul laporan

_REPORT_COLUMNS: dict[str, list[tuple[str, str]]] = {
    "Harian": [
        ("Shift",               "shift"),
        ("Jumlah DO",           "count_do"),
        ("Total Tonase (ton)",  "total_tonase"),
        ("Avg Lead Time",       "avg_lead_time"),
    ],
    "Mingguan": [
        ("Minggu Ke",           "minggu_ke"),
        ("Tgl Mulai",           "tgl_mulai"),
        ("Tgl Akhir",           "tgl_akhir"),
        ("Total DO",            "total_do"),
        ("Total Tonase (ton)",  "total_tonase"),
        ("Avg Lead Time",       "avg_lead_time"),
        ("Shift 1",             "shift_1_count"),
        ("Shift 2",             "shift_2_count"),
        ("Shift 3",             "shift_3_count"),
    ],
    "Bulanan": [
        ("Customer",            "customer"),
        ("Jumlah DO",           "count"),
        ("Total Tonase (ton)",  "tonase"),
        ("Avg Lead Time",       "avg_lead_time"),
    ],
    "Per Customer": [
        ("Customer",            "customer"),
        ("Jumlah DO",           "count_do"),
        ("Total Tonase (ton)",  "total_tonase"),
        ("Avg Lead Time",       "avg_lead_time"),
    ],
    "Per Ekspedisi": [
        ("Ekspedisi",           "ekspedisi"),
        ("Jumlah DO",           "count_do"),
        ("Total Tonase (ton)",  "total_tonase"),
        ("Avg Lead Time",       "avg_lead_time"),
    ],
}


def _fmt_lead_time(minutes: float) -> str:
    m = int(minutes)
    h, rem = divmod(m, 60)
    return f"{h}j {rem}m" if h else f"{rem} mnt"


def _rows_from_report(data: dict | list, report_type: str) -> list[dict]:
    if report_type == "Harian":
        total = data.get("total", {})
        return [
            {"shift": "Shift 1", **data.get("shift_1", {})},
            {"shift": "Shift 2", **data.get("shift_2", {})},
            {"shift": "Shift 3", **data.get("shift_3", {})},
            {"shift": "TOTAL",   **total},
        ]
    if report_type == "Mingguan":
        return data if isinstance(data, list) else []
    if report_type == "Bulanan":
        return data.get("per_customer", [])
    if report_type in ("Per Customer", "Per Ekspedisi"):
        return data if isinstance(data, list) else []
    return []


def _cell_value(val: Any, key: str) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        if "lead_time" in key or "avg_lt" in key:
            return _fmt_lead_time(val)
        return f"{val:,.2f}"
    if isinstance(val, date):
        return val.strftime("%d/%m/%Y")
    return str(val)


def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(
        doc.pagesize[0] - doc.rightMargin,
        doc.bottomMargin / 2,
        f"Halaman {doc.page}",
    )
    canvas.drawString(
        doc.leftMargin,
        doc.bottomMargin / 2,
        f"Dicetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )
    canvas.restoreState()


def export_report_to_pdf(
    data: dict | list,
    report_type: str,
    company_name: str,
    filepath: str,
) -> str:
    """Export report data to PDF using ReportLab platypus."""
    margin = 2 * cm
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
    )

    styles = getSampleStyleSheet()

    style_company = ParagraphStyle(
        "company",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=_ACCENT,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    style_title = ParagraphStyle(
        "title",
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        "subtitle",
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        alignment=TA_CENTER,
        spaceAfter=2,
    )

    elements = []

    # ── Header block ──────────────────────────────────────────────────────
    elements.append(Paragraph(company_name, style_company))
    elements.append(Paragraph(f"LAPORAN LEAD TIME — {report_type.upper()}", style_title))
    elements.append(Paragraph(datetime.now().strftime("%d %B %Y"), style_subtitle))
    elements.append(Spacer(1, 0.5 * cm))

    # ── Table ─────────────────────────────────────────────────────────────
    cols = _REPORT_COLUMNS.get(report_type, [])
    row_dicts = _rows_from_report(data, report_type)

    if cols and row_dicts:
        header_labels = [c[0] for c in cols]
        keys = [c[1] for c in cols]

        table_data: list[list[str]] = [header_labels]
        for row in row_dicts:
            table_data.append([_cell_value(row.get(k), k) for k in keys])

        # Distribute column widths evenly within available page width
        avail_w = A4[0] - 2 * margin
        col_w = avail_w / len(cols)
        col_widths = [col_w] * len(cols)

        tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(
            TableStyle([
                # Header row
                ("BACKGROUND",  (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
                ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE",    (0, 0), (-1, 0), 9),
                ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
                # Body rows
                ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE",    (0, 1), (-1, -1), 9),
                ("ALIGN",       (0, 1), (-1, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                # Grid
                ("GRID",        (0, 0), (-1, -1), 0.5, _GRID_COLOR),
                ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",  (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(tbl)
    else:
        no_data_style = ParagraphStyle(
            "nodata",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.gray,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph("Tidak ada data.", no_data_style))

    doc.build(elements, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return filepath
