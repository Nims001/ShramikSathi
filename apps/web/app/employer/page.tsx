"use client";

// Employer portal: enter a worker's share code to link them, then browse
// their work logs. Only employer-role accounts can access this page.
//
// The "Awaiting your approval" inbox lists every signed record across all
// linked workers, oldest first, with inline approve/reject.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import BreakTimes, { WorkRange } from "@/components/BreakTimes";
import RequireEmployer from "@/components/RequireEmployer";
import {
  approveLog,
  linkEmployee,
  listLinkedEmployees,
  listPendingLogs,
  rejectLog,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { LinkedEmployee, PendingLog } from "@/lib/types";

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

function workedMinutes(log: PendingLog): number {
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

export default function EmployerPortalPage() {
  const { t } = useLanguage();
  const { logout } = useAuth();
  const router = useRouter();

  const [employees, setEmployees] = useState<LinkedEmployee[]>([]);
  const [pending, setPending] = useState<PendingLog[]>([]);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [pendingLoaded, setPendingLoaded] = useState(false);

  const [rejectFor, setRejectFor] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [agreed, setAgreed] = useState<Set<string>>(new Set());

  const loadPending = useCallback(() => {
    listPendingLogs()
      .then(setPending)
      .catch(() => setPending([]))
      .finally(() => setPendingLoaded(true));
  }, []);

  const load = useCallback(() => {
    listLinkedEmployees()
      .then(setEmployees)
      .catch(() => setEmployees([]))
      .finally(() => setLoaded(true));
  }, []);

  useEffect(() => {
    load();
    loadPending();
  }, [load, loadPending]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setBusy(true);
    try {
      const emp = await linkEmployee(code);
      setSuccess(`${t("employer.linked")} (${emp.username})`);
      setCode("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("employer.invalidCode"));
    } finally {
      setBusy(false);
    }
  };

  const removePending = (logId: string) =>
    setPending((list) => list.filter((l) => l.log_id !== logId));

  const toggleAgree = (logId: string) =>
    setAgreed((s) => {
      const next = new Set(s);
      if (next.has(logId)) next.delete(logId);
      else next.add(logId);
      return next;
    });

  const handleApprove = async (log: PendingLog) => {
    setBusyId(log.log_id);
    setError(null);
    setSuccess(null);
    try {
      await approveLog(log.employee_id, log.log_id);
      removePending(log.log_id);
      setSuccess(t("employer.approveSuccess"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusyId(null);
    }
  };

  const handleReject = async (log: PendingLog) => {
    if (!rejectReason.trim()) {
      setSuccess(null);
      setError(t("employer.rejectRequired"));
      return;
    }
    setBusyId(log.log_id);
    setError(null);
    setSuccess(null);
    try {
      await rejectLog(log.employee_id, log.log_id, rejectReason.trim());
      removePending(log.log_id);
      setRejectFor(null);
      setRejectReason("");
      setSuccess(t("employer.rejectSuccess"));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusyId(null);
    }
  };

  const doLogout = async () => {
    await logout();
    router.replace("/");
  };

  return (
    <RequireEmployer>
      <div className="mx-auto flex min-h-dvh w-full max-w-md flex-col bg-[#F8FAFC] shadow-soft-lg sm:border-x sm:border-slate-200">
        <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="flex items-center justify-between px-4 py-3">
            <div>
              <h1 className="text-lg font-bold text-slate-900">{t("employer.title")}</h1>
              <p className="text-xs text-slate-500">{t("employer.subtitle")}</p>
            </div>
            <button
              type="button"
              onClick={doLogout}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600"
            >
              {t("employer.logout")}
            </button>
          </div>
        </header>

        <main className="flex-1 space-y-6 px-4 py-6">
          {error ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          ) : null}
          {success ? (
            <p className="rounded-lg bg-brand-100 px-3 py-2 text-sm text-brand-800">{success}</p>
          ) : null}

          {/* Pending approvals inbox */}
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-semibold text-slate-800">{t("employer.pendingTitle")}</h2>
              {pending.length > 0 ? (
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                  {pending.length}
                </span>
              ) : null}
            </div>
            {!pendingLoaded ? (
              <div className="flex h-24 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              </div>
            ) : pending.length === 0 ? (
              <div className="card p-5 text-center">
                <p className="text-sm text-slate-600">{t("employer.noPending")}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pending.map((log) => (
                  <div key={log.log_id} className="card p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-slate-900">
                          {log.username}
                          <span className="ml-2 font-normal text-slate-400">· {log.log_date}</span>
                        </p>
                        <p className="mt-0.5 truncate text-xs text-slate-500">
                          {log.workplace_name ?? "—"}
                          {log.workplace_district ? ` · ${log.workplace_district}` : ""}
                        </p>
                      </div>
                      <Link
                        href={`/employer/employee/${log.employee_id}`}
                        className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600"
                      >
                        {t("employer.viewLogs")}
                      </Link>
                    </div>

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
                          <span className="font-medium tabular-nums">
                            रू {(log.promised_amount ?? 0).toLocaleString("en-IN")}
                          </span>
                        </div>
                      ) : null}
                      {log.paid_amount != null ? (
                        <div className="flex items-center justify-between">
                          <span className="text-slate-500">{t("home.paid")}</span>
                          <span className="font-medium tabular-nums">
                            रू {(log.paid_amount ?? 0).toLocaleString("en-IN")}
                          </span>
                        </div>
                      ) : null}
                    </div>

                    {rejectFor === log.log_id ? (
                      <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
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
                      <div className="mt-3 space-y-3 border-t border-slate-100 pt-3">
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
                ))}
              </div>
            )}
          </section>

          {/* Add worker by code */}
          <section className="card p-4">
            <h2 className="mb-3 font-semibold text-slate-800">{t("employer.addTitle")}</h2>
            <form onSubmit={submit} className="space-y-3">
              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-slate-700">
                  {t("employer.code")}
                </span>
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder={t("employer.codePlaceholder")}
                  autoComplete="off"
                  spellCheck={false}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-mono text-sm uppercase tracking-wider text-slate-900 placeholder:normal-case placeholder:tracking-normal placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
                <span className="mt-1 block text-xs text-slate-400">{t("employer.codeHint")}</span>
              </label>

              <button type="submit" disabled={busy || code.trim().length < 8} className="btn-primary w-full">
                {busy ? t("employer.adding") : t("employer.addBtn")}
              </button>
            </form>
          </section>

          {/* Linked workers */}
          <section>
            <h2 className="mb-3 font-semibold text-slate-800">{t("employer.workers")}</h2>
            {!loaded ? (
              <div className="flex h-24 items-center justify-center">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              </div>
            ) : employees.length === 0 ? (
              <div className="card p-5 text-center">
                <p className="text-sm text-slate-600">{t("employer.noEmployees")}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {employees.map((emp) => (
                  <div key={emp.employee_id} className="card p-4">
                    <div className="flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <p className="truncate font-semibold text-slate-900">{emp.username}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {t("employer.logCount", { count: emp.log_count })}
                        </p>
                      </div>
                      <Link
                        href={`/employer/employee/${emp.employee_id}`}
                        className="shrink-0 rounded-lg bg-brand-600 px-3 py-2 text-xs font-semibold text-white"
                      >
                        {t("employer.viewLogs")}
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <p className="text-center text-[11px] text-slate-400">
            {t("ai.disclaimer")}
          </p>
        </main>
      </div>
    </RequireEmployer>
  );
}
