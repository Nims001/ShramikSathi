"use client";

// The "negotiation script" panel. Calls POST /api/analysis/negotiate (Gemini,
// using the retrieved Labour Act sections) and renders a short, polite script
// per employer that the worker could use to raise issues. Clearly labelled as
// an AI-generated suggestion, not legal advice.

import { useState } from "react";

import { generateNegotiationScript } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { NegotiationResult } from "@/lib/types";

type State = "idle" | "loading" | "done" | "error";

export default function NegotiationScriptPanel({ hasEmployers }: { hasEmployers: boolean }) {
  const { t, lang } = useLanguage();
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<NegotiationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (state === "loading") return;
    setState("loading");
    setError(null);
    try {
      const res = await generateNegotiationScript();
      setResult(res);
      setState("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  const text = (en: string, ne?: string | null) => (lang === "ne" && ne ? ne : en);

  return (
    <section className="card">
      <div className="border-b border-slate-200 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">{t("ai.negotiationTitle")}</h2>
            <p className="mt-0.5 text-xs text-slate-500">{t("ai.negotiationSubtitle")}</p>
          </div>
          <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-700">
            AI
          </span>
        </div>
      </div>

      <div className="p-4">
        {!hasEmployers ? (
          <p className="text-sm text-slate-500">{t("ai.noEmployers")}</p>
        ) : (
          <>
            <button
              type="button"
              onClick={run}
              disabled={state === "loading"}
              className="btn-primary w-full text-sm disabled:cursor-wait"
            >
              {state === "loading" ? t("ai.negotiationRunning") : t("ai.negotiationRun")}
            </button>

            {state === "loading" ? (
              <div className="mt-4 flex items-center justify-center gap-2 py-4 text-sm text-slate-500">
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
                {t("ai.negotiationRunningDesc")}
              </div>
            ) : null}

            {state === "error" ? (
              <div className="mt-4 rounded-card border border-red-200 bg-red-50 p-4">
                <p className="text-sm font-medium text-red-800">{t("ai.negotiationError")}</p>
                <p className="mt-1 text-xs text-red-700">{error}</p>
              </div>
            ) : null}

            {state === "done" && result ? (
              <div className="mt-4 space-y-4">
                {result.warning ? (
                  <p className="rounded-card border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                    {t("ai.warning")}: {result.warning}
                  </p>
                ) : null}

                {result.scripts.length === 0 ? (
                  <div className="rounded-card border border-brand-200 bg-brand-50 p-5 text-center">
                    <p className="text-sm font-medium text-brand-800">{t("ai.negotiationNone")}</p>
                  </div>
                ) : (
                  result.scripts.map((s) => (
                    <div key={s.employer_id} className="rounded-card border border-slate-200 p-4">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                        {t("ai.forEmployer")}: {s.employer_name}
                      </p>
                      <p className="text-sm italic text-slate-700">“{text(s.opening_en, s.opening_ne)}”</p>
                      <ul className="mt-3 space-y-2">
                        {(lang === "ne" && s.points_ne?.length ? s.points_ne : s.points_en).map(
                          (p, i) => (
                            <li key={i} className="flex gap-2 text-sm text-slate-700">
                              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                              {p}
                            </li>
                          ),
                        )}
                      </ul>
                      <p className="mt-3 text-sm italic text-slate-700">“{text(s.closing_en, s.closing_ne)}”</p>
                    </div>
                  ))
                )}

                <p className="pt-1 text-[11px] text-slate-400">{t("ai.disclaimer")}</p>
              </div>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}
