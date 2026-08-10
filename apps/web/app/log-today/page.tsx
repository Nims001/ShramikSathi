"use client";

// Log today's (or a past day's) work as a guided flow:
//
//   1. Weekly presets  — blocking page if this Sunday→Saturday week has no
//      presets yet (break days, promised payment day / daily wage).
//   2. Schedule + pay  — scheduled times (report/end/break) plus the promised
//      pay amount (on pay days or daily pay), or pieces × rate for per-piece
//      employment. The promised-vs-gotten difference is computed in background.
//   3. Timer           — live Day Start / Break / Day End timer with seconds,
//      a scheduled-break-overrun reminder and missed-break logging. A temporary
//      dev control picks the date the timer stamps against so overtime is
//      computed from the log date (the old "now" stamps caused ~700h overtime).
//   4. Payment         — after Day End, the actual payment received that day.
//   5. Sign & submit   — the employee reviews the record, confirms it is
//      accurate and signs it with their digital key (Electronic Transactions
//      Act, 2063 — asymmetric cryptosystem). The record is then locked and sent
//      to the linked employer for dual-consensus approval.
//
// `?edit=<id>` reopens a rejected record so the employee can fix a mistake and
// resubmit. Saved via the worklogs API; overtime minutes are server-computed.

// In-progress log draft (see lib/logDraft.ts) keeps a running timer and the
// values already entered alive across page navigation.

