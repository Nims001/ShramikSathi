"use client";

// Daily logs: every work log you recorded, grouped by employer and ordered by
// timestamp, split into "this week" and "earlier". Read-only list — logs are
// added from the logging form.

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import BreakTimes, { WorkRange } from "@/components/BreakTimes";
import RequireAuth from "@/components/RequireAuth";
import { listEmployers, listWorklogs } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { Employer, WorkLog } from "@/lib/types";

function weekStart(d: Date): Date {
  const copy = new Date(d);
  copy.setHours(0, 0, 0, 0);
  const day = (copy.getDay() + 6) % 7; // Monday = 0
  copy.setDate(copy.getDate() - day);
  return copy;
}

function fmtDuration(totalMinutes: number): string {
  const m = Math.max(0, Math.round(totalMinutes));
  const h = Math.floor(m / 60);
  const mm = m % 60;
  if (h === 0) return `${mm}m`;
  if (mm === 0) return `${h}h`;
  return `${h}h ${mm}m`;
}

function workedMinutes(log: WorkLog): number {
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

function StatusBadge({ log, t }: { log: WorkLog; t: (k: string) => string }) {
  const status = log.approval_status ?? "draft";
  if (status === "approved") {
    return (
      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
        ✓ {t("logs.approved")}
      </span>
    );
  }
  if (status === "rejected") {
    return (
      <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
        ✕ {t("logs.rejected")}
      </span>
    );
  }
  if (status === "pending_employer") {
    return (
      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
        ⏳ {t("logs.pending")}
      </span>
    );
  }
  return null;
}

export default function LogsPage() {
  const { t, lang } = useLanguage();
  const [employers, setEmployers] = useState<Employer[]>([]);
  const [logs, setLogs] = useState<WorkLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([listEmployers(), listWorklogs()])
      .then(([emps, work]) => {
        if (!active) return;
        setEmployers(emps);
        setLogs(work);
      })
      .catch(() => {
        if (!active) return;
        setEmployers([]);
        setLogs([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const grouped = useMemo(() => {
    const today = new Date();
    const ws = weekStart(today).getTime();
    const sorted = [...logs].sort(
      (a, b) =>
        (b.log_date > a.log_date ? 1 : b.log_date < a.log_date ? -1 : 0) ||
        (b.work_started_at ?? "") < (a.work_started_at ?? "")
          ? -1
          : 1,
    );
    const byEmployer = new Map<string, { thisWeek: WorkLog[]; earlier: WorkLog[] }>();
    for (const log of sorted) {
      const bucket = byEmployer.get(log.employer_id) ?? {
        thisWeek: [],
        earlier: [],
      };
      if (new Date(`${log.log_date}T00:00:00`).getTime() >= ws) bucket.thisWeek.push(log);
      else bucket.earlier.push(log);
      byEmployer.set(log.employer_id, bucket);
    }
    return byEmployer;
  }, [logs]);

  const nameOf = useMemo(
    () => new Map(employers.map((e) => [e.id, e.employer_name])),
    [employers],
  );

  const hasUnapproved =
    logs.some((l) => l.approval_status === "pending_employer" || l.approval_status === "rejected");

  const dateLabel = (iso: string) =>
    new Date(`${iso}T00:00:00`).toLocaleDateString(lang === "ne" ? "ne-NP" : "en-IN", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });

  return (
    <RequireAuth>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("logs.title")}</h1>
          <p className="mt-1 text-sm text-slate-500">{t("logs.subtitle")}</p>
        </div>

        {loading ? (
          <div className="flex h-40 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
          </div>
        ) : employers.length === 0 ? (
          <div className="card p-6 text-center">
            <p className="text-sm text-slate-600">{t("logs.noEmployers")}</p>
            <Link href="/add-employer" className="btn-primary mt-4 inline-block px-5 py-3">
              {t("logs.addEmployer")}
            </Link>
          </div>
        ) : logs.length === 0 ? (
          <div className="card p-6 text-center">
            <p className="text-sm text-slate-600">{t("logs.empty")}</p>
          </div>
        ) : (
          [...grouped.entries()].map(([employerId, { thisWeek, earlier }]) => {
            const sections: { label: string; logs: WorkLog[] }[] = [];
            if (thisWeek.length > 0) sections.push({ label: t("logs.thisWeek"), logs: thisWeek });
            if (earlier.length > 0) sections.push({ label: t("logs.earlier"), logs: earlier });
            return (
              <section key={employerId} className="card overflow-hidden">
                <h2 className="flex items-center gap-2 border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">
                  <span className="icon-chip h-8 w-8 rounded-lg text-xs">
                    {(nameOf.get(employerId) ?? "—")[0]?.toUpperCase() ?? "?"}
                  </span>
                  {nameOf.get(employerId) ?? "—"}
                </h2>
                <div className="divide-y divide-slate-100">
                  {sections.map((section) => (
                    <div key={section.label}>
                      <p className="bg-slate-50 px-4 py-1.5 text-xs font-medium text-slate-500">
                        {section.label}
                      </p>
                      {section.logs.map((log) => (
                        <div key={log.id} className="px-4 py-3">
                          <div className="flex items-center justify-between gap-2">
                            <p className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                              {dateLabel(log.log_date)}
                              <StatusBadge log={log} t={(k) => t(k)} />
                            </p>
                            <div className="text-right">
                              <p className="text-sm tabular-nums text-slate-700">
                                {t("logs.worked")} {fmtDuration(workedMinutes(log))}
                              </p>
                              <WorkRange start={log.work_started_at} end={log.work_ended_at} />
                            </div>
                          </div>
                          <div className="mt-1 flex flex-wrap items-start gap-x-4 gap-y-1 text-xs text-slate-500">
                            {(log.breaks ?? []).length > 0 ? (
                              <span>
                                <span className="font-medium text-slate-500">{t("logs.break")}</span>
                                <BreakTimes breaks={log.breaks ?? []} />
                              </span>
                            ) : null}
                            {log.overtime_minutes > 0 ? (
                              <span className="font-medium text-amber-700">
                                {t("logs.overtime")} {fmtDuration(log.overtime_minutes)}
                              </span>
                            ) : null}
                            {log.paid_amount != null ? (
                              <span>
                                {t("home.paid")} रू {log.paid_amount.toLocaleString("en-IN")}
                              </span>
                            ) : log.promised_amount != null ? (
                              <span className="font-medium text-rose-700">
                                {t("logs.notPaid")}
                              </span>
                            ) : null}
                            {log.promised_amount != null && log.paid_amount == null ? (
                              <span>
                                {t("home.promised")} रू {log.promised_amount.toLocaleString("en-IN")}
                              </span>
                            ) : null}
                            {log.deductions && log.deductions.length > 0 ? (
                              <span>{t("logs.deductions")}: {log.deductions.length}</span>
                            ) : null}
                          </div>
                          {log.rejection_reason ? (
                            <div className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2">
                              <p className="text-[11px] font-semibold text-rose-600">
                                {t("logs.rejection")}
                              </p>
                              <p className="mt-0.5 text-sm text-rose-800">“{log.rejection_reason}”</p>
                            </div>
                          ) : null}
                          {log.approval_status === "rejected" ? (
                            <Link
                              href={`/log-today?edit=${log.id}`}
                              className="mt-2 inline-block text-sm font-medium text-brand-700"
                            >
                              {t("logs.resubmit")} →
                            </Link>
                          ) : null}
                          {log.note ? (
                            <p className="mt-1.5 text-xs italic text-slate-500">{log.note}</p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </section>
            );
          })
        )}

        {hasUnapproved ? (
          <div className="card border-amber-200 p-5">
            <h3 className="text-base font-semibold text-slate-900">{t("logs.legalTitle")}</h3>
            <p className="mt-2 text-sm text-slate-600">{t("logs.legalBody")}</p>
            <Link
              href="/analysis"
              className="mt-3 inline-block text-sm font-medium text-brand-700"
            >
              {t("home.view")} →
            </Link>
          </div>
        ) : null}
      </div>
    </RequireAuth>
  );
}
