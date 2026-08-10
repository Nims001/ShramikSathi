"use client";

// Employer portal: full view of one linked worker's work logs, with the
// dual-consensus approval controls. Records the worker signed and submitted
// (`pending_employer`) can be approved — which verifies the worker's digital
// signature and adds the employer's own — or rejected with a short message.

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import BreakTimes, { WorkRange } from "@/components/BreakTimes";
import RequireEmployer from "@/components/RequireEmployer";
import { approveLog, getEmployeeLogs, rejectLog } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { EmployeeLog } from "@/lib/types";

function money(n: number | undefined): string {
  return (n ?? 0).toLocaleString("en-IN");
}

function fmtTime(v: string | null | undefined): string {
  if (!v) return "—";
  return v.slice(0, 5);
}

function fmtDuration(totalMinutes: number): string {
  const m = Math.max(0, Math.round(totalMinutes));
  const h = Math.floor(m / 60);
  const mm = m % 60;
  if (h === 0) return `${mm}m`;
  if (mm === 0) return `${h}h`;
  return `${h}h ${mm}m`;
}

function workedMinutes(log: EmployeeLog): number {
  if (log.work_started_at && log.work_ended_at) {
    return (
      (new Date(log.work_ended_at).getTime() - new Date(log.work_started_at).getTime()) /
      60000
    );
  }
  if (log.report_time && log.scheduled_end_time) {
    const [sh, sm] = log.report_time.split(":").map(Number);
    const [eh, em] = log.scheduled_end_time.split(":").map(Number);
    let mins = eh * 60 + em - (sh * 60 + sm);
    if (mins < 0) mins += 24 * 60;
    return mins;
  }
  return 0;
}

function StatusBadge({ log, t }: { log: EmployeeLog; t: (k: string) => string }) {
  if (log.approval_status === "approved") {
    return (
      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
        ✓ {t("employer.approved")}
      </span>
    );
  }
  if (log.approval_status === "rejected") {
    return (
      <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
        ✕ {t("employer.rejected")}
      </span>
    );
  }
  if (log.approval_status === "pending_employer") {
    return (
      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
        ⏳ {t("employer.pendingApproval")}
      </span>
    );
  }
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-500">
      {t("employer.waitingTitle")}
    </span>
  );
}

