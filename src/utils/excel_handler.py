"""
Excel importer for DO loading-time records.

Returns
-------
dict with keys:
  success    – list of valid DORecord-compatible dicts
  duplicates – list of existing DORecord instances that conflict
  errors     – list of {row: int, reason: str}
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column aliases  (normalised lower-stripped → field name)
# ---------------------------------------------------------------------------
_COL_MAP: dict[str, str] = {
    "tgl": "tgl",
    "tanggal": "tgl",
    "#do": "no_do",
    "no do": "no_do",
    "no. do": "no_do",
    "nodo": "no_do",
    "no shipment": "no_shipment",
    "no. shipment": "no_shipment",
    "noshipment": "no_shipment",
    "customer": "customer",
    "kota/kab": "kota_kab",
    "kota kab": "kota_kab",
    "kota": "kota_kab",
    "kab": "kota_kab",
    "jenis": "jenis",
    "ekspedisi": "ekspedisi",
    "expedisi": "ekspedisi",
    "jenis truk": "jenis_truk",
    "jenistruk": "jenis_truk",
    "nomor fk": "nomor_fk",
    "no fk": "nomor_fk",
    "nofk": "nomor_fk",
    "loading mulai": "loading_mulai",
    "loadingmulai": "loading_mulai",
    "mulai": "loading_mulai",
    "loading selesai": "loading_selesai",
    "loadingselesai": "loading_selesai",
    "selesai": "loading_selesai",
    "tonase (roll)": "tonase_roll",
    "tonase roll": "tonase_roll",
    "tonaseroll": "tonase_roll",
    "tonase": "tonase_roll",
    "loading time": "loading_mulai",
    "tonase (sheet)": "tonase_sheet",
    "tonase sheet": "tonase_sheet",
    "tonasesheet": "tonase_sheet",
    # intentionally skipped: lead time, shift
}

_REQUIRED_FIELDS = {"no_do", "no_shipment"}
_TARGET_SHEET = "LOADING TIME 2026"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise_col(name: Any) -> str:
    return str(name).strip().lower()


def _find_header_row(xl: pd.ExcelFile, sheet_name: str, max_scan: int = 15) -> int:
    """Scan first N rows to find the one with the most COL_MAP matches."""
    df = xl.parse(sheet_name, header=None, dtype=object, nrows=max_scan)
    best_row, best_count = 0, 0
    for i in range(min(max_scan, len(df))):
        count = sum(1 for v in df.iloc[i] if _normalise_col(v) in _COL_MAP)
        if count > best_count:
            best_count, best_row = count, i
    logger.info("Header auto-detected at row %d (%d matched columns)", best_row, best_count)
    return best_row


def _resolve_columns(df: pd.DataFrame) -> dict[str, str]:
    """Return mapping {df_column → field_name} for recognised columns."""
    mapping: dict[str, str] = {}
    for col in df.columns:
        key = _normalise_col(col)
        if key in _COL_MAP:
            mapping[col] = _COL_MAP[key]
    return mapping


def _parse_date(value: Any) -> date | None:
    """Convert Excel serial, datetime, date, or string to Python date."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (datetime,)):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        # Excel date serial fallback: epoch 1899-12-30
        try:
            return (datetime(1899, 12, 30) + timedelta(days=float(value))).date()
        except (ValueError, OverflowError):
            return None
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _parse_time(value: Any) -> time | None:
    """
    Accept:
      - datetime / time objects
      - HH:MM or HH:MM:SS strings
      - fractional day as float (0.458333... → 11:00)
      - integer Excel time serial
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, (int, float)):
        frac = float(value) % 1.0          # keep only fractional-day part
        total_seconds = round(frac * 86400)
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        try:
            return time(int(h) % 24, int(m), int(s))
        except ValueError:
            return None
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except ValueError:
                continue
        # last attempt: try as float string
        try:
            return _parse_time(float(value))
        except (ValueError, TypeError):
            pass
    return None


def _to_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def _to_float(value: Any) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_excel(path: str) -> dict:
    """
    Parse an Excel file and return import results.

    Parameters
    ----------
    path : str
        Absolute path to the .xlsx file.

    Returns
    -------
    dict
        {
          "success":    [dict, ...],   # valid DORecord kwargs
          "duplicates": [DORecord, ...],
          "errors":     [{"row": int, "reason": str}, ...],
        }
    """
    from src.core.models import DORecord

    success: list[dict] = []
    duplicates: list = []
    errors: list[dict] = []

    # --- load workbook ---
    try:
        xl = pd.ExcelFile(path, engine="openpyxl")
    except Exception as exc:
        return {"success": [], "duplicates": [], "errors": [{"row": -1, "reason": f"Cannot open file: {exc}"}]}

    sheet_name = _TARGET_SHEET if _TARGET_SHEET in xl.sheet_names else xl.sheet_names[0]
    logger.info("Reading sheet '%s' from %s", sheet_name, path)

    # Auto-detect header row
    header_row = _find_header_row(xl, sheet_name)

    try:
        df_raw = xl.parse(sheet_name, header=header_row, dtype=object)
    except Exception as exc:
        return {"success": [], "duplicates": [], "errors": [{"row": -1, "reason": f"Cannot parse sheet: {exc}"}]}

    # Check for sub-headers (LOADING TIME -> MULAI/SELESAI pattern).
    # If the first data row contains "MULAI"/"SELESAI", its values are really
    # column sub-headers; rename the affected columns and drop that row.
    if len(df_raw) > 0:
        first = df_raw.iloc[0]
        sub_tokens = {"mulai", "selesai"}
        if any(_normalise_col(v) in sub_tokens for v in first):
            rename: dict[Any, str] = {}
            for col in df_raw.columns:
                token = _normalise_col(first[col])
                if token in sub_tokens:
                    rename[col] = token
            if rename:
                df_raw = df_raw.rename(columns=rename)
                df_raw = df_raw.iloc[1:].reset_index(drop=True)
                header_row += 1  # so excel_row math stays accurate

    col_map = _resolve_columns(df_raw)
    if not col_map:
        return {
            "success": [],
            "duplicates": [],
            "errors": [{"row": -1, "reason": "No recognised columns found in sheet. Check column headers."}],
        }

    # rename to field names (use raw df so we preserve original types)
    df_raw = df_raw.rename(columns=col_map)

    for df_row_idx, row in df_raw.iterrows():
        excel_row = int(df_row_idx) + header_row + 2  # 1-based + header offset

        record: dict[str, Any] = {}

        # --- required text fields ---
        record["no_do"] = _to_str(row.get("no_do", ""))
        record["no_shipment"] = _to_str(row.get("no_shipment", ""))

        missing = [f for f in _REQUIRED_FIELDS if not record.get(f)]
        if missing:
            logger.debug("Row %d skipped: missing %s", excel_row, missing)
            errors.append({"row": excel_row, "reason": f"Missing required field(s): {', '.join(missing)}"})
            continue

        # --- date ---
        tgl = _parse_date(row.get("tgl"))
        if tgl is None:
            errors.append({"row": excel_row, "reason": "Invalid or missing date (TGL)"})
            continue
        record["tgl"] = tgl

        # --- times ---
        mulai = _parse_time(row.get("loading_mulai"))
        selesai = _parse_time(row.get("loading_selesai"))
        if mulai is None:
            errors.append({"row": excel_row, "reason": "Invalid or missing Loading Mulai"})
            continue
        if selesai is None:
            errors.append({"row": excel_row, "reason": "Invalid or missing Loading Selesai"})
            continue
        record["loading_mulai"] = mulai
        record["loading_selesai"] = selesai

        # --- other text fields ---
        record["customer"] = _to_str(row.get("customer", ""))
        record["kota_kab"] = _to_str(row.get("kota_kab", ""))
        record["jenis"] = _to_str(row.get("jenis", ""))
        record["ekspedisi"] = _to_str(row.get("ekspedisi", ""))
        record["jenis_truk"] = _to_str(row.get("jenis_truk", ""))
        record["nomor_fk"] = _to_str(row.get("nomor_fk", "")) or None

        # --- tonase ---
        record["tonase_roll"] = _to_float(row.get("tonase_roll", 0))
        record["tonase_sheet"] = _to_float(row.get("tonase_sheet", 0))

        # Jika TONASE ada di satu kolom, pisahin berdasarkan JENIS
        jenis = record.get("jenis", "").upper().strip()
        if record["tonase_roll"] > 0 and record["tonase_sheet"] == 0:
            if jenis == "SHEET":
                record["tonase_sheet"] = record["tonase_roll"]
                record["tonase_roll"] = 0.0
            # ROLL stays as tonase_roll

        # --- duplicate check ---
        try:
            existing = DORecord.get(
                (DORecord.tgl == record["tgl"]) &
                (DORecord.no_shipment == record["no_shipment"])
            )
            duplicates.append({"existing": existing, "incoming": record})
            logger.info("Row %d is duplicate: tgl=%s no_shipment=%s", excel_row, record["tgl"], record["no_shipment"])
        except DORecord.DoesNotExist:
            success.append(record)

    logger.info(
        "parse_excel done — success=%d duplicates=%d errors=%d",
        len(success), len(duplicates), len(errors),
    )
    return {"success": success, "duplicates": duplicates, "errors": errors}


def insert_records(
    records: list[dict],
    *,
    replace_duplicates: list[dict] | None = None,
) -> tuple[int, int]:
    """
    Bulk-insert valid records and optionally replace duplicates.

    Parameters
    ----------
    records : list of dicts
        From parse_excel()["success"].
    replace_duplicates : list of duplicate entries (parse_excel()["duplicates"])
        Each entry is {"existing": DORecord, "incoming": dict}.
        Pass None or empty list to skip replacements.

    Returns
    -------
    (inserted, replaced) counts
    """
    from src.core.models import DORecord
    from src.core.database import database

    inserted = 0
    replaced = 0

    with database.atomic():
        for rec in records:
            try:
                DORecord.create(**rec)
                inserted += 1
            except Exception as exc:
                logger.warning("Insert failed for %s: %s", rec.get("no_shipment"), exc)

        for dup in (replace_duplicates or []):
            existing: DORecord = dup["existing"]
            incoming: dict = dup["incoming"]
            try:
                for k, v in incoming.items():
                    setattr(existing, k, v)
                existing.save()
                replaced += 1
            except Exception as exc:
                logger.warning("Replace failed for %s: %s", incoming.get("no_shipment"), exc)

    return inserted, replaced
