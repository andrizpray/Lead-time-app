from datetime import date, datetime, time, timedelta
from peewee import (
    Model,
    DateField,
    CharField,
    IntegerField,
    FloatField,
    TimeField,
    DateTimeField,
)
from src.core.database import database


def _calc_lead_time(start: time, end: time) -> int:
    """Return duration in minutes, handling overnight spans (e.g. 23:00 -> 01:30)."""
    t0 = timedelta(hours=start.hour, minutes=start.minute, seconds=start.second)
    t1 = timedelta(hours=end.hour, minutes=end.minute, seconds=end.second)
    delta = t1 - t0
    if delta.total_seconds() < 0:
        delta += timedelta(days=1)
    return int(delta.total_seconds() // 60)


def _detect_shift(start: time) -> int:
    """Shift 1 = 06:00–13:59, Shift 2 = 14:00–21:59, Shift 3 = 22:00–05:59."""
    h = start.hour
    if 6 <= h < 14:
        return 1
    if 14 <= h < 22:
        return 2
    return 3


class DORecord(Model):
    tgl = DateField()
    no_do = CharField(max_length=50)
    no_shipment = CharField(max_length=50)
    customer = CharField(max_length=100)
    kota_kab = CharField(max_length=100)
    jenis = CharField(max_length=50)
    ekspedisi = CharField(max_length=100)
    jenis_truk = CharField(max_length=50)
    nomor_fk = CharField(max_length=50, null=True)
    loading_mulai = TimeField()
    loading_selesai = TimeField()
    lead_time_menit = IntegerField(default=0)
    tonase_roll = FloatField(default=0.0)
    tonase_sheet = FloatField(default=0.0)
    tonase_total = FloatField(default=0.0)
    shift = IntegerField(default=0)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        database = database
        table_name = "do_records"
        indexes = (
            (("tgl", "no_shipment"), True),
        )

    def save(self, *args, **kwargs):
        if self.loading_mulai and self.loading_selesai:
            start = (
                self.loading_mulai
                if isinstance(self.loading_mulai, time)
                else time.fromisoformat(str(self.loading_mulai))
            )
            end = (
                self.loading_selesai
                if isinstance(self.loading_selesai, time)
                else time.fromisoformat(str(self.loading_selesai))
            )
            self.lead_time_menit = _calc_lead_time(start, end)
            self.shift = _detect_shift(start)

        self.tonase_total = (self.tonase_roll or 0.0) + (self.tonase_sheet or 0.0)
        return super().save(*args, **kwargs)
