"""Tests for the dashboard work-log summary aggregation."""

from datetime import date, datetime, time, timedelta, timezone

from app.services.summary import (
    aggregate,
    bucket_key,
    label_for,
    week_start,
    window_keys,
    worked_hours,
)


class FakeLog:
    def __init__(
        self,
        log_date,
        employer_id="e1",
        overtime_minutes=0,
        paid_amount=None,
        promised_amount=None,
        report_time=None,
        scheduled_end_time=None,
        work_started_at=None,
        work_ended_at=None,
    ):
        self.log_date = log_date
        self.employer_id = employer_id
        self.overtime_minutes = overtime_minutes
        self.paid_amount = paid_amount
        self.promised_amount = promised_amount
        self.report_time = report_time
        self.scheduled_end_time = scheduled_end_time
        self.work_started_at = work_started_at
        self.work_ended_at = work_ended_at


class FakeEmployer:
    def __init__(self, id="e1", employer_name="ACME"):
        self.id = id
        self.employer_name = employer_name


def test_worked_hours_uses_actual_timestamps():
    log = FakeLog(
        date(2026, 1, 5),
        work_started_at=datetime(2026, 1, 5, 9, 0, tzinfo=timezone.utc),
        work_ended_at=datetime(2026, 1, 5, 17, 30, tzinfo=timezone.utc),
    )
    assert worked_hours(log) == 8.5


def test_worked_hours_falls_back_to_schedule():
    log = FakeLog(date(2026, 1, 5), report_time=time(9, 0), scheduled_end_time=time(18, 0))
    assert worked_hours(log) == 9.0


def test_worked_hours_wraps_past_midnight():
    log = FakeLog(date(2026, 1, 5), report_time=time(22, 0), scheduled_end_time=time(6, 0))
    assert worked_hours(log) == 8.0


def test_worked_hours_no_times_is_zero():
    assert worked_hours(FakeLog(date(2026, 1, 5))) == 0.0


def test_week_start_is_monday():
    assert week_start(date(2026, 8, 7)) == date(2026, 8, 3)  # Friday -> Monday
    assert week_start(date(2026, 8, 3)) == date(2026, 8, 3)  # Monday stays
    assert week_start(date(2026, 8, 9)) == date(2026, 8, 3)  # Sunday -> Monday


def test_bucket_key():
    assert bucket_key(date(2026, 8, 7), "daily") == "2026-08-07"
    assert bucket_key(date(2026, 8, 7), "weekly") == "2026-08-03"
    assert bucket_key(date(2026, 8, 7), "monthly") == "2026-08"


def test_label_for():
    assert label_for("2026-08-07", "daily") == "Fri 7"
    assert label_for("2026-08-03", "weekly") == "Aug 3 - Aug 9"
    assert label_for("2026-08", "monthly") == "Aug 2026"
    assert label_for("2025-01", "monthly") == "Jan 2025"


def test_window_keys_daily():
    keys = window_keys(date(2026, 8, 7), "daily")
    assert len(keys) == 7
    assert keys[-1] == "2026-08-07"
    assert keys[0] == "2026-08-01"


def test_window_keys_weekly():
    keys = window_keys(date(2026, 8, 7), "weekly")
    assert len(keys) == 8
    assert keys[-1] == "2026-08-03"
    assert keys[0] == "2026-06-15"


def test_window_keys_monthly():
    keys = window_keys(date(2026, 8, 7), "monthly")
    assert len(keys) == 6
    assert keys[-1] == "2026-08"
    assert keys[0] == "2026-03"


def test_window_keys_monthly_rolls_year():
    keys = window_keys(date(2026, 2, 10), "monthly")
    assert keys == ["2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02"]


def test_aggregate_buckets_and_totals():
    employers = [FakeEmployer(), FakeEmployer(id="e2", employer_name="Beta")]
    logs = [
        FakeLog(
            date(2026, 8, 3),
            overtime_minutes=30,
            paid_amount=800,
            promised_amount=1000,
            report_time=time(9, 0),
            scheduled_end_time=time(17, 0),
        ),
        FakeLog(
            date(2026, 8, 4),
            employer_id="e2",
            paid_amount=0,
            promised_amount=900,
            report_time=time(9, 0),
            scheduled_end_time=time(17, 0),
        ),
        FakeLog(
            date(2026, 7, 20),
            paid_amount=700,
            promised_amount=1000,
            report_time=time(9, 0),
            scheduled_end_time=time(17, 0),
        ),
    ]
    out = aggregate(logs, employers, "weekly", date(2026, 8, 7))

    assert out["total_logs"] == 3
    assert out["period"] == "weekly"
    assert len(out["rows"]) == 8

    this_week = next(r for r in out["rows"] if r["key"] == "2026-08-03")
    assert this_week["days"] == 2
    assert this_week["hours"] == 16
    assert this_week["overtime"] == 0.5
    assert this_week["paid"] == 800
    assert this_week["promised"] == 1900

    empty = next(r for r in out["rows"] if r["key"] == "2026-06-15")
    assert empty["days"] == 0
    assert empty["hours"] == 0

    by_employer = out["by_employer"]
    assert len(by_employer) == 2
    assert by_employer[0]["name"] == "ACME"
    assert by_employer[0]["value"] == 16  # 8h Aug 3 + 8h Jul 20
    assert by_employer[1]["name"] == "Beta"


def test_aggregate_by_employer_sorted_and_skips_zero():
    employers = [FakeEmployer()]
    logs = [
        FakeLog(date(2026, 8, 3), report_time=time(9, 0), scheduled_end_time=time(17, 0)),
        FakeLog(date(2026, 8, 4), report_time=time(9, 0), scheduled_end_time=time(13, 0)),
    ]
    out = aggregate(logs, employers, "daily", date(2026, 8, 4))
    assert len(out["by_employer"]) == 1
    assert out["by_employer"][0]["name"] == "ACME"
    assert out["by_employer"][0]["value"] == 12

    no_hours = [FakeLog(date(2026, 8, 3))]
    out = aggregate(no_hours, [], "daily", date(2026, 8, 3))
    assert out["by_employer"] == []


def test_aggregate_missing_employer_placeholder_name():
    out = aggregate(
        [FakeLog(date(2026, 8, 3), report_time=time(9, 0), scheduled_end_time=time(17, 0))],
        [],
        "daily",
        date(2026, 8, 3),
    )
    assert out["by_employer"][0]["name"] == "—"


def test_aggregate_monthly_window():
    logs = [FakeLog(date(2026, 8, 15), promised_amount=1500)]
    out = aggregate(logs, [], "monthly", date(2026, 8, 7))
    rows = out["rows"]
    assert len(rows) == 6
    aug = next(r for r in rows if r["key"] == "2026-08")
    assert aug["days"] == 1
    assert aug["promised"] == 1500
    assert aug["label"] == "Aug 2026"
