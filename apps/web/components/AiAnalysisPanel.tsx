"use client";

// The "Analyse with AI" panel. Calls POST /api/analysis/ai (RAG over The
// Labour Act, 2017) and renders the new AI-generated findings grouped by
// employer, with the cited Labour Act sections called out. Everything here is
// supplementary to the deterministic findings and is labelled AI-generated.

import { useState } from "react";

import { analyseWithAI } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { AiAnalysisResult, Severity } from "@/lib/types";

const cardStyles: Record<Severity, string> = {
  info: "border-sky-200 bg-sky-50",
  warning: "border-amber-200 bg-amber-50",
  critical: "border-red-200 bg-red-50",
};

const badgeStyles: Record<Severity, string> = {
  info: "bg-sky-500",
  warning: "bg-amber-500",
  critical: "bg-red-500",
};

const sectionStyles: Record<Severity, string> = {
  info: "bg-sky-100 text-sky-900",
  warning: "bg-amber-100 text-amber-900",
  critical: "bg-red-100 text-red-900",
};

type State = "idle" | "loading" | "done" | "error";

export default function AiAnalysisPanel({ hasEmployers }: { hasEmployers: boolean }) {
  const { t, lang } = useLanguage();
  const [state, setState] = useState<State>("idle");
  const [result, setResult] = useState<AiAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const totalFindings = result?.ai_findings.reduce((n, g) => n + g.findings.length, 0) ?? 0;

  async function run() {
    if (state === "loading") return;
    setState("loading");
    setError(null);
    try {
      const res = await analyseWithAI();
      setResult(res);
      setState("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }

  const explanation = (f: { plain_explanation_en: string; plain_explanation_ne?: string | null }) =>
    lang === "ne" && f.plain_explanation_ne ? f.plain_explanation_ne : f.plain_explanation_en;
  const action = (f: { suggested_action_en: string; suggested_action_ne?: string | null }) =>
    lang === "ne" && f.suggested_action_ne ? f.suggested_action_ne : f.suggested_action_en;

  return (
    <section className="card">
      <div className="border-b border-slate-200 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">{t("ai.title")}</h2>
            <p className="mt-0.5 text-xs text-slate-500">{t("ai.subtitle")}</p>
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
              {state === "loading" ? t("ai.running") : t("ai.run")}
            </button>

            {state === "loading" ? (
              <div className="mt-4 flex items-center justify-center gap-2 py-4 text-sm text-slate-500">
                <span className="h-5 w-5 animate-spin rounded-full bg-[conic-gradient(from_0deg,#8b5cf6,#c4b5fd,#8b5cf6)]" />
                {t("ai.runningDesc")}
              </div>
            ) : null}

            {state === "error" ? (
              <div className="mt-4 rounded-card border border-red-200 bg-red-50 p-4">
                <p className="text-sm font-medium text-red-800">{t("ai.error")}</p>
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

                {totalFindings === 0 ? (
                  <div className="rounded-card border border-brand-200 bg-brand-50 p-5 text-center">
                    <p className="text-sm font-medium text-brand-800">{t("ai.none")}</p>
                    <p className="mt-1 text-xs text-brand-700">{t("ai.noneDesc")}</p>
                  </div>
                ) : (
                  result.ai_findings
                    .filter((g) => g.findings.length > 0)
                    .map((group) => (
                      <div key={group.employer_id}>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                          {t("ai.forEmployer")}: {group.employer_name}
                        </p>
                        <div className="space-y-2">
                          {group.findings.map((f, i) => (
                            <div
                              key={`${group.employer_id}-${f.rule_id}-${i}`}
                              className={`rounded-card border p-3.5 ${cardStyles[f.severity]}`}
                            >
                              <div className="flex items-center justify-between gap-2">
                                <span className="flex items-center gap-2">
                                  <span
                                    className={`h-2.5 w-2.5 rounded-full ${badgeStyles[f.severity]}`}
                                  />
                                  <span className="text-xs font-semibold capitalize text-slate-800">
                                    {f.rule_id.replace(/^ai_generated\./, "").replace(/\./g, " · ")}
                                  </span>
                                </span>
                                <span
                                  className={`rounded px-2 py-0.5 text-xs font-bold ${sectionStyles[f.severity]}`}
                                >
                                  {f.section_reference}
                                </span>
                              </div>
                              <p className="mt-2.5 text-sm text-slate-700">{explanation(f)}</p>
                              <p className="mt-2 text-sm font-medium text-brand-800">
                                → {action(f)}
                              </p>
                            </div>
                          ))}
                        </div>
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
