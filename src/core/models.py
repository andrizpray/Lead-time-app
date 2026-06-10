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


def _detect_shift(tgl: "date", start: time) -> int:
    """Deteksi shift berdasarkan tanggal + jam mulai dari konfigurasi schedule.

    Mencari shift schedule yang berlaku untuk tgl, lalu mencocokkan jam.
    Mendukung shift overnight (jam_mulai > jam_selesai, misal 19:00-06:59).
    """
    from src.core.settings import get_shift_for_date

    sched = get_shift_for_date(tgl)

    def _parse(t: str) -> time:
        return time.fromisoformat(t)

    def _in_range(t: time, start_str: str, end_str: str) -> bool:
        s = _parse(start_str)
        e = _parse(end_str)
        if s <= e:
            return s <= t <= e
        else:
            return t >= s or t <= e

    if _in_range(start, sched["shift_1_start"], sched["shift_1_end"]):
        return 1
    if _in_range(start, sched["shift_2_start"], sched["shift_2_end"]):
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
            self.shift = _detect_shift(self.tgl, start)

        self.tonase_total = (self.tonase_roll or 0.0) + (self.tonase_sheet or 0.0)
        return super().save(*args, **kwargs)
