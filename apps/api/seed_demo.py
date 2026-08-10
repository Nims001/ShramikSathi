"""Demo data seeder for ShramikSathi.

Creates one demo employer-role account ("ABC Construction Pvt. Ltd.")
plus five worker accounts with different employment types and violation
profiles, links them via share codes, and seeds ~2 weeks of daily work logs
(approved / pending / rejected / draft) per worker with valid dual signatures.

Run from inside the api container:

    docker exec infra-api-1 python seed_demo.py

Safe to re-run: demo usernames are deleted and recreated.
"""

import asyncio
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select

from app import crypto
from app.db import SessionLocal
from app.models import Employer, EmployerLink, User, WeeklySetting, WorkLog, WorkLogSignatureEvent
from app.security import generate_share_code, hash_password, hash_share_code
from app.services import signing
from app.services.analysis import _run_deterministic
from app.services.calculations import age_from_dob, compute_employer_background

DEMO_ORG = "ABC Construction Pvt. Ltd."
DEMO_PREFIX = "demo."
PASSWORD = "Demo@123"
EMPLOYER_USERNAME = "abc.employer"
EMPLOYER_PASSWORD = "Employer@123"

NEPAL = timezone(timedelta(hours=5, minutes=45))
UTC = timezone.utc


def nepal_datetime(d: date, t: time) -> datetime:
    """Nepal-local wall clock stored as UTC (matches what the web app does)."""
    return datetime.combine(d, t, tzinfo=NEPAL).astimezone(UTC)


def overtime_minutes(d: date, scheduled_end: time, ended: time) -> int:
    """Minutes worked past the scheduled end, same-day, on Nepal wall clock."""
    start_min = scheduled_end.hour * 60 + scheduled_end.minute
    end_min = ended.hour * 60 + ended.minute
    return max(0, end_min - start_min)


def workdays_since(today: date, days: int, skip_sunday: bool) -> list[date]:
    out = []
    d = today
    while len(out) < days:
        if not (skip_sunday and d.weekday() == 6):
            out.append(d)
        d -= timedelta(days=1)
    out.reverse()
    return out


def payday_date(today: date, pay: dict) -> Optional[date]:
    nature = pay.get("nature")
    if nature == "daily":
        return None
    if nature == "weekly":
        # Most recent Saturday (weekday 5).
        return today - timedelta(days=(today.weekday() - 5) % 7)
    if nature == "monthly":
        # Most recent 5th of the month.
        if today.day >= 5:
            return date(today.year, today.month, 5)
        prev = today.replace(day=1) - timedelta(days=1)
        return date(prev.year, prev.month, 5)
    return None


# ── Per-worker contract profiles (drives deterministic violations) ────────────

