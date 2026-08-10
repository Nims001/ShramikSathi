"use client";

// Rights check: deterministic violations from the user's logs, plus the
// optional "Analyse with AI" step (RAG over The Labour Act, 2017).

import { useEffect, useMemo, useState } from "react";

import RequireAuth from "@/components/RequireAuth";
import ViolationCard from "@/components/ViolationCard";
import AiAnalysisPanel from "@/components/AiAnalysisPanel";
import NegotiationScriptPanel from "@/components/NegotiationScriptPanel";
import { getAnalysis, listEmployers } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { AnalysisDocument, Employer } from "@/lib/types";

export default function AnalysisPage() {
  const { t } = useLanguage();
  const [employers, setEmployers] = useState<Employer[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisDocument | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([listEmployers(), getAnalysis()])
      .then(([emps, doc]) => {
        if (!active) return;
        setEmployers(emps);
        setAnalysis(doc);
      })
      .catch(() => {
        if (!active) return;
        setEmployers([]);
        setAnalysis(null);
      });
    return () => {
      active = false;
    };
  }, []);

  const findings = useMemo(
    () => analysis?.employers.flatMap((e) => e.deterministic_findings) ?? [],
    [analysis],
  );

  return (
    <RequireAuth>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("dash.violations")}</h1>
          <p className="mt-1 text-sm text-slate-500">{t("dash.violationsDesc")}</p>
        </div>

        {/* Violations from logs */}
        <section>
          {findings.length === 0 ? (
            <div className="rounded-card border border-brand-200 bg-brand-50 p-5 text-center">
              <p className="text-sm font-medium text-brand-800">{t("dash.noViolations")}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {findings.map((f, i) => (
                <ViolationCard key={`${f.rule_id}-${i}`} violation={f} />
              ))}
            </div>
          )}
        </section>

        {/* AI analysis (RAG over The Labour Act, 2017) */}
        <AiAnalysisPanel hasEmployers={employers.length > 0} />

        {/* Negotiation script (AI-generated suggestion) */}
        <NegotiationScriptPanel hasEmployers={employers.length > 0} />
      </div>
    </RequireAuth>
  );
}