export default function EmployeeLogsPage() {
  const { t } = useLanguage();
  const params = useParams<{ id: string }>();
  const employeeId = params.id;

  const [logs, setLogs] = useState<EmployeeLog[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [rejectFor, setRejectFor] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [agreed, setAgreed] = useState<Set<string>>(new Set());

  const load = useCallback(() => {
    getEmployeeLogs(employeeId)
      .then(setLogs)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed"));
  }, [employeeId]);

  useEffect(() => {
    load();
  }, [load]);

  const patchLog = (updated: EmployeeLog) =>
    setLogs((list) => (list ?? []).map((l) => (l.log_id === updated.log_id ? updated : l)));

  const toggleAgree = (logId: string) =>
    setAgreed((s) => {
      const next = new Set(s);
      if (next.has(logId)) next.delete(logId);
      else next.add(logId);
      return next;
    });

  const handleApprove = async (log: EmployeeLog) => {
    setBusyId(log.log_id);
    setError(null);
    setNotice(null);
    try {
      const updated = await approveLog(employeeId, log.log_id);
      patchLog(updated);
      setNotice(t("employer.approveSuccess"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusyId(null);
    }
  };

  const handleReject = async (log: EmployeeLog) => {
    if (!rejectReason.trim()) {
      setNotice(null);
      setError(t("employer.rejectRequired"));
      return;
    }
    setBusyId(log.log_id);
    setError(null);
    setNotice(null);
    try {
      const updated = await rejectLog(employeeId, log.log_id, rejectReason.trim());
      patchLog(updated);
      setRejectFor(null);
      setRejectReason("");
      setNotice(t("employer.rejectSuccess"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <RequireEmployer>
      <div className="mx-auto flex min-h-dvh w-full max-w-md flex-col bg-[#F8FAFC] shadow-soft-lg sm:border-x sm:border-slate-200">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="flex items-center justify-between px-4 py-3">
            <Link
              href="/employer"
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600"
            >
              ← {t("employer.back")}
            </Link>
            <h1 className="text-lg font-bold text-slate-900">{t("employer.logsTitle")}</h1>
            <span className="w-[76px]" />
          </div>
        </header>

        <main className="flex-1 space-y-3 px-4 py-6">
          {error ? (
            <div className="card p-5 text-center">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          ) : null}
          {notice ? (
            <div className="card p-5 text-center">
              <p className="text-sm font-medium text-emerald-800">{notice}</p>
            </div>
          ) : null}
          {logs === null ? (
            <div className="flex h-24 items-center justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
            </div>
          ) : logs.length === 0 ? (
            <div className="card p-5 text-center">
              <p className="text-sm text-slate-600">{t("employer.noLogs")}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div key={log.log_id} className="card p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-semibold text-slate-900">{log.log_date}</p>
                    <StatusBadge log={log} t={(k) => t(k)} />
                  </div>
                  <p className="mt-1 text-xs text-slate-500">
                    {log.workplace_name ?? "—"}
                    {log.workplace_district ? ` · ${log.workplace_district}` : ""}
                  </p>

                  <div className="mt-3 space-y-1.5 border-t border-slate-100 pt-3 text-sm text-slate-700">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">{t("employer.scheduled")}</span>
                      <span className="tabular-nums">
                        {fmtTime(log.report_time)} → {fmtTime(log.scheduled_end_time)}
                      </span>
                    </div>
                    {log.scheduled_break_start || log.scheduled_break_end ? (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">{t("employer.scheduledBreak")}</span>
                        <span className="tabular-nums">
                          {fmtTime(log.scheduled_break_start)} → {fmtTime(log.scheduled_break_end)}
                        </span>
                      </div>
                    ) : null}
                      <div className="flex items-start justify-between">
                        <span className="text-slate-500">{t("employer.worked")}</span>
                        <div className="text-right">
                          <span className="font-medium tabular-nums">{fmtDuration(workedMinutes(log))}</span>
                          <WorkRange start={log.work_started_at} end={log.work_ended_at} />
                        </div>
                      </div>
                    {(log.breaks ?? []).length > 0 ? (
                      <div className="flex items-start justify-between gap-3">
                        <span className="text-slate-500">{t("employer.breaks")}</span>
                        <BreakTimes breaks={log.breaks ?? []} />
                      </div>
                    ) : null}
                    {log.overtime_minutes > 0 ? (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">{t("employer.overtime")}</span>
                        <span className="font-medium tabular-nums text-amber-700">
                          {fmtDuration(log.overtime_minutes)}
                        </span>
                      </div>
                    ) : null}
                    {log.promised_amount != null ? (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">{t("home.promised")}</span>
                        <span className="font-medium tabular-nums">रू {money(log.promised_amount)}</span>
                      </div>
                    ) : null}
                    {log.paid_amount != null ? (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-500">{t("home.paid")}</span>
                        <span className="font-medium tabular-nums">रू {money(log.paid_amount)}</span>
                      </div>
                    ) : null}
                    {log.deductions && log.deductions.length > 0 ? (
                      <div className="flex items-start justify-between gap-3">
                        <span className="text-slate-500">{t("employer.deductions")}</span>
                        <span className="tabular-nums text-xs">
                          {(log.deductions ?? [])
                            .map((d) => `${d.label ?? ""}${d.amount != null ? ` रू${d.amount}` : ""}`)
                            .filter(Boolean)
                            .join(", ")}
                        </span>
                      </div>
                    ) : null}
                  </div>

                  {log.note ? (
                    <p className="mt-2 text-xs italic text-slate-500">“{log.note}”</p>
                  ) : null}

                  {log.approval_status === "pending_employer" ? (
                    <div className="mt-3 border-t border-slate-100 pt-3">
                      <p className="mb-2 text-xs font-semibold text-slate-700">
                        {t("employer.signedByWorker")}
                      </p>
                      {rejectFor === log.log_id ? (
                        <div className="space-y-2">
                          <textarea
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder={t("employer.rejectReasonHint")}
                            rows={2}
                            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-rose-400 focus:outline-none focus:ring-2 focus:ring-rose-400/20"
                          />
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setRejectFor(null);
                                setRejectReason("");
                              }}
                              className="btn-secondary flex-1 px-3 py-2 text-sm"
                            >
                              {t("form.back")}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleReject(log)}
                              disabled={busyId === log.log_id}
                              className="flex-1 rounded-lg bg-rose-600 px-3 py-2 text-sm font-semibold text-white active:bg-rose-700"
                            >
                              {busyId === log.log_id ? t("form.saving") : t("employer.reject")}
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-3 space-y-3">
                          <div className="rounded-xl border border-brand-200 bg-brand-50 p-3 text-sm text-brand-900">
                            <p>{t("employer.agreeIntro")}</p>
                            <p className="mt-2 text-xs text-brand-800">{t("employer.agreeNote")}</p>
                          </div>
                          <label className="flex items-start gap-2.5 text-sm text-slate-700">
                            <input
                              type="checkbox"
                              checked={agreed.has(log.log_id)}
                              onChange={() => toggleAgree(log.log_id)}
                              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                            />
                            <span>{t("employer.agree")}</span>
                          </label>
                          <div className="flex gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setRejectFor(log.log_id);
                                setError(null);
                              }}
                              disabled={busyId === log.log_id}
                              className="flex-1 rounded-lg border border-rose-300 px-3 py-2 text-sm font-semibold text-rose-700 active:bg-rose-50"
                            >
                              {t("employer.reject")}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleApprove(log)}
                              disabled={busyId === log.log_id || !agreed.has(log.log_id)}
                              className="flex-1 rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white active:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              {busyId === log.log_id ? t("form.saving") : t("employer.approve")}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : null}

                  {log.approval_status === "rejected" && log.rejection_reason ? (
                    <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2">
                      <p className="text-[11px] font-semibold text-rose-600">{t("logs.rejection")}</p>
                      <p className="mt-0.5 text-sm text-rose-800">“{log.rejection_reason}”</p>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </RequireEmployer>
  );
}
