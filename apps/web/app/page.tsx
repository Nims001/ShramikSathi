"use client";

// Onboarding: logo fade-in, purpose line, language choice, then the
// login / signup / Nagarik (placeholder) entry points.

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/lib/auth";
import { useLanguage, type Lang } from "@/lib/i18n/LanguageContext";
import { nagarikSso } from "@/lib/api";
import Logo from "@/components/Logo";

export default function OnboardingPage() {
  const { lang, setLang, t } = useLanguage();
  const { user } = useAuth();
  const router = useRouter();
  const [nagarikNote, setNagarikNote] = useState<string | null>(null);

  useEffect(() => {
    if (user) router.replace(user.role === "employer" ? "/employer" : "/home");
  }, [user, router]);

  // Placeholder: hits the stub endpoint, which always says "coming soon".
  const tryNagarik = async () => {
    try {
      await nagarikSso();
    } catch (e) {
      setNagarikNote(e instanceof Error ? e.message : t("onboard.nagarikSoon"));
    }
  };

  const languages: { value: Lang; label: string }[] = [
    { value: "en", label: "English" },
    { value: "ne", label: "नेपाली" },
  ];

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-[#F8FAFC] px-6">
      <div className="animate-fade-up flex w-full max-w-sm flex-col items-center text-center">
        <div className="icon-chip h-20 w-20 rounded-2xl bg-brand-50">
          <Logo className="h-full w-full" />
        </div>
        <h1 className="mt-6 text-3xl font-bold text-slate-900">{t("appName")}</h1>
        <p
          className="animate-fade-up mt-3 text-lg font-medium text-slate-700"
          style={{ animationDelay: "0.15s" }}
        >
          {t("onboard.empower")}
        </p>
        <p
          className="animate-fade-up mt-2 text-sm leading-relaxed text-slate-500"
          style={{ animationDelay: "0.3s" }}
        >
          {t("onboard.purpose")}
        </p>

        <div
          className="animate-fade-up mt-10 w-full"
          style={{ animationDelay: "0.45s" }}
        >
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            {t("onboard.chooseLang")}
          </p>
          <div className="grid grid-cols-2 gap-2">
            {languages.map((l) => (
              <button
                key={l.value}
                onClick={() => setLang(l.value)}
                aria-pressed={lang === l.value}
                className={`rounded-xl border px-4 py-3 text-base font-medium transition-colors ${
                  lang === l.value
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-slate-200 bg-white text-slate-700 active:bg-slate-50"
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>
        </div>

        <div
          className="animate-fade-up mt-8 flex w-full flex-col gap-3"
          style={{ animationDelay: "0.6s" }}
        >
          <Link href="/login" className="btn-primary w-full">
            {t("onboard.login")}
          </Link>
          <Link href="/signup" className="btn-secondary w-full">
            {t("onboard.signup")}
          </Link>
          <button
            type="button"
            onClick={tryNagarik}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-base font-medium text-slate-700 active:bg-slate-100"
          >
            {t("onboard.nagarik")} · {t("onboard.nagarikSoon")}
          </button>
          {nagarikNote ? (
            <p className="rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600">{nagarikNote}</p>
          ) : null}
        </div>

        <p
          className="animate-fade-up mt-8 text-xs leading-relaxed text-slate-400"
          style={{ animationDelay: "0.75s" }}
        >
          {t("onboard.disclaimer")}
        </p>
      </div>
    </div>
  );
}
