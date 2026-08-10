"use client";

import { useLanguage } from "@/lib/i18n/LanguageContext";

export type BreakItem = { start?: string | null; end?: string | null };

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export function breakTimeOf(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (!Number.isNaN(d.getTime())) return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  return iso.slice(0, 5) || "—";
}

export function breakMinutes(breaks: BreakItem[]): number {
  return (breaks ?? []).reduce((sum, b) => {
    if (!b.start || !b.end) return sum;
    return (
      sum +
      Math.max(0, (new Date(b.end).getTime() - new Date(b.start).getTime()) / 60000)
    );
  }, 0);
}

function fmtDuration(totalMinutes: number): string {
  const m = Math.max(0, Math.round(totalMinutes));
  const h = Math.floor(m / 60);
  const mm = m % 60;
  if (h === 0) return `${mm}m`;
  if (mm === 0) return `${h}h`;
  return `${h}h ${mm}m`;
}

export function WorkRange({ start, end }: { start?: string | null; end?: string | null }) {
  if (!start || !end) return null;
  return (
    <p className="tabular-nums text-xs text-slate-600">
      {breakTimeOf(start)} → {breakTimeOf(end)}
    </p>
  );
}

export default function BreakTimes({ breaks }: { breaks: BreakItem[] }) {
  const { t } = useLanguage();
  if (!breaks || breaks.length === 0) return null;
  const total = breakMinutes(breaks);
  return (
    <div className="space-y-0.5">
      {breaks.map((b, i) => {
        const dur = breakMinutes([b]);
        return (
          <p key={i} className="tabular-nums text-xs text-slate-600">
            {breakTimeOf(b.start)} → {breakTimeOf(b.end)}
            {dur > 0 ? <span className="text-slate-400"> · {fmtDuration(dur)}</span> : null}
          </p>
        );
      })}
      {total > 0 ? (
        <p className="text-xs font-medium text-slate-700">
          {t("logs.totalBreak")}: {fmtDuration(total)}
        </p>
      ) : null}
    </div>
  );
}
