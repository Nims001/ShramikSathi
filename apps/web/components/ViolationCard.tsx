"use client";

// One rule-engine finding rendered in the current language.

import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { Violation } from "@/lib/types";

const styles: Record<Violation["severity"], string> = {
  info: "border-sky-200 bg-sky-50",
  warning: "border-amber-200 bg-amber-50",
  critical: "border-red-200 bg-red-50",
};

const dots: Record<Violation["severity"], string> = {
  info: "bg-sky-500",
  warning: "bg-amber-500",
  critical: "bg-red-500",
};

export default function ViolationCard({ violation }: { violation: Violation }) {
  const { lang } = useLanguage();

  const explanation =
    lang === "ne" && violation.plain_explanation_ne
      ? violation.plain_explanation_ne
      : violation.plain_explanation_en;
  const action =
    lang === "ne" && violation.suggested_action_ne
      ? violation.suggested_action_ne
      : violation.suggested_action_en;

  return (
    <div className={`rounded-card border p-4 shadow-soft ${styles[violation.severity]}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${dots[violation.severity]}`} />
          <span className="text-sm font-semibold capitalize text-slate-800">
            {violation.rule_id.replace(/\./g, " · ")}
          </span>
        </span>
        <span className="rounded bg-white/80 px-2 py-0.5 text-xs font-medium text-slate-600">
          {violation.section_reference}
        </span>
      </div>
      <p className="mt-3 text-sm text-slate-700">{explanation}</p>
      <p className="mt-2 text-sm font-medium text-brand-800">→ {action}</p>
    </div>
  );
}
