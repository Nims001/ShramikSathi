"use client";

// Compact app bar: app name on the left, language toggle on the right.
// Primary navigation lives in the bottom TabBar. While a work-log timer is
// running, a live chip shows the elapsed time and links back to the log so
// the timer visibly keeps running on every page.

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import Logo from "@/components/Logo";
import { useLanguage, type Lang } from "@/lib/i18n/LanguageContext";
import { loadLogDraft, type LogStatus } from "@/lib/logDraft";

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

// Same active-time formula as the log page: wall-clock now minus the start
// time, excluding only the currently open break.
function activeElapsed(startedAt: string, breakStart: string | null): string {
  const start = new Date(startedAt).getTime();
  let ms = Date.now() - start;
  if (breakStart) ms -= Date.now() - new Date(breakStart).getTime();
  if (ms < 0) ms = 0;
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  const s = Math.floor((ms % 60_000) / 1_000);
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

export function RunningTimerChip() {
  const pathname = usePathname();
  const { t } = useLanguage();
  const [running, setRunning] = useState<{ status: LogStatus; startedAt: string; breakStart: string | null } | null>(null);
  const [, setTick] = useState(0);

  useEffect(() => {
    if (pathname === "/log-today") {
      setRunning(null);
      return;
    }
    const read = () => {
      const draft = loadLogDraft();
      const next =
        draft && draft.status !== "idle" && draft.startedAt
          ? { status: draft.status, startedAt: draft.startedAt, breakStart: draft.breakStart }
          : null;
      if (next) {
        setRunning(next);
        setTick((n) => n + 1);
      } else {
        setRunning(null);
      }
    };
    read();
    const id = setInterval(read, 1_000);
    return () => clearInterval(id);
  }, [pathname]);

  if (!running) return null;

  const onBreak = running.status === "on_break";

  return (
    <Link
      href="/log-today"
      className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
        onBreak
          ? "border-amber-200 bg-amber-50 text-amber-800"
          : "border-emerald-200 bg-emerald-50 text-emerald-800"
      }`}
    >
      <span className={`h-1.5 w-1.5 animate-pulse rounded-full ${onBreak ? "bg-amber-500" : "bg-emerald-500"}`} />
      <span className="tabular-nums">{activeElapsed(running.startedAt, running.breakStart)}</span>
      <span>{onBreak ? t("timer.chipBreak") : t("timer.chipRunning")}</span>
    </Link>
  );
}

export function LanguageToggle() {
  const { lang, setLang } = useLanguage();

  const cycle = () => setLang(lang === "en" ? "ne" : "en");

  return (
    <button
      onClick={cycle}
      className="rounded-full border border-brand-100 bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-700 active:bg-brand-100"
      aria-label="Toggle language / भाषा बदल्नुहोस्"
    >
      {lang === "en" ? "नेपाली" : "English"}
    </button>
  );
}

export default function Header() {
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="flex items-center justify-between px-4 py-3">
        <Link href="/home" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50">
            <Logo className="h-full w-full" />
          </span>
          <span className="text-lg font-bold text-brand-700">{t("appName")}</span>
        </Link>
        <div className="flex items-center gap-2">
          <RunningTimerChip />
          <LanguageToggle />
        </div>
      </div>
    </header>
  );
}