WORKERS = [
    {
        "username": "sita.shrestha",
        "name": "Sita Shrestha",
        "role_profile": "compliant",
        "gender": "female",
        "dob": date(1995, 4, 10),
        "ethnicity": "Brahmin",
        "education": "Grade 10",
        "language": "en",
        "job_title": "Office Accountant",
        "employment_type": "regular",
        "fields": {
            "employer_name": DEMO_ORG,
            "work_province": "Bagmati",
            "work_district": "Kathmandu",
            "work_address": "Thamel, Kathmandu",
            "skill_level": "skilled",
            "industry": "construction",
            "hiring_channel": "direct",
            "job_title": "Office Accountant",
            "tenure_years": 4,
            "tenure_months": 2,
            "contract_hours_per_day": 8,
            "contract_break_start": time(13, 0),
            "contract_break_end": time(13, 30),
            "contract_break_unspecified": False,
            "contract_days_per_week": 6,
            "contract_months_per_year": 12,
            "actual_hours_per_day": 8,
            "actual_break_start": time(13, 0),
            "actual_break_end": time(13, 30),
            "actual_break_unspecified": False,
            "actual_days_per_week": 6,
            "actual_months_per_year": 12,
            "overtime_rule": True,
            "overtime_rate": "150",
            "overtime_consent": "voluntary",
            "night_work": False,
            "pay_unit": "monthly",
            "promised_wage": 28000,
            "payment_frequency": "monthly",
            "payment_method": "bank_transfer",
            "received_annual_increment": True,
            "festival_expense_paid": True,
            "weekly_leave_days_per_week": 1,
            "weekly_off_day_guaranteed": True,
            "public_holiday_paid_leave": True,
            "has_written_contract": True,
            "contract_states_wage": True,
            "contract_states_hours": True,
            "contract_states_leave": True,
            "contract_states_termination": True,
            "contract_explained_in_own_language": True,
            "ssf_registered": True,
            "pf_deducted": True,
            "pf_deposited": True,
            "gratuity_deducted": False,
            "gratuity_paid_by_employer": True,
            "medical_insurance_provided": True,
            "accidental_insurance_provided": True,
            "free_to_leave_during_off_hours": True,
            "abuse_experienced": False,
        },
        "log": {
            "skip_sunday": True,
            "report_time": time(9, 0),
            "scheduled_end": time(17, 0),
            "sched_break": (time(13, 0), time(13, 30)),
            "pay": {"nature": "monthly", "monthly_salary": 28000},
            "end_times": None,  # ends at scheduled end
        },
    },
    {
        "username": "ram.bahadur",
        "name": "Ram Bahadur",
        "role_profile": "violations",
        "gender": "male",
        "dob": date(1988, 12, 1),
        "ethnicity": "Tharu",
        "education": "Primary",
        "language": "ne",
        "job_title": "Construction Worker (Mason Helper)",
        "employment_type": "casual",
        "fields": {
            "employer_name": DEMO_ORG,
            "work_province": "Bagmati",
            "work_district": "Kathmandu",
            "work_address": "Thamel, Kathmandu",
            "skill_level": "unskilled",
            "industry": "construction",
            "hiring_channel": "labor_contractor",
            "job_title": "Construction Worker (Mason Helper)",
            "tenure_years": 5,
            "tenure_months": 10,
            "contract_hours_per_day": 9,
            "contract_break_unspecified": True,
            "contract_days_per_week": 7,
            "contract_months_per_year": 12,
            "actual_hours_per_day": 13,
            "actual_break_unspecified": True,
            "actual_days_per_week": 7,
            "actual_months_per_year": 12,
            "overtime_rule": False,
            "overtime_consent": "forced",
            "night_work": True,
            "night_allowance": False,
            "pay_unit": "daily",
            "promised_wage": 500,
            "payment_frequency": "monthly",
            "payment_method": "cash",
            "received_annual_increment": False,
            "festival_expense_paid": False,
            "other_deduction_reason": "uniform and safety gear",
            "weekly_leave_days_per_week": 0,
            "weekly_off_day_guaranteed": False,
            "worked_off_day_paid_and_replaced": False,
            "public_holiday_paid_leave": False,
            "sick_leave_denied": True,
            "paternity_leave_denied": True,
            "has_written_contract": False,
            "ssf_registered": False,
            "pf_deducted": True,
            "pf_deposited": False,
            "gratuity_deducted": True,
            "gratuity_paid_by_employer": False,
            "medical_insurance_provided": False,
            "accidental_insurance_provided": False,
            "paid_fee_to_get_job": True,
            "employer_holds_documents": True,
            "free_to_leave_during_off_hours": False,
            "abuse_experienced": True,
            "other_clauses": [
                "Must work overtime whenever asked without extra pay",
                "Salary is paid only after the project finishes",
            ],
        },
        "log": {
            "skip_sunday": False,
            "report_time": time(8, 0),
            "scheduled_end": time(17, 0),
            "sched_break": None,
            "pay": {
                "nature": "daily",
                "promised": 500,
                "paid": 400,
                "deduction": {"label": "uniform & safety gear", "amount": 50},
            },
            "end_times": [time(20, 30), time(19, 0), time(21, 0), time(18, 30), time(20, 0)],
        },
    },
    {
        "username": "maya.tamang",
        "name": "Maya Tamang",
        "role_profile": "few",
        "gender": "female",
        "dob": date(1997, 6, 20),
        "ethnicity": "Tamang",
        "education": "Grade 8",
        "language": "en",
        "job_title": "Garment Machinist (per piece)",
        "employment_type": "work_based",
        "fields": {
            "employer_name": DEMO_ORG,
            "work_province": "Bagmati",
            "work_district": "Kathmandu",
            "work_address": "Baneshwor, Kathmandu",
            "skill_level": "semi_skilled",
            "industry": "garment",
            "hiring_channel": "direct",
            "job_title": "Garment Machinist (per piece)",
            "tenure_years": 2,
            "tenure_months": 3,
            "contract_hours_per_day": 8,
            "contract_break_start": time(13, 0),
            "contract_break_end": time(13, 30),
            "contract_break_unspecified": False,
            "contract_days_per_week": 6,
            "contract_months_per_year": 12,
            "actual_hours_per_day": 8,
            "actual_break_start": time(13, 0),
            "actual_break_end": time(13, 30),
            "actual_break_unspecified": False,
            "actual_days_per_week": 6,
            "actual_months_per_year": 12,
            "overtime_rule": True,
            "overtime_rate": "150",
            "overtime_consent": "voluntary",
            "pay_unit": "per_piece",
            "promised_wage": 55,
            "payment_frequency": "weekly",
            "payment_method": "cash",
            "received_annual_increment": True,
            "festival_expense_paid": True,
            "weekly_leave_days_per_week": 1,
            "weekly_off_day_guaranteed": True,
            "public_holiday_paid_leave": True,
            "has_written_contract": True,
            "contract_states_wage": True,
            "contract_states_hours": True,
            "contract_states_leave": False,
            "contract_states_termination": True,
            "contract_explained_in_own_language": True,
            "ssf_registered": True,
            "pf_deducted": True,
            "pf_deposited": True,
            "gratuity_deducted": False,
            "gratuity_paid_by_employer": True,
            "medical_insurance_provided": False,
            "accidental_insurance_provided": False,
            "free_to_leave_during_off_hours": True,
            "abuse_experienced": False,
        },
        "log": {
            "skip_sunday": True,
            "report_time": time(9, 0),
            "scheduled_end": time(17, 0),
            "sched_break": (time(13, 0), time(13, 30)),
            "pay": {"nature": "weekly", "per_piece": (45, 55), "paid_full": True},
            "end_times": None,
        },
    },
    {
        "username": "bikash.yadav",
        "name": "Bikash Yadav",
        "role_profile": "few",
        "gender": "male",
        "dob": date(1999, 2, 14),
        "ethnicity": "Madheshi",
        "education": "Grade 10",
        "language": "en",
        "job_title": "Site Labourer (daily wage)",
        "employment_type": "time_based",
        "fields": {
            "employer_name": DEMO_ORG,
            "work_province": "Bagmati",
            "work_district": "Lalitpur",
            "work_address": "Balkumari, Lalitpur",
            "skill_level": "unskilled",
            "industry": "construction",
            "hiring_channel": "direct",
            "job_title": "Site Labourer (daily wage)",
            "tenure_years": 0,
            "tenure_months": 6,
            "contract_hours_per_day": 8,
            "contract_break_start": time(13, 0),
            "contract_break_end": time(13, 30),
            "contract_break_unspecified": False,
            "contract_days_per_week": 6,
            "contract_months_per_year": 12,
            "actual_hours_per_day": 8,
            "actual_break_unspecified": True,
            "actual_days_per_week": 6,
            "actual_months_per_year": 12,
            "overtime_rule": False,
            "pay_unit": "daily",
            "promised_wage": 850,
            "payment_frequency": "daily",
            "payment_method": "cash",
            "received_annual_increment": False,
            "festival_expense_paid": False,
            "weekly_leave_days_per_week": 1,
            "weekly_off_day_guaranteed": True,
            "public_holiday_paid_leave": False,
            "has_written_contract": False,
            "ssf_registered": False,
            "pf_deducted": False,
            "medical_insurance_provided": False,
            "accidental_insurance_provided": False,
            "free_to_leave_during_off_hours": True,
            "abuse_experienced": False,
        },
        "log": {
            "skip_sunday": True,
            "report_time": time(8, 0),
            "scheduled_end": time(17, 0),
            "sched_break": (time(13, 0), time(13, 30)),
            "pay": {"nature": "daily", "promised": 850, "paid": 850},
            "end_times": None,
        },
    },
    {
        "username": "sunita.rai",
        "name": "Sunita Rai",
        "role_profile": "few",
        "gender": "female",
        "dob": date(2000, 11, 5),
        "ethnicity": "Rai",
        "education": "Bachelors (running)",
        "language": "en",
        "job_title": "Cafe Attendant (part time)",
        "employment_type": "part_time",
        "fields": {
            "employer_name": DEMO_ORG,
            "work_province": "Bagmati",
            "work_district": "Kathmandu",
            "work_address": "Jhamsikhel, Lalitpur",
            "skill_level": "semi_skilled",
            "industry": "hospitality",
            "hiring_channel": "direct",
            "job_title": "Cafe Attendant (part time)",
            "tenure_years": 0,
            "tenure_months": 10,
            "contract_hours_per_day": 5,
            "contract_days_per_week": 5,
            "contract_months_per_year": 12,
            "actual_hours_per_day": 5,
            "actual_days_per_week": 5,
            "actual_months_per_year": 12,
            "overtime_rule": False,
            "pay_unit": "hourly",
            "promised_wage": 450,
            "payment_frequency": "weekly",
            "payment_method": "bank_transfer",
            "received_annual_increment": True,
            "festival_expense_paid": False,
            "weekly_leave_days_per_week": 2,
            "weekly_off_day_guaranteed": True,
            "public_holiday_paid_leave": True,
            "has_written_contract": True,
            "contract_states_wage": True,
            "contract_states_hours": True,
            "contract_states_leave": True,
            "contract_states_termination": True,
            "contract_explained_in_own_language": True,
            "ssf_registered": False,
            "pf_deducted": False,
            "gratuity_paid_by_employer": True,
            "medical_insurance_provided": False,
            "accidental_insurance_provided": False,
            "free_to_leave_during_off_hours": True,
            "abuse_experienced": False,
        },
        "log": {
            "skip_sunday": True,
            "report_time": time(15, 0),
            "scheduled_end": time(20, 0),
            "sched_break": None,
            "pay": {"nature": "weekly", "daily_earnings": 2250, "paid_full": True},
            "end_times": None,
        },
    },
]

