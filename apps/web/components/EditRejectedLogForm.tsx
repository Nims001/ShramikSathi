"use client";

// Edit & resend: a single flat form for correcting a rejected work log.
//
// Unlike the regular 5-step logging wizard (presets → schedule → timer →
// payment → sign), this form shows every stored field at once, pre-filled,
// with no timer buttons. The employee fixes what the employer asked and sends
// it back for review + signature. This form owns its own state, so the wizard
// is never entered for a resubmission.

import { useState, type FormEvent } from "react";

import { SelectField, TextField } from "@/components/controls";
import { updateWorklog } from "@/lib/api";
import type { Employer, WorkLog } from "@/lib/types";

type T = (key: string, vars?: Record<string, string | number>) => string;

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function hhmmOf(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function isoFor(logDate: string, time: string): string {
  return new Date(`${logDate}T${time}`).toISOString();
}

export default function EditRejectedLogForm({
  log,
  employers,
  t,
  onSave,
  onCancel,
}: {
  log: WorkLog;
  employers: Employer[];
  t: T;
  onSave: (updated: WorkLog) => void;
  onCancel: () => void;
}) {
  const [employerId, setEmployerId] = useState(log.employer_id);
  const [date, setDate] = useState(log.log_date);
  const [reportTime, setReportTime] = useState(log.report_time?.slice(0, 5) ?? "");
  const [scheduledEnd, setScheduledEnd] = useState(log.scheduled_end_time?.slice(0, 5) ?? "");
  const [schedBreakStart, setSchedBreakStart] = useState(
    log.scheduled_break_start?.slice(0, 5) ?? "",
  );
  const [schedBreakEnd, setSchedBreakEnd] = useState(log.scheduled_break_end?.slice(0, 5) ?? "");
  const [actualStart, setActualStart] = useState(hhmmOf(log.work_started_at));
  const [actualEnd, setActualEnd] = useState(hhmmOf(log.work_ended_at));
  const [breakRows, setBreakRows] = useState<{ start: string; end: string }[]>(
    log.breaks && log.breaks.length > 0
      ? log.breaks.map((b) => ({ start: hhmmOf(b.start), end: hhmmOf(b.end) }))
      : [{ start: "", end: "" }],
  );
  const [promised, setPromised] = useState(
    log.promised_amount != null ? String(log.promised_amount) : "",
  );
  const [paid, setPaid] = useState(log.paid_amount != null ? String(log.paid_amount) : "");
  const [pieces, setPieces] = useState(log.piece_count != null ? String(log.piece_count) : "");
  const [pieceRate, setPieceRate] = useState(
    log.piece_rate != null ? String(log.piece_rate) : "",
  );
  const [deductions, setDeductions] = useState<{ label: string; amount: string }[]>(
    log.deductions && log.deductions.length > 0
      ? log.deductions.map((d) => ({
          label: d.label ?? "",
          amount: d.amount != null ? String(d.amount) : "",
        }))
      : [{ label: "", amount: "" }],
  );
  const [note, setNote] = useState(log.note ?? "");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const employer = employers.find((e) => e.id === employerId);
  const isPerPiece = employer?.pay_unit === "per_piece";

  const updateBreakRow = (index: number, patch: Partial<{ start: string; end: string }>) =>
    setBreakRows((rows) => rows.map((r, i) => (i === index ? { ...r, ...patch } : r)));

  const addBreakRow = () => setBreakRows((rows) => [...rows, { start: "", end: "" }]);

  const removeBreakRow = (index: number) =>
    setBreakRows((rows) =>
      rows.length === 1 ? [{ start: "", end: "" }] : rows.filter((_, i) => i !== index),
    );

  const updateDeduction = (index: number, patch: Partial<{ label: string; amount: string }>) =>
    setDeductions((rows) => rows.map((r, i) => (i === index ? { ...r, ...patch } : r)));

  const addDeduction = () => setDeductions((rows) => [...rows, { label: "", amount: "" }]);

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const updated = await updateWorklog(log.id, {
        employer_id: employerId,
        log_date: date,
        report_time: reportTime || null,
        scheduled_end_time: scheduledEnd || null,
        scheduled_break_start: schedBreakStart || null,
        scheduled_break_end: schedBreakEnd || null,
        work_started_at: actualStart ? isoFor(date, actualStart) : null,
        work_ended_at: actualEnd ? isoFor(date, actualEnd) : null,
        breaks: breakRows.filter((r) => r.start).length
          ? breakRows
              .filter((r) => r.start)
              .map((r) => ({
                start: isoFor(date, r.start),
                end: r.end ? isoFor(date, r.end) : undefined,
              }))
          : null,
        piece_count: isPerPiece && pieces !== "" ? Number(pieces) : null,
        piece_rate: isPerPiece && pieceRate !== "" ? Number(pieceRate) : null,
        paid_amount: paid !== "" ? Number(paid) : null,
        promised_amount: isPerPiece ? null : promised !== "" ? Number(promised) : null,
        deductions: deductions.filter((d) => d.label || d.amount).length
          ? deductions
              .filter((d) => d.label || d.amount)
              .map((d) => ({
                label: d.label,
                amount: d.amount === "" ? undefined : Number(d.amount),
              }))
          : null,
        note: note || null,
      });
      onSave(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={save} className="space-y-4">
      {log.rejection_reason ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5">
          <p className="text-xs font-semibold text-rose-700">{t("sign.rejectionReason")}</p>
          <p className="mt-0.5 text-sm text-rose-800">“{log.rejection_reason}”</p>
        </div>
      ) : null}

      {error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}

      <div className="card p-4">
        <SelectField
          label={t("log.chooseEmployer")}
          value={employerId}
          onChange={setEmployerId}
          options={employers.map((e) => ({
            value: e.id,
            en: e.employer_name ?? "",
            ne: e.employer_name ?? "",
          }))}
        />
        <div className="mt-3">
          <TextField label={t("log.backfillDate")} type="date" value={date} onChange={setDate} />
        </div>
      </div>

      <section className="card p-4">
        <h2 className="text-sm font-semibold text-slate-900">{t("log.schedTimes")}</h2>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <TextField label={t("log.reportTime")} type="time" value={reportTime} onChange={setReportTime} />
          <TextField label={t("log.scheduledEnd")} type="time" value={scheduledEnd} onChange={setScheduledEnd} />
          <TextField label={t("log.scheduledBreakStart")} type="time" value={schedBreakStart} onChange={setSchedBreakStart} />
          <TextField label={t("log.scheduledBreakEnd")} type="time" value={schedBreakEnd} onChange={setSchedBreakEnd} />
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold text-slate-900">{t("log.actualTimes")}</h2>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <TextField label={t("log.actualStart")} type="time" value={actualStart} onChange={setActualStart} />
          <TextField label={t("log.actualEnd")} type="time" value={actualEnd} onChange={setActualEnd} />
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold text-slate-900">{t("log.breaksTaken")}</h2>
        <div className="mt-3 space-y-2">
          {breakRows.map((row, i) => (
            <div key={i} className="grid grid-cols-[1fr_1fr_auto] items-end gap-2">
              <TextField label={t("log.breakStart")} type="time" value={row.start} onChange={(v) => updateBreakRow(i, { start: v })} />
              <TextField label={t("log.breakEnd")} type="time" value={row.end} onChange={(v) => updateBreakRow(i, { end: v })} />
              <button
                type="button"
                onClick={() => removeBreakRow(i)}
                className="h-11 rounded-lg border border-slate-300 px-3 text-sm font-medium text-rose-600"
              >
                {t("profile.delete")}
              </button>
            </div>
          ))}
        </div>
        <button type="button" onClick={addBreakRow} className="mt-2 text-sm font-medium text-brand-700">
          + {t("log.addBreak")}
        </button>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-semibold text-slate-900">{t("log.payDetails")}</h2>
        <div className="mt-3 space-y-3">
          {isPerPiece ? (
            <div className="grid grid-cols-2 gap-3">
              <TextField label={t("pay.pieces")} type="number" inputMode="numeric" min={0} value={pieces} onChange={setPieces} />
              <TextField label={t("pay.pieceRate")} type="number" inputMode="decimal" min={0} value={pieceRate} onChange={setPieceRate} />
            </div>
          ) : (
            <TextField label={t("log.promised")} type="number" inputMode="decimal" min={0} value={promised} onChange={setPromised} />
          )}
          <TextField label={t("pay.totalPaid")} type="number" inputMode="decimal" min={0} value={paid} onChange={setPaid} />
          <div>
            <p className="mb-1.5 text-sm font-medium text-slate-800">{t("log.addDeduction")}</p>
            <div className="space-y-2">
              {deductions.map((d, i) => (
                <div key={i} className="grid grid-cols-2 gap-2">
                  <TextField label={t("log.deductionLabel")} value={d.label} onChange={(v) => updateDeduction(i, { label: v })} />
                  <TextField label={t("log.deductionAmount")} type="number" inputMode="decimal" min={0} value={d.amount} onChange={(v) => updateDeduction(i, { amount: v })} />
                </div>
              ))}
            </div>
            <button type="button" onClick={addDeduction} className="mt-2 text-sm font-medium text-brand-700">
              + {t("log.addDeduction")}
            </button>
          </div>
        </div>
      </section>

      <section className="card p-4">
        <TextField label={t("log.note")} value={note} onChange={setNote} />
      </section>

      <div className="flex gap-3">
        <button type="button" onClick={onCancel} className="btn-secondary flex-1">
          {t("form.cancel")}
        </button>
        <button type="submit" disabled={busy} className="btn-primary flex-1">
          {busy ? t("form.saving") : t("log.saveReview")}
        </button>
      </div>
    </form>
  );
}
