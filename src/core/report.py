from peewee import fn
from src.core.models import DORecord


class ReportGenerator:

    @staticmethod
    def daily_detail_report(tgl_awal, tgl_akhir) -> dict:
        """
        Laporan detail per DO dalam rentang tanggal, lengkap dengan:
        - Baris per DO (tgl, no_do, no_shipment, customer, kota_kab, jenis, tonase_total, shift)
        - Agregat per hari per shift (count_do, total_tonase)
        - Total keseluruhan termasuk avg_lead_time
        """
        # --- detail records ---
        records = list(
            DORecord.select()
            .where(DORecord.tgl.between(tgl_awal, tgl_akhir))
            .order_by(DORecord.tgl.asc(), DORecord.shift.asc(), DORecord.id.asc())
        )

        # --- daily per-shift aggregates ---
        daily_shift = list(
            DORecord.select(
                DORecord.tgl,
                DORecord.shift,
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.SUM(DORecord.lead_time_menit).alias("sum_lt"),
            )
            .where(DORecord.tgl.between(tgl_awal, tgl_akhir))
            .group_by(DORecord.tgl, DORecord.shift)
            .order_by(DORecord.tgl.asc(), DORecord.shift.asc())
            .namedtuples()
        )

        # Build dict: date -> {shift -> {cnt, ton, sum_lt}}
        from collections import defaultdict
        daily_map: dict = defaultdict(lambda: {
            1: {"cnt": 0, "ton": 0.0, "sum_lt": 0.0},
            2: {"cnt": 0, "ton": 0.0, "sum_lt": 0.0},
            3: {"cnt": 0, "ton": 0.0, "sum_lt": 0.0},
        })
        for r in daily_shift:
            s = r.shift or 1
            daily_map[r.tgl][s] = {
                "cnt": r.cnt or 0,
                "ton": float(r.sum_ton or 0.0),
                "sum_lt": float(r.sum_lt or 0.0),
            }

        # Sorted list of dates
        sorted_dates = sorted(daily_map.keys())

        daily_stats = []
        for d in sorted_dates:
            sh = daily_map[d]
            total_do_day = sh[1]["cnt"] + sh[2]["cnt"] + sh[3]["cnt"]
            total_lt_day = sh[1]["sum_lt"] + sh[2]["sum_lt"] + sh[3]["sum_lt"]
            daily_stats.append({
                "tgl": d,
                "shift_1_do":  sh[1]["cnt"],
                "shift_1_ton": sh[1]["ton"],
                "shift_2_do":  sh[2]["cnt"],
                "shift_2_ton": sh[2]["ton"],
                "shift_3_do":  sh[3]["cnt"],
                "shift_3_ton": sh[3]["ton"],
                "total_do":    total_do_day,
                "total_ton":   sh[1]["ton"] + sh[2]["ton"] + sh[3]["ton"],
                "avg_lead_time": total_lt_day / total_do_day if total_do_day else 0.0,
            })

        total_do = sum(d["total_do"] for d in daily_stats)
        total_ton = sum(d["total_ton"] for d in daily_stats)
        total_lt = sum(d["avg_lead_time"] * d["total_do"] for d in daily_stats)
        avg_lead_time = total_lt / total_do if total_do else 0.0

        return {
            "tgl_awal": tgl_awal,
            "tgl_akhir": tgl_akhir,
            "records": records,
            "daily_stats": daily_stats,
            "total_do": total_do,
            "total_ton": total_ton,
            "avg_lead_time": avg_lead_time,
        }

    @staticmethod
    def daily_report(tgl) -> dict:
        rows = list(
            DORecord.select(
                DORecord.shift,
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(DORecord.tgl == tgl)
            .group_by(DORecord.shift)
            .namedtuples()
        )

        result = {
            "tgl": tgl,
            "shift_1": {"count_do": 0, "total_tonase": 0.0, "avg_lead_time": 0.0},
            "shift_2": {"count_do": 0, "total_tonase": 0.0, "avg_lead_time": 0.0},
            "shift_3": {"count_do": 0, "total_tonase": 0.0, "avg_lead_time": 0.0},
            "total": {"count_do": 0, "total_tonase": 0.0, "avg_lead_time": 0.0},
        }

        total_cnt = 0
        total_ton = 0.0
        weighted_lt = 0.0

        for r in rows:
            key = f"shift_{r.shift}"
            if key in result:
                cnt = r.cnt or 0
                ton = float(r.sum_ton or 0.0)
                avg = float(r.avg_lt or 0.0)
                result[key] = {"count_do": cnt, "total_tonase": ton, "avg_lead_time": avg}
                total_cnt += cnt
                total_ton += ton
                weighted_lt += avg * cnt

        result["total"] = {
            "count_do": total_cnt,
            "total_tonase": total_ton,
            "avg_lead_time": weighted_lt / total_cnt if total_cnt else 0.0,
        }
        return result

    @staticmethod
    def weekly_report(tgl_awal, tgl_akhir) -> list[dict]:
        week_expr = fn.strftime("%Y-%W", DORecord.tgl)

        agg = list(
            DORecord.select(
                week_expr.alias("week"),
                fn.MIN(DORecord.tgl).alias("tgl_mulai"),
                fn.MAX(DORecord.tgl).alias("tgl_akhir"),
                fn.COUNT(DORecord.id).alias("total_do"),
                fn.SUM(DORecord.tonase_total).alias("total_tonase"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(DORecord.tgl.between(tgl_awal, tgl_akhir))
            .group_by(week_expr)
            .order_by(week_expr)
            .namedtuples()
        )

        if not agg:
            return []

        shift_rows = list(
            DORecord.select(
                week_expr.alias("week"),
                DORecord.shift,
                fn.COUNT(DORecord.id).alias("cnt"),
            )
            .where(DORecord.tgl.between(tgl_awal, tgl_akhir))
            .group_by(week_expr, DORecord.shift)
            .namedtuples()
        )

        shift_map: dict[str, dict[int, int]] = {}
        for r in shift_rows:
            shift_map.setdefault(r.week, {})[r.shift] = r.cnt

        results = []
        for i, r in enumerate(agg, 1):
            shifts = shift_map.get(r.week, {})
            results.append({
                "minggu_ke": i,
                "tgl_mulai": r.tgl_mulai,
                "tgl_akhir": r.tgl_akhir,
                "total_do": r.total_do or 0,
                "total_tonase": float(r.total_tonase or 0.0),
                "avg_lead_time": float(r.avg_lt or 0.0),
                "shift_1_count": shifts.get(1, 0),
                "shift_2_count": shifts.get(2, 0),
                "shift_3_count": shifts.get(3, 0),
            })

        return results

    @staticmethod
    def monthly_report(tahun: int, bulan: int) -> dict:
        year_str = str(tahun)
        month_str = f"{bulan:02d}"

        totals = (
            DORecord.select(
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(
                fn.strftime("%Y", DORecord.tgl) == year_str,
                fn.strftime("%m", DORecord.tgl) == month_str,
            )
            .namedtuples()
            .first()
        )

        shift_rows = list(
            DORecord.select(
                DORecord.shift,
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(
                fn.strftime("%Y", DORecord.tgl) == year_str,
                fn.strftime("%m", DORecord.tgl) == month_str,
            )
            .group_by(DORecord.shift)
            .namedtuples()
        )

        per_shift = {}
        for r in shift_rows:
            per_shift[f"shift_{r.shift}"] = {
                "count_do": r.cnt or 0,
                "total_tonase": float(r.sum_ton or 0.0),
                "avg_lead_time": float(r.avg_lt or 0.0),
            }

        cust_rows = list(
            DORecord.select(
                DORecord.customer,
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(
                fn.strftime("%Y", DORecord.tgl) == year_str,
                fn.strftime("%m", DORecord.tgl) == month_str,
            )
            .group_by(DORecord.customer)
            .order_by(fn.SUM(DORecord.tonase_total).desc())
            .namedtuples()
        )

        per_customer = [
            {
                "customer": r.customer or "—",
                "count": r.cnt or 0,
                "tonase": float(r.sum_ton or 0.0),
                "avg_lead_time": float(r.avg_lt or 0.0),
            }
            for r in cust_rows
        ]

        return {
            "bulan": bulan,
            "tahun": tahun,
            "total_do": totals.cnt or 0 if totals else 0,
            "total_tonase": float(totals.sum_ton or 0.0) if totals else 0.0,
            "avg_lead_time": float(totals.avg_lt or 0.0) if totals else 0.0,
            "per_shift": per_shift,
            "per_customer": per_customer,
        }

    @staticmethod
    def customer_report(tgl_awal, tgl_akhir) -> list[dict]:
        rows = list(
            DORecord.select(
                DORecord.customer,
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(DORecord.tgl.between(tgl_awal, tgl_akhir))
            .group_by(DORecord.customer)
            .order_by(fn.COUNT(DORecord.id).desc())
            .namedtuples()
        )
        return [
            {
                "customer": r.customer or "—",
                "count_do": r.cnt or 0,
                "total_tonase": float(r.sum_ton or 0.0),
                "avg_lead_time": float(r.avg_lt or 0.0),
            }
            for r in rows
        ]

    @staticmethod
    def expedition_report(tgl_awal, tgl_akhir) -> list[dict]:
        rows = list(
            DORecord.select(
                DORecord.ekspedisi,
                fn.COUNT(DORecord.id).alias("cnt"),
                fn.SUM(DORecord.tonase_total).alias("sum_ton"),
                fn.AVG(DORecord.lead_time_menit).alias("avg_lt"),
            )
            .where(DORecord.tgl.between(tgl_awal, tgl_akhir))
            .group_by(DORecord.ekspedisi)
            .order_by(fn.COUNT(DORecord.id).desc())
            .namedtuples()
        )
        return [
            {
                "ekspedisi": r.ekspedisi or "—",
                "count_do": r.cnt or 0,
                "total_tonase": float(r.sum_ton or 0.0),
                "avg_lead_time": float(r.avg_lt or 0.0),
            }
            for r in rows
        ]