REJECTION_REASON = (
    "Overtime hours look wrong for this day — please check the start and end "
    "times and resubmit."
)


async def main() -> None:
    async with SessionLocal() as db:
        # ── Clean up a previous run ────────────────────────────────────────
        demo_usernames = [EMPLOYER_USERNAME] + [w["username"] for w in WORKERS]
        old_users = list(
            (
                await db.execute(
                    select(User).where(User.username.in_(demo_usernames))
                )
            ).scalars()
        )
        if old_users:
            old_ids = [u.id for u in old_users]
            await db.execute(
                delete(EmployerLink).where(
                    EmployerLink.employer_user_id.in_(old_ids)
                    | EmployerLink.employee_user_id.in_(old_ids)
                )
            )
            await db.execute(
                delete(WorkLog).where(WorkLog.user_id.in_(old_ids))
            )
            await db.execute(
                delete(Employer).where(Employer.user_id.in_(old_ids))
            )
            for u in old_users:
                await db.delete(u)
            await db.commit()
            print(f"Removed {len(old_users)} previous demo user(s)")

        # ── Employer portal account ────────────────────────────────────────
        employer_user = User(
            username=EMPLOYER_USERNAME,
            password_hash=hash_password(EMPLOYER_PASSWORD),
            role="employer",
            language="en",
        )
        db.add(employer_user)
        await db.flush()
        await signing.ensure_signing_keys(db, employer_user)
        print(f"Employer account: {EMPLOYER_USERNAME} / {EMPLOYER_PASSWORD}")

        today = date.today()

        # ── Workers ────────────────────────────────────────────────────────
        for profile in WORKERS:
            username = profile["username"]
            fields = profile["fields"]
            user = User(
                username=username,
                password_hash=hash_password(PASSWORD),
                role="worker",
                gender=profile["gender"],
                date_of_birth=profile["dob"],
                age=age_from_dob(profile["dob"]),
                ethnicity=profile["ethnicity"],
                education_level=profile["education"],
                language=profile["language"],
                share_code_hash=hash_share_code(generate_share_code()),
            )
            db.add(user)
            await db.flush()
            await signing.ensure_signing_keys(db, user)

            # Replace the share code so the printed code is the one on file.
            code = generate_share_code()
            user.share_code_hash = hash_share_code(code)

            employer = Employer(user_id=user.id)
            data = dict(fields)
            data.setdefault("employment_type", profile.get("employment_type"))
            for field, value in data.items():
                setattr(employer, field, value)
            for field, value in compute_employer_background(data).items():
                setattr(employer, field, value)
            db.add(employer)
            await db.flush()

            db.add(
                EmployerLink(
                    employer_user_id=employer_user.id,
                    employee_user_id=user.id,
                    note=profile.get("name"),
                )
            )

            log_cfg = profile["log"]
            pay = log_cfg.get("pay", {})
            payday = payday_date(today, pay)

            db.add(
                WeeklySetting(
                    employer_id=employer.id,
                    week_start=week_monday(today),
                    break_days_this_week=[] if fields.get("weekly_leave_days_per_week", 1) == 0 else ["6"],
                    promised_payment_day=payday,
                    daily_promised_wage=(
                        fields.get("promised_wage") if fields.get("pay_unit") == "daily" else None
                    ),
                )
            )

            # ── Work logs ─────────────────────────────────────────────────
            dates = workdays_since(today, 14, log_cfg["skip_sunday"])

            weekly_pay = None
            if pay.get("nature") == "weekly" and payday:
                week_dates = [dd for dd in dates if payday - timedelta(days=6) <= dd <= payday]
                if pay.get("per_piece"):
                    pc, pr = pay["per_piece"]
                    weekly_pay = round(len(week_dates) * pc * pr, 2)
                else:
                    weekly_pay = round(len(week_dates) * pay["daily_earnings"], 2)

            end_pool = log_cfg.get("end_times") or []
            for i, d in enumerate(dates):
                scheduled_end = log_cfg["scheduled_end"]
                # Ram works late; the rest end on schedule.
                end_time = scheduled_end
                if end_pool:
                    end_time = end_pool[i % len(end_pool)]
                started = nepal_datetime(d, log_cfg["report_time"])
                ended = nepal_datetime(d, end_time)

                breaks = None
                if log_cfg.get("sched_break"):
                    bs, be = log_cfg["sched_break"]
                    breaks = [
                        {
                            "start": nepal_datetime(d, bs).isoformat(),
                            "end": nepal_datetime(d, be).isoformat(),
                        }
                    ]

                # Promised / paid amounts only exist for daily-paid workers or
                # on the configured payment day, matching the logging UI.
                nature = pay.get("nature", "daily")
                is_pay = nature == "daily" or d == payday
                piece_count = piece_rate = None
                if pay.get("per_piece"):
                    piece_count, piece_rate = pay["per_piece"]
                promised = paid = None
                deductions = None
                if is_pay:
                    if nature == "daily":
                        promised = pay["promised"]
                        paid = pay.get("paid", promised)
                        if pay.get("deduction"):
                            deductions = [pay["deduction"]]
                    elif nature == "weekly":
                        if piece_count is not None:
                            promised = round(piece_count * piece_rate, 2)
                        else:
                            promised = pay["daily_earnings"]
                        paid = weekly_pay if pay.get("paid_full") else pay.get("paid", promised)
                    else:  # monthly
                        promised = pay["monthly_salary"]
                        paid = pay.get("paid", promised)

                log = WorkLog(
                    user_id=user.id,
                    employer_id=employer.id,
                    log_date=d,
                    report_time=log_cfg["report_time"],
                    scheduled_end_time=scheduled_end,
                    scheduled_break_start=(
                        log_cfg["sched_break"][0] if log_cfg.get("sched_break") else None
                    ),
                    scheduled_break_end=(
                        log_cfg["sched_break"][1] if log_cfg.get("sched_break") else None
                    ),
                    work_started_at=started,
                    work_ended_at=ended,
                    breaks=breaks,
                    overtime_minutes=overtime_minutes(d, scheduled_end, end_time),
                    paid_amount=paid,
                    promised_amount=promised,
                    piece_count=piece_count,
                    piece_rate=piece_rate,
                    deductions=deductions,
                )
                db.add(log)
                await db.flush()

                idx_from_latest = len(dates) - 1 - i
                if idx_from_latest == 0:
                    continue  # today: draft (in progress)
                if idx_from_latest == 1:
                    status = "rejected"
                elif idx_from_latest in (2, 3):
                    status = "pending_employer"
                else:
                    status = "approved"
                await _sign(db, log, user, employer_user, status)
            await db.commit()

            findings = _run_deterministic(user, employer)
            print(
                f"Worker: {username} / {PASSWORD}  share-code={code}  "
                f"violations={len(findings)}"
            )

        print("\nDone. Log in as the employer at /employer and use the worker "
              "share codes to link accounts.")


