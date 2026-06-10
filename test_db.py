import pytest
import os
from datetime import date, time
from src.core.database import database, init_db, close_db
from src.core.models import DORecord

DB_PATH = "test_leadtime.db"

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db(DB_PATH)
    yield
    close_db()
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except PermissionError:
            pass

def test_crud_dorecord():
    # CREATE
    record = DORecord.create(
        tgl=date(2026, 6, 10),
        no_do="DO-1001",
        no_shipment="SHP-A",
        customer="PT Bintang",
        kota_kab="Bandung",
        jenis="ROLL",
        ekspedisi="Sicepat",
        jenis_truk="CDD",
        nomor_fk="FK01",
        loading_mulai=time(13, 30),
        loading_selesai=time(14, 15),
        tonase_roll=500.5,
        tonase_sheet=0.0
    )

    # Auto calculation checks
    assert record.lead_time_menit == 45
    assert record.shift == 1  # Shift 1 = 06-13:59
    assert record.tonase_total == 500.5

    # READ
    fetched = DORecord.get_by_id(record.id)
    assert fetched.no_do == "DO-1001"
    assert fetched.customer == "PT Bintang"

    # Overnight lead time test (Shift 3)
    record2 = DORecord.create(
        tgl=date(2026, 6, 11),
        no_do="DO-1002",
        no_shipment="SHP-B",
        customer="PT Cahaya",
        kota_kab="Jakarta",
        jenis="SHEET",
        ekspedisi="JNT",
        jenis_truk="ENGKEL",
        nomor_fk="FK02",
        loading_mulai=time(23, 30),
        loading_selesai=time(0, 30),
        tonase_roll=0.0,
        tonase_sheet=1200.0
    )
    assert record2.lead_time_menit == 60
    assert record2.shift == 3

    # Test Unique Constraint (tgl, no_shipment)
    from peewee import IntegrityError
    with pytest.raises(IntegrityError):
        DORecord.create(
            tgl=date(2026, 6, 10),
            no_do="DO-1003",
            no_shipment="SHP-A",
            customer="PT Duplikat",
            loading_mulai=time(10, 0),
            loading_selesai=time(11, 0)
        )

    # UPDATE
    record.tonase_roll = 600.0
    record.save()
    updated = DORecord.get_by_id(record.id)
    assert updated.tonase_roll == 600.0
    assert updated.tonase_total == 600.0

    # DELETE
    record.delete_instance()
    assert DORecord.select().count() == 1

def test_filter_query():
    # Create test data
    for i in range(5):
        DORecord.create(
            tgl=date(2026, 6, 10 + i),
            no_do=f"DO-{2000+i}",
            no_shipment=f"SHP-{chr(65+i)}",
            customer="PT Filter Test",
            kota_kab="Surabaya",
            jenis="ROLL",
            ekspedisi="JNE",
            jenis_truk="CDD",
            loading_mulai=time(8, 0),
            loading_selesai=time(9, 0),
            tonase_roll=100.0 * (i + 1)
        )

    query = (DORecord
             .select()
             .where(DORecord.customer == "PT Filter Test")
             .order_by(DORecord.tgl))
    
    assert query.count() == 5
    assert query[0].tonase_roll == 100.0
    assert query[4].tonase_roll == 500.0

    all_records = DORecord.select()
    assert all_records.count() == 5