import { Suspense, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import BreakTimes, { WorkRange } from "@/components/BreakTimes";
import RequireAuth from "@/components/RequireAuth";
import EditRejectedLogForm from "@/components/EditRejectedLogForm";
import { SelectField, TextField } from "@/components/controls";
import { clearLogDraft, loadLogDraft, LOG_DRAFT_KEY, type LogDraft, type LogStatus, type LogStep } from "@/lib/logDraft";
import {
  createWorklog,
  listEmployers,
  listWeeklySettings,
  listWorklogs,
  signWorklog,
  updateWorklog,
  verifyWorklog,
  upsertWeeklySettings,
} from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { Employer, WeeklySetting, WorkLog, WorkLogVerify } from "@/lib/types";

type Status = LogStatus;
type Step = LogStep;

const DEV_TIMER_HELPER = true; // TEMPORARY dev buttons — set to false / remove before launch.
const DEV_DATE_HELPER = true; // TEMPORARY dev date shortcuts — set to false / remove before launch.

const WEEKDAY_LABELS: Record<"en" | "ne", string[]> = {
  en: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
  ne: ["सोम", "मङ्गल", "बुध", "बिही", "शुक्र", "शनि", "आइत"],
};

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function todayStr(): string {
  return new Date().toISOString().slice(0, 10);
}

function daysAgoStr(daysAgo: number): string {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - daysAgo);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

// Sunday of the current Sunday → Saturday week ("last Sunday to coming Saturday").
function sundayStr(d = new Date()): string {
  const copy = new Date(d);
  copy.setHours(0, 0, 0, 0);
  copy.setDate(copy.getDate() - copy.getDay()); // getDay(): 0 = Sunday
  return `${copy.getFullYear()}-${pad(copy.getMonth() + 1)}-${pad(copy.getDate())}`;
}

function hhmm(d: Date): string {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function hhmmss(d: Date): string {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function elapsedLabel(startedAt: Date, breakStart: Date | null, status: Status): string {
  const now = Date.now();
  let activeMs = now - startedAt.getTime();
  if (breakStart) activeMs -= now - breakStart.getTime();
  const h = Math.floor(activeMs / 3_600_000);
  const m = Math.floor((activeMs % 3_600_000) / 60_000);
  const s = Math.floor((activeMs % 60_000) / 1_000);
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

function isoFor(logDate: string, time: string): string {
  return new Date(`${logDate}T${time}`).toISOString();
}

// HH:MM of a stored ISO timestamp in the user's local timezone (for editing).
function hhmmOf(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Stamp a work start/break/end anchored to the chosen log date instead of the
// real "now", so backfilled days don't record timestamps weeks away from the
// log date (which produced ~700 h of bogus overtime). For today this is the
// current instant.
function nowStamp(logDate: string): string {
  const now = new Date();
  const local = new Date(`${logDate}T${hhmmss(now)}`);
  return local.toISOString();
}

function fmtDuration(totalMinutes: number): string {
  const m = Math.max(0, Math.round(totalMinutes));
  const h = Math.floor(m / 60);
  const mm = m % 60;
  if (h === 0) return `${mm}m`;
  if (mm === 0) return `${h}h`;
  return `${h}h ${mm}m`;
}

function scheduledBreakMinutes(start: string, end: string): number | null {
  if (!start || !end) return null;
  const [sh, sm] = start.split(":").map(Number);
  const [eh, em] = end.split(":").map(Number);
  let m = eh * 60 + em - (sh * 60 + sm);
  if (m < 0) m += 24 * 60;
  return m;
}

// In-progress log draft: the type and load/clear helpers live in
// lib/logDraft.ts so the header can show the running timer on every page.

// Shared "record status" screen shown to the employee once a log has been
// signed (awaiting employer), approved, or rejected. Rejected records carry
// the employer's message plus a link to edit & resubmit.
function StatusScreen({
  log,
  employerName,
  onVerify,
  verifyResult,
  verifyBusy,
  verifyError,
  onEditResubmit,
  t,
}: {
  log: WorkLog;
  employerName: string;
  onVerify: () => void;
  verifyResult: WorkLogVerify | null;
  verifyBusy: boolean;
  verifyError: string | null;
  onEditResubmit: () => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}) {
  const status = log.approval_status ?? "draft";

  return (
    <RequireAuth>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("log.title")}</h1>
          <p className="mt-1 text-sm text-slate-500">{t("log.timerNote")}</p>
        </div>

        <div className="card p-6 text-center">
          {status === "approved" ? (
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-2xl">
              ✓
            </div>
          ) : status === "rejected" ? (
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-rose-100 text-2xl">
              ✕
            </div>
          ) : (
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 text-2xl">
              ⏳
            </div>
          )}

          <h2 className="mt-4 text-lg font-semibold text-slate-900">
            {status === "approved"
              ? t("sign.approved")
              : status === "rejected"
                ? t("sign.rejected")
                : t("sign.waiting")}
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            {log.log_date} · {employerName}
          </p>
          <p className="mt-3 text-sm text-slate-500">
            {status === "approved"
              ? t("sign.approvedDesc")
              : status === "rejected"
                ? t("sign.rejectedDesc")
                : t("sign.sentDesc", { employer: employerName })}
          </p>

          {status === "rejected" && log.rejection_reason ? (
            <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-left">
              <p className="text-xs font-semibold text-rose-700">{t("sign.rejectionReason")}</p>
              <p className="mt-1 text-sm text-rose-800">“{log.rejection_reason}”</p>
            </div>
          ) : null}

          {verifyResult ? (
            <p
              className={`mt-4 rounded-lg px-3 py-2 text-sm ${
                verifyResult.content_hash_matches &&
                verifyResult.employee_signature_valid &&
                (status !== "approved" || verifyResult.employer_signature_valid)
                  ? "bg-emerald-50 text-emerald-800"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {verifyResult.content_hash_matches &&
              verifyResult.employee_signature_valid &&
              (status !== "approved" || verifyResult.employer_signature_valid)
                ? t("sign.verifyOk")
                : t("sign.verifyBad")}
            </p>
          ) : null}
          {verifyError ? (
            <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{verifyError}</p>
          ) : null}

          <div className="mt-5 flex flex-col gap-3">
            {status === "rejected" ? (
              <button type="button" onClick={onEditResubmit} className="btn-primary w-full px-5 py-3">
                {t("sign.editResubmit")}
              </button>
            ) : null}
            <button
              type="button"
              onClick={onVerify}
              disabled={verifyBusy}
              className="btn-secondary w-full px-5 py-3"
            >
              {verifyBusy ? t("form.saving") : t("sign.verify")}
            </button>
            <div className="flex gap-3">
              <Link href="/home" className="btn-primary flex-1 px-5 py-3">
                {t("form.done")}
              </Link>
              <Link href="/logs" className="btn-secondary flex-1 px-5 py-3">
                {t("nav.logs")}
              </Link>
            </div>
          </div>
        </div>

        {/* Legal help shown when the employer refuses to approve */}
        {status === "rejected" || status === "pending_employer" ? (
          <div className="card border-amber-200 p-5">
            <h3 className="text-base font-semibold text-slate-900">{t("sign.legal.title")}</h3>
            <p className="mt-2 text-sm text-slate-600">{t("sign.legal.p1")}</p>
            <ul className="mt-3 list-disc space-y-1.5 pl-5 text-sm text-slate-600">
              <li>{t("sign.legal.bullet1")}</li>
              <li>{t("sign.legal.bullet2")}</li>
              <li>{t("sign.legal.bullet3")}</li>
              <li>{t("sign.legal.bullet4")}</li>
            </ul>
            <p className="mt-3 text-sm text-slate-600">{t("sign.legal.p2")}</p>
          </div>
        ) : null}
      </div>
    </RequireAuth>
  );
}

function LogTodayPage() {
  const { t, lang } = useLanguage();
  const router = useRouter();
  const searchParams = useSearchParams();
  const editId = searchParams.get("edit");
  const [employers, setEmployers] = useState<Employer[]>([]);
  const [weeklySettings, setWeeklySettings] = useState<WeeklySetting[]>([]);
  const [worklogs, setWorklogs] = useState<WorkLog[]>([]);
  const [employerId, setEmployerId] = useState("");
  const [step, setStep] = useState<Step>("presets");

  const [date, setDate] = useState(todayStr());
  const [reportTime, setReportTime] = useState("");
  const [scheduledEnd, setScheduledEnd] = useState("");
  const [schedBreakStart, setSchedBreakStart] = useState("");
  const [schedBreakEnd, setSchedBreakEnd] = useState("");

  const [status, setStatus] = useState<Status>("idle");
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [breakStart, setBreakStart] = useState<Date | null>(null);
  const [endedAt, setEndedAt] = useState<Date | null>(null);
  const [breaks, setBreaks] = useState<{ start: string; end?: string }[]>([]);
  const [manualBreaks, setManualBreaks] = useState<{ start: string; end: string }[]>([
    { start: "", end: "" },
  ]);

  const [promised, setPromised] = useState("");
  const [pieces, setPieces] = useState("");
  const [pieceRate, setPieceRate] = useState("");
  const [paid, setPaid] = useState("");
  const [deductions, setDeductions] = useState<{ label: string; amount: string }[]>([
    { label: "", amount: "" },
  ]);
  const [note, setNote] = useState("");

  // Weekly presets
  const [presetBreakDays, setPresetBreakDays] = useState<string[]>([]);
  const [presetPaymentDay, setPresetPaymentDay] = useState("");
  const [presetDailyWage, setPresetDailyWage] = useState("");
  const [presetBusy, setPresetBusy] = useState(false);

  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loaded, setLoaded] = useState(false);
  // Set when a draft was restored so the presets effect below does not re-route
  // the step (and overwrite the draft's values) right after a restore.
  const skipPresetRoutingRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [, setTick] = useState(0);

  // Dual-consensus signing state.
  const [editingId, setEditingId] = useState<string | null>(null);
  const [savedLogId, setSavedLogId] = useState<string | null>(null);
  const [submittedLog, setSubmittedLog] = useState<WorkLog | null>(null);
  const [signAgreed, setSignAgreed] = useState(false);
  const [signing, setSigning] = useState(false);
  const [verifyResult, setVerifyResult] = useState<WorkLogVerify | null>(null);
  const [verifyBusy, setVerifyBusy] = useState(false);

  useEffect(() => {
    Promise.all([listEmployers(), listWeeklySettings(), listWorklogs()])
      .then(([list, settings, logs]) => {
        setEmployers(list);
        setWeeklySettings(settings);
        setWorklogs(logs);
        if (list.length === 1) setEmployerId(list[0].id);

        // Restore an in-progress draft: a running timer keeps its elapsed time
        // and the values already entered come back instead of being lost.
        const draft = loadLogDraft();
        if (draft && !editId) {
          const ownsEmployer = list.some((e) => e.id === draft.employerId);
          const alreadySigned = logs.some(
            (w) =>
              w.employer_id === draft.employerId &&
              w.log_date === draft.date &&
              w.approval_status &&
              w.approval_status !== "draft",
          );
          if (ownsEmployer && !alreadySigned) {
            skipPresetRoutingRef.current = true;
            setEmployerId(draft.employerId);
            setDate(draft.date);
            setStep(draft.step);
            setStatus(draft.status);
            setStartedAt(draft.startedAt ? new Date(draft.startedAt) : null);
            setBreakStart(draft.breakStart ? new Date(draft.breakStart) : null);
            setEndedAt(draft.endedAt ? new Date(draft.endedAt) : null);
            setBreaks(draft.breaks);
            setManualBreaks(draft.manualBreaks);
            setReportTime(draft.reportTime);
            setScheduledEnd(draft.scheduledEnd);
            setSchedBreakStart(draft.schedBreakStart);
            setSchedBreakEnd(draft.schedBreakEnd);
            setPromised(draft.promised);
            setPieces(draft.pieces);
            setPieceRate(draft.pieceRate);
            setPaid(draft.paid);
            setDeductions(draft.deductions);
            setNote(draft.note);
            setPresetBreakDays(draft.presetBreakDays);
            setPresetPaymentDay(draft.presetPaymentDay);
            setPresetDailyWage(draft.presetDailyWage);
          } else {
            clearLogDraft();
          }
        }
        setLoaded(true);
      })
      .catch(() => {
        setEmployers([]);
        setWorklogs([]);
        setLoaded(true);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep the in-progress log in localStorage as the user types / times, and
  // drop it once the entry is saved (the record then lives on the server).
  useEffect(() => {
    if (!loaded || editId || editingId != null) return;
    if (saved) {
      clearLogDraft();
      return;
    }
    const hasProgress =
      status !== "idle" ||
      startedAt != null ||
      endedAt != null ||
      breaks.length > 0 ||
      reportTime !== "" ||
      scheduledEnd !== "" ||
      schedBreakStart !== "" ||
      schedBreakEnd !== "" ||
      promised !== "" ||
      pieces !== "" ||
      pieceRate !== "" ||
      paid !== "" ||
      note !== "" ||
      deductions.some((d) => d.label || d.amount) ||
      manualBreaks.some((b) => b.start || b.end);
    if (!hasProgress) {
      clearLogDraft();
      return;
    }
    const draft: LogDraft = {
      version: 1,
      date,
      employerId,
      step,
      status,
      startedAt: startedAt ? startedAt.toISOString() : null,
      breakStart: breakStart ? breakStart.toISOString() : null,
      endedAt: endedAt ? endedAt.toISOString() : null,
      breaks,
      manualBreaks,
      reportTime,
      scheduledEnd,
      schedBreakStart,
      schedBreakEnd,
      promised,
      pieces,
      pieceRate,
      paid,
      deductions,
      note,
      presetBreakDays,
      presetPaymentDay,
      presetDailyWage,
    };
    try {
      window.localStorage.setItem(LOG_DRAFT_KEY, JSON.stringify(draft));
    } catch {
      /* storage full/unavailable — the timer still runs in memory */
    }
  }, [
    loaded,
    editId,
    editingId,
    saved,
    date,
    employerId,
    step,
    status,
    startedAt,
    breakStart,
    endedAt,
    breaks,
    manualBreaks,
    reportTime,
    scheduledEnd,
    schedBreakStart,
    schedBreakEnd,
    promised,
    pieces,
    pieceRate,
    paid,
    deductions,
    note,
    presetBreakDays,
    presetPaymentDay,
    presetDailyWage,
  ]);

  // Reopen a rejected record for editing: switch to the dedicated "Edit &
  // resend" form (a flat page, not the wizard). The form owns its own state
  // and pre-fills every stored field itself.
  useEffect(() => {
    if (!editId || worklogs.length === 0) return;
    const log = worklogs.find((w) => w.id === editId);
    if (!log) return;
    setEditingId(log.id);
    setEmployerId(log.employer_id);
    setDate(log.log_date);
    setStep("schedule");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editId, worklogs]);

  useEffect(() => {
    if (status === "idle") return;
    const id = setInterval(() => setTick((n) => n + 1), 1_000);
    return () => clearInterval(id);
  }, [status]);

  const selectedEmployer = employers.find((e) => e.id === employerId);
  const payDaily =
    selectedEmployer?.pay_unit === "daily" || selectedEmployer?.payment_frequency === "daily";
  const isPerPiece = selectedEmployer?.pay_unit === "per_piece";
  // Payment is due today when the job is paid daily or the weekly preset marks
  // this date as the promised payment day.
  const isPayDay = payDaily || (presetPaymentDay !== "" && presetPaymentDay === date);
  // Editing a rejected record shows every pay field regardless of pay schedule,
  // so the promised / received amounts are never dropped on resubmit.
  const isEditing = editingId != null;
  const editingLog = editingId ? (worklogs.find((w) => w.id === editingId) ?? null) : null;

  const thisWeekSetting = weeklySettings.find((s) => s.employer_id === employerId);
  const presetSetForWeek = !!thisWeekSetting && thisWeekSetting.week_start === sundayStr();

  // When the chosen employer changes, load this week's presets (if any) and
  // route to the blocking preset page unless presets exist for the current
  // Sunday→Saturday week. Rejected-log edits skip the presets step entirely.
  useEffect(() => {
    if (!employerId) return;
    if (skipPresetRoutingRef.current) {
      skipPresetRoutingRef.current = false;
      return;
    }
    if (editingId) {
      setStep("schedule");
      return;
    }
    const setting = weeklySettings.find((s) => s.employer_id === employerId);
    setPresetBreakDays(setting?.break_days_this_week ?? []);
    setPresetPaymentDay(setting?.promised_payment_day ?? "");
    setPresetDailyWage(setting?.daily_promised_wage != null ? String(setting.daily_promised_wage) : "");
    const emp = employers.find((e) => e.id === employerId);
    const daily = emp?.pay_unit === "daily" || emp?.payment_frequency === "daily";
    if (setting && setting.week_start === sundayStr()) {
      setStep("schedule");
      if (daily && setting.daily_promised_wage != null) {
        setPromised(String(setting.daily_promised_wage));
      }
    } else {
      setStep("presets");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employerId, weeklySettings, editingId]);

  // The record-status screen to show: a freshly signed log, or an existing
  // log for the selected employer+date that is already signed/approved/rejected.
  const statusLog = (() => {
    if (submittedLog && submittedLog.approval_status && submittedLog.approval_status !== "draft") {
      return submittedLog;
    }
    if (!editingId) {
      const existing = worklogs.find(
        (w) => w.employer_id === employerId && w.log_date === date,
      );
      if (existing && existing.approval_status && existing.approval_status !== "draft") {
        return existing;
      }
    }
    return null;
  })();

  const toggleBreakDay = (day: string) =>
    setPresetBreakDays((arr) =>
      arr.includes(day) ? arr.filter((d) => d !== day) : [...arr, day],
    );

  const savePresets = async () => {
    if (!employerId) return;
    setPresetBusy(true);
    setError(null);
    try {
      const savedSetting = await upsertWeeklySettings(employerId, {
        week_start: sundayStr(),
        break_days_this_week: presetBreakDays.length ? presetBreakDays : null,
        promised_payment_day: presetPaymentDay || null,
        daily_promised_wage: presetDailyWage !== "" ? Number(presetDailyWage) : null,
      });
      setWeeklySettings((list) => [
        ...list.filter((s) => s.employer_id !== employerId),
        savedSetting,
      ]);
      if (payDaily && savedSetting.daily_promised_wage != null) {
        setPromised(String(savedSetting.daily_promised_wage));
      }
      setStep("schedule");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setPresetBusy(false);
    }
  };

  const weekBreakDaysCount = presetBreakDays.length;
  const workDaysThisWeek = 7 - weekBreakDaysCount;
  const computedWeekly =
    payDaily && presetDailyWage !== ""
      ? Number(presetDailyWage) * workDaysThisWeek
      : null;

  const computedPromised =
    isPerPiece && pieces !== "" && pieceRate !== ""
      ? Number(pieces) * Number(pieceRate)
      : null;
  const promisedAmount = computedPromised ?? ((isPayDay || isEditing) && promised !== "" ? Number(promised) : null);
  const paidAmount = (isPayDay || isEditing) && paid !== "" ? Number(paid) : null;
  const amountDue =
    promisedAmount != null && paidAmount != null
      ? Math.max(0, Math.round((promisedAmount - paidAmount) * 100) / 100)
      : null;

  const pressStart = () => {
    setSaved(false);
    setStartedAt(new Date(nowStamp(date)));
    setEndedAt(null);
    setBreakStart(null);
    setBreaks([]);
    setStatus("working");
  };

  const pressBreak = () => {
    setSaved(false);
    if (status === "on_break") {
      const started = breakStart;
      if (started) {
        setBreaks((arr) => {
          const copy = [...arr];
          copy[copy.length - 1] = { ...copy[copy.length - 1], end: nowStamp(date) };
          return copy;
        });
      }
      setBreakStart(null);
      setStatus("working");
    } else if (status === "working") {
      setBreaks((arr) => [...arr, { start: nowStamp(date) }]);
      setBreakStart(new Date(nowStamp(date)));
      setStatus("on_break");
    }
  };

  const pressEnd = () => {
    setSaved(false);
    if (status === "on_break" && breakStart) {
      setBreaks((arr) => {
        const copy = [...arr];
        copy[copy.length - 1] = { ...copy[copy.length - 1], end: nowStamp(date) };
        return copy;
      });
      setBreakStart(null);
    }
    setEndedAt(new Date(nowStamp(date)));
    setStatus("idle");
  };

  const requestDayEnd = () => setConfirmOpen(true);

  const confirmDayEnd = () => {
    setConfirmOpen(false);
    pressEnd();
    setStep("payment");
  };

  const reset = () => {
    setStartedAt(null);
    setBreakStart(null);
    setEndedAt(null);
    setStatus("idle");
  };

  // TEMPORARY dev helper — adds minutes to the recorded times so you can test
  // overtime / duration handling without waiting. Remove before launch.
  const bumpTimes = (minutes: number) => {
    setSaved(false);
    if (endedAt) {
      setEndedAt(new Date(endedAt.getTime() + minutes * 60_000));
    } else if (startedAt) {
      setStartedAt(new Date(startedAt.getTime() - minutes * 60_000));
    }
  };

  const addManualBreak = () => {
    const row = manualBreaks[manualBreaks.length - 1];
    if (!row.start || !row.end) return;
    setSaved(false);
    setBreaks((arr) => [...arr, { start: isoFor(date, row.start), end: isoFor(date, row.end) }]);
    setManualBreaks((arr) => [...arr.slice(0, -1), { start: "", end: "" }]);
  };

  const removeBreak = (index: number) =>
    setBreaks((arr) => arr.filter((_, i) => i !== index));

  const doSubmit = async () => {
    setBusy(true);
    setError(null);
    try {
      const started = startedAt;
      const payDeductions = deductions.filter((d) => d.label || d.amount).map((d) => ({
        label: d.label,
        amount: d.amount === "" ? undefined : Number(d.amount),
      }));
      const payload = {
        employer_id: employerId,
        log_date: date,
        report_time: reportTime || null,
        scheduled_end_time: scheduledEnd || null,
        scheduled_break_start: schedBreakStart || null,
        scheduled_break_end: schedBreakEnd || null,
        work_started_at: started ? started.toISOString() : null,
        work_ended_at: endedAt ? endedAt.toISOString() : null,
        breaks: breaks.length ? breaks : null,
        piece_count: isPerPiece && pieces !== "" ? Number(pieces) : null,
        piece_rate: isPerPiece && pieceRate !== "" ? Number(pieceRate) : null,
        paid_amount: paidAmount,
        promised_amount: isPerPiece ? null : ((isPayDay || isEditing) && promised !== "" ? Number(promised) : null),
        deductions: (isPayDay || isEditing) && payDeductions.length ? payDeductions : null,
        note: note || null,
      };
      const savedLog = editingId
        ? await updateWorklog(editingId, payload)
        : await createWorklog(payload);
      setSavedLogId(savedLog.id);
      setSaved(true);
      setStep("sign");
      reset();
      setBreaks([]);
      setManualBreaks([{ start: "", end: "" }]);
      setPaid("");
      setPromised("");
      setDeductions([{ label: "", amount: "" }]);
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusy(false);
    }
  };

  const doSign = async () => {
    if (!savedLogId) return;
    setSigning(true);
    setError(null);
    try {
      const log = await signWorklog(savedLogId);
      setSubmittedLog(log);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setSigning(false);
    }
  };

  // The flat "Edit & resend" form saved the corrected record: feed its values
  // into the shared review/sign state so the sign step shows an accurate
  // summary, then advance to it.
  const handleEditSaved = (updated: WorkLog) => {
    setReportTime(updated.report_time?.slice(0, 5) ?? "");
    setScheduledEnd(updated.scheduled_end_time?.slice(0, 5) ?? "");
    setSchedBreakStart(updated.scheduled_break_start?.slice(0, 5) ?? "");
    setSchedBreakEnd(updated.scheduled_break_end?.slice(0, 5) ?? "");
    setStartedAt(updated.work_started_at ? new Date(updated.work_started_at) : null);
    setEndedAt(updated.work_ended_at ? new Date(updated.work_ended_at) : null);
    setBreaks(
      (updated.breaks ?? []).filter(
        (b): b is { start: string; end?: string } => b.start != null,
      ),
    );
    setPaid(updated.paid_amount != null ? String(updated.paid_amount) : "");
    setPromised(updated.promised_amount != null ? String(updated.promised_amount) : "");
    setPieces(updated.piece_count != null ? String(updated.piece_count) : "");
    setPieceRate(updated.piece_rate != null ? String(updated.piece_rate) : "");
    setDeductions(
      updated.deductions && updated.deductions.length > 0
        ? updated.deductions.map((d) => ({
            label: d.label ?? "",
            amount: d.amount != null ? String(d.amount) : "",
          }))
        : [{ label: "", amount: "" }],
    );
    setNote(updated.note ?? "");
    setSavedLogId(updated.id);
    setStep("sign");
  };

  const doVerify = async (logId: string) => {
    setVerifyBusy(true);
    setVerifyResult(null);
    setError(null);
    try {
      const result = await verifyWorklog(logId);
      setVerifyResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setVerifyBusy(false);
    }
  };

  const handleEditResubmit = () => {
    if (statusLog) router.push(`/log-today?edit=${statusLog.id}`);
  };

  const canSave =
    employerId &&
    (startedAt || reportTime || scheduledEnd || schedBreakStart || schedBreakEnd || paid !== "" || promised !== "" || pieces !== "" || pieceRate !== "");

  const dayLabels = WEEKDAY_LABELS[lang];

  // Scheduled break overrun reminder (shown while on break).
  const schedBreakMins = scheduledBreakMinutes(schedBreakStart, schedBreakEnd);
  const breakElapsedMins =
    status === "on_break" && breakStart ? (Date.now() - breakStart.getTime()) / 60_000 : 0;
  const overBreak =
    status === "on_break" && schedBreakMins !== null && schedBreakMins > 0 && breakElapsedMins > schedBreakMins;

  const workedMinutesTotal = (() => {
    if (startedAt && endedAt) {
      const brk = breaks.reduce(
        (sum, b) =>
          sum +
          (b.start && b.end
            ? Math.max(0, (new Date(b.end).getTime() - new Date(b.start).getTime()) / 60_000)
            : 0),
        0,
      );
      return Math.max(0, (endedAt.getTime() - startedAt.getTime()) / 60_000 - brk);
    }
    if (reportTime && scheduledEnd) {
      const [sh, sm] = reportTime.split(":").map(Number);
      const [eh, em] = scheduledEnd.split(":").map(Number);
      let m = eh * 60 + em - (sh * 60 + sm);
      if (m < 0) m += 24 * 60;
      return m;
    }
    return 0;
  })();

  if (employers.length === 0) {
    return (
      <RequireAuth>
        <div className="card p-6 text-center">
          <p className="text-sm text-slate-600">{t("home.noEmployers")}</p>
          <Link href="/add-employer" className="btn-primary mt-4 inline-block px-5 py-3">
            {t("home.addEmployer")}
          </Link>
        </div>
      </RequireAuth>
    );
  }

  // A record already sent for approval / approved / rejected takes over the
  // whole page (no editing a locked record).
  if (statusLog) {
    return (
      <StatusScreen
        log={statusLog}
        employerName={selectedEmployer?.employer_name ?? ""}
        onVerify={() => doVerify(statusLog.id)}
        verifyResult={verifyResult}
        verifyBusy={verifyBusy}
        verifyError={error}
        onEditResubmit={handleEditResubmit}
        t={t}
      />
    );
  }

  const stepIndex = { presets: 1, schedule: 2, timer: 3, payment: 4, sign: 5 }[step];

  return (
    <RequireAuth>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("log.title")}</h1>
          <p className="mt-1 text-sm text-slate-500">{t("log.timerNote")}</p>
        </div>

        {!employerId ? (
          <div className="card p-4">
            <SelectField
              label={t("log.chooseEmployer")}
              value={employerId}
              onChange={setEmployerId}
              options={employers.map((e) => ({ value: e.id, en: e.employer_name ?? "", ne: e.employer_name ?? "" }))}
            />
          </div>
        ) : (
          <>
            {/* Step indicator + employer selector (hidden while editing a rejected log) */}
            {!isEditing ? (
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <span
                      key={n}
                      className={`flex h-6 w-6 items-center justify-center rounded-full ${
                        n === stepIndex ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-400"
                      }`}
                    >
                      {n}
                    </span>
                  ))}
                </div>
                {step === "presets" || step === "schedule" ? (
                  <SelectField
                    label=""
                    value={employerId}
                    onChange={setEmployerId}
                    options={employers.map((e) => ({ value: e.id, en: e.employer_name ?? "", ne: e.employer_name ?? "" }))}
                  />
                ) : (
                  <span className="max-w-[180px] truncate text-xs font-medium text-slate-600">
                    {selectedEmployer?.employer_name ?? ""}
                  </span>
                )}
              </div>
            ) : null}

            {error ? (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
            ) : null}

            {/* Edit & resend: correct a rejected log in one flat form instead of
                the wizard. The form owns its own state; on save, the corrected
                record feeds the shared review/sign step below. */}
            {isEditing && editingLog && step !== "sign" ? (
              <EditRejectedLogForm
                log={editingLog}
                employers={employers}
                t={t}
                onSave={handleEditSaved}
                onCancel={() => router.push("/logs")}
              />
            ) : null}

            {/* ─── Step 1: weekly presets (blocking) ─────────────────────── */}
            {!isEditing && step === "presets" ? (
              <section className="card p-4">
                <h2 className="text-lg font-semibold text-slate-900">{t("preset.blocking.title")}</h2>
                <p className="mt-1 text-sm text-slate-500">{t("preset.blocking.desc")}</p>
                <div className="mt-4 space-y-4">
                  <p className="text-xs text-slate-500">{t("preset.desc")}</p>
                  <div>
                    <p className="mb-1.5 text-sm font-medium text-slate-700">{t("preset.breakDays")}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {dayLabels.map((label, i) => {
                        const day = String(i);
                        const on = presetBreakDays.includes(day);
                        return (
                          <button
                            key={day}
                            type="button"
                            aria-pressed={on}
                            onClick={() => toggleBreakDay(day)}
                            className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
                              on
                                ? "border-brand-500 bg-brand-50 font-medium text-brand-700"
                                : "border-slate-300 bg-white text-slate-600"
                            }`}
                          >
                            {label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {payDaily ? (
                    <TextField
                      label={t("preset.dailyWage")}
                      type="number"
                      inputMode="decimal"
                      min={0}
                      value={presetDailyWage}
                      onChange={setPresetDailyWage}
                    />
                  ) : (
                    <TextField
                      label={t("preset.paymentDay")}
                      type="date"
                      value={presetPaymentDay}
                      onChange={setPresetPaymentDay}
                    />
                  )}

                  {computedWeekly != null ? (
                    <p className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-800">
                      {t("preset.computedWeekly")}: रू {computedWeekly.toLocaleString("en-IN")}
                    </p>
                  ) : null}

                  <button
                    type="button"
                    onClick={savePresets}
                    disabled={presetBusy}
                    className="btn-primary w-full"
                  >
                    {presetBusy ? t("form.saving") : t("preset.save")}
                  </button>
                </div>
              </section>
            ) : null}

            {/* ─── Step 2: scheduled times + promised pay ────────────────── */}
            {!isEditing && step === "schedule" ? (
              <section className="card p-4">
                <h2 className="text-lg font-semibold text-slate-900">{t("schedule.title")}</h2>
                <p className="mt-1 text-sm text-slate-500">{t("schedule.desc")}</p>
                <div className="mt-4 space-y-3">
                  <TextField label={t("log.backfillDate")} type="date" value={date} onChange={setDate} />
                  <div className="grid grid-cols-2 gap-3">
                    <TextField label={t("log.reportTime")} type="time" value={reportTime} onChange={setReportTime} />
                    <TextField label={t("log.scheduledEnd")} type="time" value={scheduledEnd} onChange={setScheduledEnd} />
                    <TextField label={t("log.scheduledBreakStart")} type="time" value={schedBreakStart} onChange={setSchedBreakStart} />
                    <TextField label={t("log.scheduledBreakEnd")} type="time" value={schedBreakEnd} onChange={setSchedBreakEnd} />
                  </div>

                  {isPayDay || isPerPiece || isEditing ? (
                    <div className="rounded-xl border border-slate-200 p-3">
                      <p className="mb-3 text-xs text-slate-500">{t("schedule.payNote")}</p>
                      {isPerPiece ? (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-3">
                            <TextField label={t("pay.pieces")} type="number" inputMode="numeric" min={0} value={pieces} onChange={setPieces} />
                            <TextField label={t("pay.pieceRate")} type="number" inputMode="decimal" min={0} value={pieceRate} onChange={setPieceRate} />
                          </div>
                          {computedPromised != null ? (
                            <p className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-800">
                              {t("pay.promisedComputed")}: रू {computedPromised.toLocaleString("en-IN")}
                            </p>
                          ) : null}
                          <TextField label={t("pay.totalPaid")} type="number" inputMode="decimal" min={0} value={paid} onChange={setPaid} />
                        </div>
                      ) : (
                        <TextField
                          label={t("log.promised")}
                          type="number"
                          inputMode="decimal"
                          min={0}
                          value={promised}
                          onChange={setPromised}
                        />
                      )}
                    </div>
                  ) : null}

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setStep("presets")}
                      className="btn-secondary flex-1"
                    >
                      {t("form.back")}
                    </button>
                    <button type="button" onClick={() => setStep("timer")} className="btn-primary flex-1">
                      {t("schedule.continue")}
                    </button>
                  </div>
                </div>
              </section>
            ) : null}

            {/* ─── Step 3: timer ─────────────────────────────────────────── */}
            {!isEditing && step === "timer" ? (
              <section className="card p-4 text-center">
                <p className="text-xs text-slate-500">{t("timer.title")}</p>
                <p className="mb-3 text-4xl font-bold tabular-nums text-slate-900">
                  {status === "idle"
                    ? endedAt
                      ? t("log.ended", { time: hhmm(endedAt) })
                      : "00:00:00"
                    : startedAt
                      ? elapsedLabel(startedAt, breakStart, status)
                      : "00:00:00"}
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {status === "idle" ? (
                    <>
                      <button
                        type="button"
                        onClick={pressStart}
                        className="col-span-1 rounded-xl bg-brand-700 px-3 py-3 text-sm font-semibold text-white active:bg-brand-800"
                      >
                        {t("timer.dayStart")}
                      </button>
                      <span className="col-span-2 flex items-center justify-center text-xs text-slate-400">
                        {endedAt && startedAt
                          ? t("log.started", { time: hhmm(startedAt) })
                          : ""}
                      </span>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={pressBreak}
                        className={`rounded-xl px-3 py-3 text-sm font-semibold ${
                          status === "on_break"
                            ? "bg-brand-700 text-white active:bg-brand-800"
                            : "border border-amber-500 text-amber-700 active:bg-amber-50"
                        }`}
                      >
                        {status === "on_break" ? t("log.breakEnd") : t("log.breakStart")}
                      </button>
                      <button
                        type="button"
                        onClick={requestDayEnd}
                        className="rounded-xl bg-rose-600 px-3 py-3 text-sm font-semibold text-white active:bg-rose-700"
                      >
                        {t("timer.dayEnd")}
                      </button>
                      <span className="flex items-center justify-center text-xs text-slate-500">
                        {status === "on_break" && breakStart
                          ? t("log.onBreak", { time: hhmm(breakStart) })
                          : startedAt
                            ? t("log.running", { time: hhmm(startedAt) })
                            : ""}
                      </span>
                    </>
                  )}
                </div>

                {overBreak ? (
                  <div className="mt-3 rounded-xl border border-amber-300 bg-amber-50 px-3 py-2.5 text-sm font-medium text-amber-800">
                    ⏱ {t("timer.breakReminder", { minutes: schedBreakMins })}
                  </div>
                ) : null}

                {/* Missed breaks */}
                <div className="mt-5 border-t border-slate-100 pt-4 text-left">
                  <p className="mb-3 text-sm font-semibold text-slate-800">{t("log.addMissedBreak")}</p>
                  <div className="space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <TextField
                        label={t("log.breakTimeStart")}
                        type="time"
                        value={manualBreaks[manualBreaks.length - 1].start}
                        onChange={(v) =>
                          setManualBreaks((arr) => [
                            ...arr.slice(0, -1),
                            { ...arr[arr.length - 1], start: v },
                          ])
                        }
                      />
                      <TextField
                        label={t("log.breakTimeEnd")}
                        type="time"
                        value={manualBreaks[manualBreaks.length - 1].end}
                        onChange={(v) =>
                          setManualBreaks((arr) => [
                            ...arr.slice(0, -1),
                            { ...arr[arr.length - 1], end: v },
                          ])
                        }
                      />
                    </div>
                    <button
                      type="button"
                      onClick={addManualBreak}
                      disabled={!manualBreaks[manualBreaks.length - 1].start || !manualBreaks[manualBreaks.length - 1].end}
                      className="text-sm font-medium text-brand-700 disabled:opacity-40"
                    >
                      + {t("log.addBreak")}
                    </button>
                  </div>
                  {breaks.length > 0 ? (
                    <ul className="mt-3 space-y-1.5">
                      {breaks.map((b, i) => (
                        <li
                          key={i}
                          className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700"
                        >
                          <span className="tabular-nums">
                            {b.start ? hhmm(new Date(b.start)) : ""}
                            {b.end ? ` → ${hhmm(new Date(b.end))}` : " → …"}
                          </span>
                          <button
                            type="button"
                            onClick={() => removeBreak(i)}
                            className="text-xs font-medium text-rose-600"
                          >
                            {t("profile.delete")}
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>

                {DEV_TIMER_HELPER ? (
                  <div className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-400">
                    <button
                      type="button"
                      onClick={() => bumpTimes(5)}
                      className="mr-3 font-medium underline"
                    >
                      [dev] +5 min
                    </button>
                    {status === "idle" && !startedAt ? (
                      <button
                        type="button"
                        onClick={() => {
                          setSaved(false);
                          setStep("payment");
                        }}
                        className="font-medium text-brand-700 underline"
                      >
                        {t("timer.skip")}
                      </button>
                    ) : null}
                  </div>
                ) : status === "idle" && !startedAt ? (
                  <button
                    type="button"
                    onClick={() => {
                      setSaved(false);
                      setStep("payment");
                    }}
                    className="mt-4 text-xs font-medium text-brand-700 underline"
                  >
                    {t("timer.skip")}
                  </button>
                ) : null}
              </section>
            ) : null}

            {/* ─── Step 4: payment after day end ─────────────────────────── */}
            {!isEditing && step === "payment" ? (
              <section className="card p-4">
                <h2 className="text-lg font-semibold text-slate-900">{t("pay.title", { date })}</h2>
                <p className="mt-1 text-sm text-slate-500">{t("pay.summary")}</p>

                <div className="mt-4 space-y-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
                  <div className="flex items-start justify-between">
                    <span className="text-slate-500">{t("logs.worked")}</span>
                    <div className="text-right">
                      <span className="font-medium tabular-nums">{fmtDuration(workedMinutesTotal)}</span>
                      {startedAt && endedAt ? (
                        <WorkRange start={startedAt.toISOString()} end={endedAt.toISOString()} />
                      ) : null}
                    </div>
                  </div>
                  {reportTime || scheduledEnd ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("pay.scheduled")}</span>
                      <span className="tabular-nums">
                        {[reportTime, scheduledEnd].filter(Boolean).join(" → ") || "—"}
                      </span>
                    </div>
                  ) : null}
                  {promisedAmount != null ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("log.promised")}</span>
                      <span className="font-medium tabular-nums">रू {promisedAmount.toLocaleString("en-IN")}</span>
                    </div>
                  ) : null}
                  {paidAmount != null ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("home.paid")}</span>
                      <span className="font-medium tabular-nums">रू {paidAmount.toLocaleString("en-IN")}</span>
                    </div>
                  ) : null}
                  {amountDue != null ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("pay.due")}</span>
                      <span className="font-semibold tabular-nums text-rose-700">
                        रू {amountDue.toLocaleString("en-IN")}
                      </span>
                    </div>
                  ) : null}
                </div>

                <div className="mt-4 space-y-3">
                  {isPayDay || isEditing ? (
                    <>
                      <TextField label={t("pay.actual")} type="number" inputMode="decimal" min={0} value={paid} onChange={setPaid} />
                      <div>
                        <p className="mb-1.5 text-sm font-medium text-slate-800">{t("log.addDeduction")}</p>
                        <div className="space-y-2">
                          {deductions.map((d, i) => (
                            <div key={i} className="grid grid-cols-2 gap-2">
                              <TextField
                                label={t("log.deductionLabel")}
                                value={d.label}
                                onChange={(v) =>
                                  setDeductions((arr) =>
                                    arr.map((x, j) => (j === i ? { ...x, label: v } : x)),
                                  )
                                }
                              />
                              <TextField
                                label={t("log.deductionAmount")}
                                type="number"
                                inputMode="decimal"
                                min={0}
                                value={d.amount}
                                onChange={(v) =>
                                  setDeductions((arr) =>
                                    arr.map((x, j) => (j === i ? { ...x, amount: v } : x)),
                                  )
                                }
                              />
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={() => setDeductions((arr) => [...arr, { label: "", amount: "" }])}
                            className="text-sm font-medium text-brand-700"
                          >
                            + {t("log.addDeduction")}
                          </button>
                        </div>
                      </div>
                    </>
                  ) : null}

                  <TextField label={t("log.note")} value={note} onChange={setNote} />

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => setStep("timer")}
                      className="btn-secondary flex-1"
                    >
                      {t("form.back")}
                    </button>
                    <button
                      type="button"
                      onClick={doSubmit}
                      disabled={busy || !canSave}
                      className="btn-primary flex-1"
                    >
                      {busy ? t("form.saving") : t("log.save")}
                    </button>
                  </div>
                </div>
              </section>
            ) : null}

            {/* ─── Step 5: review, approve & sign before sending ─────────── */}
            {step === "sign" ? (
              <section className="card p-4">
                <h2 className="text-lg font-semibold text-slate-900">{t("sign.title")}</h2>
                <p className="mt-1 text-sm text-slate-500">{t("sign.subtitle")}</p>

                <div className="mt-4 space-y-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700">
                  <div className="flex items-start justify-between">
                    <span className="text-slate-500">{t("logs.worked")}</span>
                    <div className="text-right">
                      <span className="font-medium tabular-nums">{fmtDuration(workedMinutesTotal)}</span>
                      {startedAt && endedAt ? (
                        <WorkRange start={startedAt.toISOString()} end={endedAt.toISOString()} />
                      ) : null}
                    </div>
                  </div>
                  {reportTime || scheduledEnd ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("pay.scheduled")}</span>
                      <span className="tabular-nums">
                        {[reportTime, scheduledEnd].filter(Boolean).join(" → ") || "—"}
                      </span>
                    </div>
                  ) : null}
                  {breaks.length > 0 ? (
                    <div className="flex items-start justify-between gap-3">
                      <span className="text-slate-500">{t("logs.break")}</span>
                      <BreakTimes breaks={breaks} />
                    </div>
                  ) : null}
                  {promisedAmount != null ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("log.promised")}</span>
                      <span className="font-medium tabular-nums">रू {promisedAmount.toLocaleString("en-IN")}</span>
                    </div>
                  ) : null}
                  {paidAmount != null ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("home.paid")}</span>
                      <span className="font-medium tabular-nums">रू {paidAmount.toLocaleString("en-IN")}</span>
                    </div>
                  ) : null}
                  {amountDue != null ? (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("pay.due")}</span>
                      <span className="font-semibold tabular-nums text-rose-700">
                        रू {amountDue.toLocaleString("en-IN")}
                      </span>
                    </div>
                  ) : null}
                </div>

                <div className="mt-4 rounded-xl border border-brand-200 bg-brand-50 p-3 text-sm text-brand-900">
                  <p>{t("sign.intro")}</p>
                  <p className="mt-2 text-xs text-brand-800">{t("sign.verifyNote")}</p>
                </div>

                {editingId ? (
                  <p className="mt-3 text-sm text-slate-600">{t("sign.editHint")}</p>
                ) : null}

                <label className="mt-4 flex items-start gap-2.5 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={signAgreed}
                    onChange={(e) => setSignAgreed(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span>{t("sign.agree")}</span>
                </label>

                <div className="mt-5 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setStep(isEditing ? "schedule" : "payment")}
                    className="btn-secondary flex-1"
                  >
                    {t("form.back")}
                  </button>
                  <button
                    type="button"
                    onClick={doSign}
                    disabled={signing || !signAgreed || !savedLogId}
                    className="btn-primary flex-1"
                  >
                    {signing ? t("form.saving") : t("sign.signBtn")}
                  </button>
                </div>
              </section>
            ) : null}
          </>
        )}

        {confirmOpen ? (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="card w-full max-w-sm p-5">
              <h2 className="text-lg font-semibold text-slate-900">{t("log.confirmTitle")}</h2>
              <p className="mt-2 text-sm text-slate-600">
                {t("log.confirmBody", { date })}
              </p>
              <div className="mt-5 flex gap-3">
                <button
                  type="button"
                  onClick={() => setConfirmOpen(false)}
                  className="btn-secondary flex-1"
                >
                  {t("log.confirmCancel")}
                </button>
                <button
                  type="button"
                  onClick={confirmDayEnd}
                  className="btn-primary flex-1"
                >
                  {t("log.confirmSave")}
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </RequireAuth>
  );
}

// `useSearchParams` (the ?edit=rejected-log flow) requires a Suspense boundary
// so the page can still be statically prerendered.
export default function LogTodayPageWithSuspense() {
  return (
    <Suspense fallback={<div className="flex h-40 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" /></div>}>
      <LogTodayPage />
    </Suspense>
  );
}