async def _sign(db, log: WorkLog, worker: User, employer: User, status: str) -> None:
    content_hash = signing.log_content_hash(log)
    employee_sig = crypto.sign(content_hash, worker.signing_private_key_enc)
    now = datetime.now(UTC)

    log.content_hash = content_hash
    log.employee_signature = employee_sig
    log.employee_signed_at = now
    log.submission_version = 1
    log.approval_status = "pending_employer"

    kind = "employee_sign"
    if status == "approved":
        employer_sig = crypto.sign(content_hash, employer.signing_private_key_enc)
        log.employer_signature = employer_sig
        log.employer_signed_at = now
        log.employer_decision_at = now
        log.approval_status = "approved"
        kind = "employer_approve"
    elif status == "rejected":
        log.approval_status = "rejected"
        log.employer_decision_at = now
        log.rejection_reason = REJECTION_REASON
        kind = "employer_reject"

    db.add(
        WorkLogSignatureEvent(
            worklog_id=log.id,
            kind=kind,
            actor_user_id=worker.id if kind == "employee_sign" else employer.id,
            submission_version=log.submission_version,
            content_hash=content_hash,
            signature=employee_sig if kind == "employee_sign" else log.employer_signature,
            rejection_reason=log.rejection_reason,
            canonical_payload=signing.worklog_signing_dict(log),
        )
    )


def week_monday(d: date) -> date:
    monday = d - timedelta(days=d.weekday())
    return monday


if __name__ == "__main__":
    asyncio.run(main())
