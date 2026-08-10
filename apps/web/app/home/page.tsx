"use client";

// Personal dashboard: daily / weekly / monthly views of the user's work logs,
// with summary stats and charts. The series is aggregated server-side
// (GET /api/worklogs/summary) so the page stays fast even with many logs.

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import RequireAuth from "@/components/RequireAuth";
import { getWorklogSummary, listEmployers } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { optionLabel } from "@/components/controls";
import { EMPLOYMENT_TYPES } from "@/lib/constants";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type {
  Employer,
  WorkLogPeriod,
  WorkLogSummary,
} from "@/lib/types";

const PIE_COLORS = ["#1F75E6", "#5B9DF2", "#9DC4F7", "#3D8BE0", "#1B66C9", "#86BAA8", "#7A8BA6"];

function money(n: number | undefined): string {
  return (n ?? 0).toLocaleString("en-IN");
}

export default function HomePage() {
  const { user } = useAuth();
  const { t, lang } = useLanguage();

  const [employers, setEmployers] = useState<Employer[]>([]);
  const [summary, setSummary] = useState<WorkLogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<WorkLogPeriod>("daily");

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([listEmployers(), getWorklogSummary(period)])
      .then(([emps, s]) => {
        if (!active) return;
        setEmployers(emps);
        setSummary(s);
      })
      .catch(() => {
        if (!active) return;
        setEmployers([]);
        setSummary(null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [period]);

  const rows = useMemo(() => summary?.rows ?? [], [summary]);
  const byEmployer = useMemo(() => summary?.by_employer ?? [], [summary]);
  const hasLogs = (summary?.total_logs ?? 0) > 0;

  const totals = useMemo(() => {
    let days = 0;
    let hours = 0;
    let overtime = 0;
    let promised = 0;
    let paid = 0;
    for (const r of rows) {
      days += r.days;
      hours += r.hours;
      overtime += r.overtime;
      promised += r.promised;
      paid += r.paid;
    }
    return { days, hours, overtime, promised, paid, due: promised - paid };
  }, [rows]);

  const rowsWithData = rows.filter((r) => r.days > 0);

  const periodLabel =
    period === "daily" ? t("dash.today") : period === "weekly" ? t("dash.thisWeek") : t("dash.thisMonth");

  const initials = (user?.username ?? "?")[0]?.toUpperCase() ?? "?";

  const tooltipFormatter = (value: number | string, name: string) => {
    const v = Number(value);
    if (name === t("home.promised") || name === t("home.paid") || name === t("home.due")) {
      return [`रू ${money(v)}`, name];
    }
    return [`${v.toFixed(1)}h`, name];
  };

  if (loading && !summary) {
    return (
      <div className="flex h-40 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <RequireAuth>
      <div className="space-y-6">
        {/* Title + profile button */}
        <div className="flex items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{t("dash.title")}</h1>
            <p className="mt-1 text-sm text-slate-500">{t("dash.subtitle")}</p>
          </div>
          <Link
            href="/profile"
            aria-label={t("profile.title")}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-brand-200 bg-brand-50 text-base font-bold text-brand-800"
          >
            {initials}
          </Link>
        </div>

        {!hasLogs ? (
          <div className="card p-6 text-center">
            <p className="text-sm text-slate-600">{t("dash.noLogs")}</p>
            <Link
              href="/log-today"
              className="btn-primary mt-4 inline-block px-5 py-3"
            >
              {t("dash.addFirstLog")}
            </Link>
          </div>
        ) : (
          <>
            {/* Voice-guided rights check */}
            <Link
              href="/voice"
              className="flex items-center justify-between rounded-card border border-violet-200 bg-violet-50 p-4"
            >
              <div>
                <p className="text-sm font-semibold text-violet-900">{t("home.voiceTitle")}</p>
                <p className="mt-0.5 text-xs text-violet-700">{t("home.voiceDesc")}</p>
              </div>
              <span className="text-2xl">🎙️</span>
            </Link>

            {/* Period selector */}
            <div>
              <p className="mb-1.5 text-sm font-medium text-slate-700">{t("dash.viewBy")}</p>
              <div className="grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1">
                {(["daily", "weekly", "monthly"] as WorkLogPeriod[]).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPeriod(p)}
                    aria-pressed={period === p}
                    className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                      period === p
                        ? "bg-white text-brand-800 shadow-sm"
                        : "text-slate-500 active:bg-slate-200"
                    }`}
                  >
                    {p === "daily" ? t("dash.daily") : p === "weekly" ? t("dash.weekly") : t("dash.monthly")}
                  </button>
                ))}
              </div>
            </div>

            {/* Summary cards */}
            <div>
              <h2 className="mb-2 text-sm font-semibold text-slate-800">{periodLabel}</h2>
              <div className="grid grid-cols-3 gap-2">
                <SummaryCard label={t("dash.days")} value={String(totals.days)} />
                <SummaryCard label={t("dash.hours")} value={`${totals.hours.toFixed(1)}h`} />
                <SummaryCard label={t("dash.overtime")} value={`${totals.overtime.toFixed(1)}h`} />
                <SummaryCard label={t("home.promised")} value={`रू ${money(totals.promised)}`} />
                <SummaryCard label={t("home.paid")} value={`रू ${money(totals.paid)}`} />
                <SummaryCard label={t("home.due")} value={`रू ${money(totals.due)}`} />
              </div>
            </div>

            {/* Hours chart */}
            <section className="card p-4">
              <h2 className="mb-3 text-sm font-semibold text-slate-800">{t("dash.hours")}</h2>
              {rowsWithData.length === 0 ? (
                <p className="py-6 text-center text-sm text-slate-500">{t("dash.noLogs")}</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={rows} margin={{ top: 4, right: 4, left: -18, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
                    <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                    <Tooltip formatter={tooltipFormatter} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="hours" name={t("dash.hours")} fill="#1F75E6" radius={[4, 4, 0, 0]} maxBarSize={26} />
                    <Bar dataKey="overtime" name={t("dash.overtime")} fill="#87B1EC" radius={[4, 4, 0, 0]} maxBarSize={26} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </section>

            {/* Pay chart */}
            <section className="card p-4">
              <h2 className="mb-3 text-sm font-semibold text-slate-800">{t("dash.pay")}</h2>
              {rowsWithData.length === 0 ? (
                <p className="py-6 text-center text-sm text-slate-500">{t("dash.noLogs")}</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={rows} margin={{ top: 4, right: 4, left: -6, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} />
                    <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                    <Tooltip formatter={tooltipFormatter} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="promised" name={t("home.promised")} fill="#94A3B8" radius={[4, 4, 0, 0]} maxBarSize={26} />
                    <Bar dataKey="paid" name={t("home.paid")} fill="#1F75E6" radius={[4, 4, 0, 0]} maxBarSize={26} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </section>

            {/* Hours by employer */}
            {byEmployer.length > 0 ? (
              <section className="card p-4">
                <h2 className="mb-3 text-sm font-semibold text-slate-800">{t("dash.byEmployer")}</h2>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={byEmployer}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      stroke="#fff"
                    >
                      {byEmployer.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              </section>
            ) : null}

            {/* Details */}
            <section className="card">
              <h2 className="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-800">
                {t("dash.details")}
              </h2>
              {rowsWithData.length === 0 ? (
                <p className="px-4 py-6 text-center text-sm text-slate-500">{t("dash.noLogs")}</p>
              ) : (
                <div className="divide-y divide-slate-100">
                  <div className="flex items-center justify-between bg-slate-50 px-4 py-2 text-xs font-medium text-slate-500">
                    <span>{t("dash.period")}</span>
                    <div className="flex items-center gap-3">
                      <span className="w-8 text-right">{t("dash.days")}</span>
                      <span className="w-12 text-right">{t("dash.hours")}</span>
                      <span className="w-12 text-right">{t("dash.overtime")}</span>
                      <span className="w-16 text-right">{t("home.paid")}</span>
                    </div>
                  </div>
                  {rowsWithData.map((r) => (
                    <div
                      key={r.key}
                      className="flex items-center justify-between px-4 py-2.5 text-sm text-slate-700"
                    >
                      <span className="font-medium text-slate-900">{r.label}</span>
                      <div className="flex items-center gap-3 tabular-nums">
                        <span className="w-8 text-right text-slate-600">{r.days}</span>
                        <span className="w-12 text-right">{r.hours.toFixed(1)}</span>
                        <span className="w-12 text-right">{r.overtime.toFixed(1)}</span>
                        <span className="w-16 text-right">रू {money(r.paid)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

          </>
        )}

        {/* Employers */}
        <section>
          <h2 className="mb-3 font-semibold text-slate-800">{t("home.employers")}</h2>
          {employers.length === 0 ? (
            <div className="card p-5 text-center">
              <p className="text-sm text-slate-600">{t("home.noEmployers")}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {employers.map((e) => {
                const type = optionLabel(e.employment_type ?? "", EMPLOYMENT_TYPES, lang);
                return (
                  <div key={e.id} className="card p-4">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-slate-900">{e.employer_name ?? "—"}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {[e.work_district, type].filter(Boolean).join(" · ")}
                        </p>
                        {e.actual_hours_per_day ? (
                          <p className="mt-1 text-xs text-slate-600">
                            {e.actual_hours_per_day}h/day ·{" "}
                            {e.actual_days_per_week ?? e.contract_days_per_week ?? "—"} /wk
                          </p>
                        ) : null}
                      </div>
                      <div className="flex shrink-0 gap-2">
                        <Link
                          href={`/add-employer/${e.id}`}
                          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-700"
                        >
                          {t("home.edit")}
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          <Link
            href="/add-employer"
            className="btn-secondary mt-3 block w-full text-center"
          >
            {t("home.addEmployer")}
          </Link>
        </section>

        {/* Bottom action */}
        <Link
          href="/log-today"
          className="btn-primary block w-full text-center text-sm"
        >
          {t("home.logToday")}
        </Link>
      </div>
    </RequireAuth>
  );
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="card px-3 py-2.5">
      <p className="text-[11px] font-medium text-slate-500">{label}</p>
      <p className="mt-0.5 truncate text-sm font-bold text-slate-900">{value}</p>
    </div>
  );
}
