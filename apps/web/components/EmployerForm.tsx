"use client";

// Data-driven bilingual employer intake form. Sections render in order; some
// fields only appear when earlier answers make them relevant (conditional
// fields). All option text comes from lib/constants / i18n dictionaries.

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  CheckboxField,
  FieldLabel,
  InfoCard,
  SelectField,
  TextField,
  YesNoGroup,
} from "@/components/controls";
import { createEmployer, updateEmployer } from "@/lib/api";
import type { Employer } from "@/lib/types";
import {
  EMPLOYMENT_TYPES,
  HIRING_CHANNELS,
  OVERTIME_CONSENT,
  OVERTIME_RATES,
  OVERTIME_UNITS,
  PAYMENT_METHODS,
  PAY_FREQUENCIES,
  PAY_UNITS,
  PROVINCES,
  SKILL_LEVELS,
  WEEKDAYS,
  type BilingualOption,
} from "@/lib/constants";
import { useAuth } from "@/lib/auth";
import { useLanguage } from "@/lib/i18n/LanguageContext";

type FormData = Record<string, string>;

type FieldDef = {
  key: string;
  label: string;
  hint?: string;
  type: "text" | "number" | "date" | "time" | "select" | "yesno" | "chips" | "note" | "checkbox" | "textlist";
  options?: BilingualOption[];
  visible?: (d: FormData) => boolean;
  labelFor?: (d: FormData) => string;
  min?: number;
  max?: number;
  group?: string;
  groupLabel?: string;
};

type SectionDef = {
  id: string;
  title: string;
  desc: string;
  fields: FieldDef[];
};

const HINT_5H = "option.hoursGt5";

function buildSections(t: (k: string) => string): SectionDef[] {
  return [
    {
      id: "employment",
      title: t("sec.employment"),
      desc: t("sec.employment.desc"),
      fields: [
        { key: "employer_name", label: t("field.employer_name"), type: "text" },
        { key: "work_province", label: t("field.province"), type: "select", options: [] },
        { key: "work_district", label: t("field.district"), type: "select", options: [] },
        { key: "work_address", label: t("field.address"), type: "text" },
        { key: "skill_level", label: t("field.skill"), type: "select", options: SKILL_LEVELS },
        { key: "industry", label: t("field.industry"), type: "text" },
        { key: "employment_type", label: t("field.type"), type: "select", options: EMPLOYMENT_TYPES },
        { key: "job_title", label: t("field.title"), type: "text" },
        { key: "hiring_channel", label: t("field.hiring"), type: "select", options: HIRING_CHANNELS },
        {
          key: "contractor_name",
          label: t("field.contractor"),
          type: "text",
          visible: (d) => d.hiring_channel === "contractor",
        },
        {
          key: "tenure_years",
          label: t("field.tenure"),
          type: "number",
          group: "tenure",
          groupLabel: t("field.tenure.years"),
          min: 0,
        },
        {
          key: "tenure_months",
          label: t("field.tenure"),
          type: "number",
          group: "tenure",
          groupLabel: t("field.tenure.months"),
          min: 0,
          max: 12,
        },
        { key: "on_probation", label: t("field.probation"), type: "yesno" },
        {
          key: "probation_since",
          label: t("field.probation.since"),
          type: "date",
          visible: (d) => d.on_probation === "yes",
        },
      ],
    },
    {
      id: "contracted",
      title: t("sec.contracted"),
      desc: t("sec.contracted.desc"),
      fields: [
        { key: "contract_hours_per_day", label: t("field.contracted.hours"), type: "number", hint: HINT_5H, min: 0, max: 24 },
        {
          key: "contract_break_start",
          label: t("field.contracted.breakStart"),
          type: "time",
          visible: (d) => Number(d.contract_hours_per_day) > 5 && d.contract_break_unspecified !== "yes",
        },
        {
          key: "contract_break_end",
          label: t("field.contracted.breakEnd"),
          type: "time",
          visible: (d) => Number(d.contract_hours_per_day) > 5 && d.contract_break_unspecified !== "yes",
        },
        {
          key: "contract_break_unspecified",
          label: t("field.contracted.breakUnspecified"),
          type: "yesno",
          visible: (d) => Number(d.contract_hours_per_day) > 5,
        },
        { key: "contract_days_per_week", label: t("field.contracted.days"), type: "number", min: 0, max: 7 },
        {
          key: "contract_break_days",
          label: t("field.contracted.breakDays"),
          type: "chips",
          options: WEEKDAYS,
          visible: (d) =>
            Number(d.contract_days_per_week) > 0 && Number(d.contract_days_per_week) < 7 && d.contract_break_days_unspecified !== "yes",
        },
        {
          key: "contract_break_days_unspecified",
          label: t("field.contracted.breakDaysUnspecified"),
          type: "yesno",
          visible: (d) => Number(d.contract_days_per_week) > 0 && Number(d.contract_days_per_week) < 7,
        },
        { key: "contract_months_per_year", label: t("field.contracted.months"), type: "number", min: 0, max: 12 },
      ],
    },
    {
      id: "actual",
      title: t("sec.actual"),
      desc: t("sec.actual.desc"),
      fields: [
        { key: "actual_hours_per_day", label: t("field.actual.hours"), type: "number", hint: HINT_5H, min: 0, max: 24 },
        {
          key: "actual_break_start",
          label: t("field.actual.breakStart"),
          type: "time",
          visible: (d) => Number(d.actual_hours_per_day) > 5 && d.actual_break_unspecified !== "yes",
        },
        {
          key: "actual_break_end",
          label: t("field.actual.breakEnd"),
          type: "time",
          visible: (d) => Number(d.actual_hours_per_day) > 5 && d.actual_break_unspecified !== "yes",
        },
        {
          key: "actual_break_unspecified",
          label: t("field.actual.breakUnspecified"),
          type: "yesno",
          visible: (d) => Number(d.actual_hours_per_day) > 5,
        },
        { key: "actual_days_per_week", label: t("field.actual.days"), type: "number", min: 0, max: 7 },
        {
          key: "actual_break_days",
          label: t("field.actual.breakDays"),
          type: "chips",
          options: WEEKDAYS,
          visible: (d) =>
            Number(d.actual_days_per_week) > 0 && Number(d.actual_days_per_week) < 7 && d.actual_break_days_unspecified !== "yes",
        },
        {
          key: "actual_break_days_unspecified",
          label: t("field.actual.breakDaysUnspecified"),
          type: "yesno",
          visible: (d) => Number(d.actual_days_per_week) > 0 && Number(d.actual_days_per_week) < 7,
        },
        { key: "actual_months_per_year", label: t("field.actual.months"), type: "number", min: 0, max: 12 },
      ],
    },
    {
      id: "overtime",
      title: t("sec.overtime"),
      desc: t("sec.overtime.desc"),
      fields: [
        { key: "overtime_rule", label: t("field.overtime.rule"), type: "yesno" },
        {
          key: "overtime_hours_per_unit",
          label: t("field.overtime.hours"),
          type: "number",
          min: 0,
          visible: (d) => d.overtime_rule === "yes",
        },
        {
          key: "overtime_unit",
          label: t("field.overtime.hours"),
          type: "select",
          options: OVERTIME_UNITS,
          visible: (d) => d.overtime_rule === "yes",
        },
        {
          key: "overtime_rate",
          label: t("field.overtime.rate"),
          type: "select",
          options: OVERTIME_RATES,
          visible: (d) => d.overtime_rule === "yes",
        },
        {
          key: "overtime_rate_other",
          label: t("field.overtime.rateOther"),
          type: "number",
          min: 0,
          visible: (d) => d.overtime_rule === "yes" && d.overtime_rate === "other",
        },
        {
          key: "overtime_consent",
          label: t("field.overtime.consent"),
          type: "select",
          options: OVERTIME_CONSENT,
          visible: (d) => d.overtime_rule === "yes",
        },
        { key: "night_work", label: t("field.night"), type: "yesno" },
        {
          key: "night_allowance",
          label: t("field.night.allowance"),
          type: "yesno",
          visible: (d) => d.night_work === "yes",
        },
      ],
    },
    {
      id: "pay",
      title: t("sec.pay"),
      desc: t("sec.pay.desc"),
      fields: [
        { key: "pay_unit", label: t("field.pay.unit"), type: "select", options: PAY_UNITS },
        {
          key: "promised_wage",
          label: t("field.pay.promised"),
          labelFor: (d) => {
            const perUnitKey = {
              hourly: "field.pay.promisedPerHour",
              daily: "field.pay.promisedPerDay",
              weekly: "field.pay.promisedPerWeek",
              monthly: "field.pay.promisedPerMonth",
              per_piece: "field.pay.promisedPerPiece",
            }[d.pay_unit ?? ""];
            return perUnitKey ? t(perUnitKey) : t("field.pay.promised");
          },
          type: "number",
          min: 0,
        },
        { key: "payment_frequency", label: t("field.pay.when"), type: "select", options: PAY_FREQUENCIES },
        { key: "payment_method", label: t("field.pay.method"), type: "select", options: PAYMENT_METHODS },
        { key: "received_annual_increment", label: t("field.pay.increment"), type: "yesno" },
        { key: "festival_expense_paid", label: t("field.pay.festival"), type: "yesno" },
        { key: "other_deduction_reason", label: t("field.pay.deduction"), type: "note" },
      ],
    },
    {
      id: "leave",
      title: t("sec.leave"),
      desc: t("sec.leave.desc"),
      fields: [
        { key: "weekly_leave_days_per_week", label: t("field.leave.weeklyDays"), type: "number", min: 0, max: 7 },
        { key: "weekly_off_day_guaranteed", label: t("field.leave.offDay"), type: "yesno" },
        { key: "worked_off_day_paid_and_replaced", label: t("field.leave.workedOffDay"), type: "yesno" },
        { key: "public_holiday_paid_leave", label: t("field.leave.publicHoliday"), type: "yesno" },
        { key: "sick_leave_denied", label: t("field.leave.sickDenied"), type: "yesno" },
        { key: "pregnant_or_maternity_last_year", label: t("field.leave.pregnant"), type: "yesno" },
        {
          key: "maternity_leave_denied",
          label: t("field.leave.maternityDenied"),
          type: "yesno",
          visible: (d) => d.pregnant_or_maternity_last_year === "yes",
        },
        { key: "paternity_leave_denied", label: t("field.leave.paternityDenied"), type: "yesno" },
        { key: "mourning_leave_denied", label: t("field.leave.mourningDenied"), type: "yesno" },
      ],
    },
    {
      id: "contract",
      title: t("sec.contract"),
      desc: t("sec.contract.desc"),
      fields: [
        { key: "has_written_contract", label: t("field.contract.written"), type: "yesno" },
        {
          key: "contract_states_wage",
          label: t("field.contract.statesWage"),
          type: "yesno",
          visible: (d) => d.has_written_contract === "yes",
        },
        {
          key: "contract_states_hours",
          label: t("field.contract.statesHours"),
          type: "yesno",
          visible: (d) => d.has_written_contract === "yes",
        },
        {
          key: "contract_states_leave",
          label: t("field.contract.statesLeave"),
          type: "yesno",
          visible: (d) => d.has_written_contract === "yes",
        },
        {
          key: "contract_states_termination",
          label: t("field.contract.statesTermination"),
          type: "yesno",
          visible: (d) => d.has_written_contract === "yes",
        },
        {
          key: "contract_explained_in_own_language",
          label: t("field.contract.explained"),
          type: "yesno",
          visible: (d) => d.has_written_contract === "yes",
        },
      ],
    },
    {
      id: "social",
      title: t("sec.social"),
      desc: t("sec.social.desc"),
      fields: [
        { key: "ssf_registered", label: t("field.social.ssf"), type: "yesno" },
        { key: "pf_deducted", label: t("field.social.pfDeducted"), type: "yesno" },
        {
          key: "pf_deposited",
          label: t("field.social.pfDeposited"),
          type: "yesno",
          visible: (d) => d.pf_deducted === "yes",
        },
        { key: "gratuity_deducted", label: t("field.social.gratuityDeducted"), type: "yesno" },
        { key: "gratuity_paid_by_employer", label: t("field.social.gratuityPaid"), type: "yesno" },
        { key: "medical_insurance_provided", label: t("field.social.medical"), type: "yesno" },
        { key: "accidental_insurance_provided", label: t("field.social.accidental"), type: "yesno" },
      ],
    },
    {
      id: "recruitment",
      title: t("sec.recruitment"),
      desc: t("sec.recruitment.desc"),
      fields: [
        { key: "paid_fee_to_get_job", label: t("field.recruit.fee"), type: "yesno" },
        { key: "wage_withheld_before_start", label: t("field.recruit.withheld"), type: "yesno" },
        { key: "employer_holds_documents", label: t("field.recruit.documents"), type: "yesno" },
      ],
    },
    {
      id: "safety",
      title: t("sec.safety"),
      desc: t("sec.safety.desc"),
      fields: [
        { key: "free_to_leave_during_off_hours", label: t("field.safety.freeToLeave"), type: "yesno" },
        { key: "abuse_experienced", label: t("field.safety.abuse"), type: "yesno" },
        { key: "abuse_support_note", label: t("field.safety.abuse.details"), type: "note", visible: (d) => d.abuse_experienced === "yes" },
      ],
    },
    {
      id: "termination",
      title: t("sec.termination"),
      desc: t("sec.termination.desc"),
      fields: [
        { key: "terminated", label: t("field.term.occurred"), type: "yesno" },
        {
          key: "notice_given_days",
          label: t("field.term.notice"),
          type: "number",
          min: 0,
          max: 365,
          visible: (d) => d.terminated === "yes",
        },
        {
          key: "retrenchment_compensation_months",
          label: t("field.term.compensation"),
          type: "number",
          min: 0,
          visible: (d) => d.terminated === "yes",
        },
        {
          key: "final_settlement_within_15_days",
          label: t("field.term.settlement"),
          type: "yesno",
          visible: (d) => d.terminated === "yes",
        },
      ],
    },
    {
      id: "other",
      title: t("sec.other"),
      desc: t("sec.other.desc"),
      fields: [
        { key: "other_clauses", label: t("field.other.clauses"), type: "textlist" },
      ],
    },
  ];
}

// Fields the user is allowed to leave blank even when visible.
const OPTIONAL_KEYS = new Set(["work_address", "job_title", "other_deduction_reason"]);

// Group consecutive fields that share a `group` id so they render side by side.
function groupFields(fields: FieldDef[]): (FieldDef | FieldDef[])[] {
  const out: (FieldDef | FieldDef[])[] = [];
  for (const f of fields) {
    if (f.group) {
      const last = out[out.length - 1];
      if (Array.isArray(last) && last[0].group === f.group) last.push(f);
      else out.push([f]);
    } else {
      out.push(f);
    }
  }
  return out;
}

function rangeMessage(
  field: FieldDef,
  t: (k: string, vars?: Record<string, string | number>) => string,
): string {
  const { label, min, max } = field;
  if (min !== undefined && max !== undefined) return t("form.err.range", { field: label, min, max });
  if (max !== undefined) return t("form.err.max", { field: label, max });
  return t("form.err.min", { field: label, min: min ?? 0 });
}

// Validate a list of already-visible fields. Returns the first error message.
function validateFields(
  fields: FieldDef[],
  data: FormData,
  t: (k: string, vars?: Record<string, string | number>) => string,
): string | null {
  for (const f of fields) {
    if (f.type === "note" || OPTIONAL_KEYS.has(f.key)) continue;
    const value = data[f.key] ?? "";
    if (f.type === "number") {
      if (value === "") return t("form.err.required", { field: f.label });
      const n = Number(value);
      if (!Number.isFinite(n)) return t("form.err.number", { field: f.label });
      if (f.min !== undefined && n < f.min) return rangeMessage(f, t);
      if (f.max !== undefined && n > f.max) return rangeMessage(f, t);
    } else if (f.type === "chips") {
      let selected: unknown;
      try {
        selected = JSON.parse(value);
      } catch {
        selected = [];
      }
      if (!Array.isArray(selected) || selected.length === 0) {
        return t("form.err.required", { field: f.label });
      }
    } else if (f.type === "select" || f.type === "yesno") {
      if (value === "") return t("form.err.required", { field: f.label });
    } else if (f.type === "text") {
      if (value.trim() === "") return t("form.err.required", { field: f.label });
    } else if (f.type === "date" || f.type === "time") {
      if (value === "") return t("form.err.required", { field: f.label });
    }
  }
  return null;
}

function fromEmployer(e: Employer | null): FormData {
  const d: FormData = {};
  if (!e) return d;
  const map: Record<string, keyof Employer> = {
    employer_name: "employer_name",
    work_province: "work_province",
    work_district: "work_district",
    work_address: "work_address",
    skill_level: "skill_level",
    industry: "industry",
    employment_type: "employment_type",
    job_title: "job_title",
    hiring_channel: "hiring_channel",
    contractor_name: "contractor_name",
    tenure_years: "tenure_years",
    tenure_months: "tenure_months",
    on_probation: "on_probation",
    probation_since: "probation_since",
    contract_hours_per_day: "contract_hours_per_day",
    contract_break_start: "contract_break_start",
    contract_break_end: "contract_break_end",
    contract_break_unspecified: "contract_break_unspecified",
    contract_days_per_week: "contract_days_per_week",
    contract_break_days: "contract_break_days",
    contract_break_days_unspecified: "contract_break_days_unspecified",
    contract_months_per_year: "contract_months_per_year",
    actual_hours_per_day: "actual_hours_per_day",
    actual_break_start: "actual_break_start",
    actual_break_end: "actual_break_end",
    actual_break_unspecified: "actual_break_unspecified",
    actual_days_per_week: "actual_days_per_week",
    actual_break_days: "actual_break_days",
    actual_break_days_unspecified: "actual_break_days_unspecified",
    actual_months_per_year: "actual_months_per_year",
    overtime_rule: "overtime_rule",
    overtime_hours_per_unit: "overtime_hours_per_unit",
    overtime_unit: "overtime_unit",
    overtime_rate: "overtime_rate",
    overtime_rate_other: "overtime_rate_other",
    overtime_consent: "overtime_consent",
    night_work: "night_work",
    night_allowance: "night_allowance",
    pay_unit: "pay_unit",
    promised_wage: "promised_wage",
    payment_frequency: "payment_frequency",
    payment_method: "payment_method",
    received_annual_increment: "received_annual_increment",
    festival_expense_paid: "festival_expense_paid",
    other_deduction_reason: "other_deduction_reason",
    weekly_leave_days_per_week: "weekly_leave_days_per_week",
    weekly_off_day_guaranteed: "weekly_off_day_guaranteed",
    worked_off_day_paid_and_replaced: "worked_off_day_paid_and_replaced",
    public_holiday_paid_leave: "public_holiday_paid_leave",
    sick_leave_denied: "sick_leave_denied",
    pregnant_or_maternity_last_year: "pregnant_or_maternity_last_year",
    maternity_leave_denied: "maternity_leave_denied",
    paternity_leave_denied: "paternity_leave_denied",
    mourning_leave_denied: "mourning_leave_denied",
    has_written_contract: "has_written_contract",
    contract_states_wage: "contract_states_wage",
    contract_states_hours: "contract_states_hours",
    contract_states_leave: "contract_states_leave",
    contract_states_termination: "contract_states_termination",
    contract_explained_in_own_language: "contract_explained_in_own_language",
    ssf_registered: "ssf_registered",
    pf_deducted: "pf_deducted",
    pf_deposited: "pf_deposited",
    gratuity_deducted: "gratuity_deducted",
    gratuity_paid_by_employer: "gratuity_paid_by_employer",
    medical_insurance_provided: "medical_insurance_provided",
    accidental_insurance_provided: "accidental_insurance_provided",
    paid_fee_to_get_job: "paid_fee_to_get_job",
    wage_withheld_before_start: "wage_withheld_before_start",
    employer_holds_documents: "employer_holds_documents",
    free_to_leave_during_off_hours: "free_to_leave_during_off_hours",
    abuse_experienced: "abuse_experienced",
    terminated: "terminated",
    notice_given_days: "notice_given_days",
    retrenchment_compensation_months: "retrenchment_compensation_months",
    final_settlement_within_15_days: "final_settlement_within_15_days",
    other_clauses: "other_clauses",
  };
  for (const [key, field] of Object.entries(map)) {
    const v = e[field];
    if (v === undefined || v === null) continue;
    if (typeof v === "boolean") d[key] = v ? "yes" : "no";
    else if (Array.isArray(v)) d[key] = JSON.stringify(v);
    else d[key] = String(v);
  }
  return d;
}

export default function EmployerForm({ existing }: { existing?: Employer | null }) {
  const { t, lang } = useLanguage();
  const { user } = useAuth();
  const router = useRouter();

  const sections = useMemo(() => buildSections(t), [t]);
  const [data, setData] = useState<FormData>(() => fromEmployer(existing ?? null));
  const [sectionIdx, setSectionIdx] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const set = (key: string, value: string) => {
    setData((d) => ({ ...d, [key]: value }));
    setSaved(false);
  };

  const toggleChoice = (key: string, value: string) => {
    let current: Set<string>;
    try {
      current = new Set<string>(data[key] ? JSON.parse(data[key]) : []);
    } catch {
      current = new Set<string>();
    }
    if (current.has(value)) current.delete(value);
    else current.add(value);
    set(key, JSON.stringify([...current]));
  };

  const ageUnder18 = user?.age !== undefined && user.age !== null && user.age < 18;
  const under18Flag =
    ageUnder18 && (data.night_work === "yes" || data.overtime_rule === "yes");

  const section = sections[sectionIdx];
  const visibleFields = section.fields.filter((f) => f.visible?.(data) ?? true);
  const rows = groupFields(visibleFields);

  const validateSection = (idx: number): string | null =>
    validateFields(
      sections[idx].fields.filter((f) => f.visible?.(data) ?? true),
      data,
      t,
    );

  const next = () => {
    const err = validateSection(sectionIdx);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    if (sectionIdx < sections.length - 1) setSectionIdx((i) => i + 1);
    else submit();
  };

  const submit = async () => {
    for (let i = 0; i < sections.length; i++) {
      const err = validateSection(i);
      if (err) {
        setError(err);
        setSectionIdx(i);
        return;
      }
    }
    setBusy(true);
    setError(null);
    const payload = toPayload(data);
    try {
      if (existing) await updateEmployer(existing.id, payload);
      else await createEmployer(payload);
      setSaved(true);
      if (existing) {
        router.push("/profile");
      } else {
        router.push("/home");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("form.error"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      {/* Section stepper */}
      <div className="mb-4 flex items-center justify-between">
        <button
          type="button"
          onClick={() => (sectionIdx === 0 ? router.back() : setSectionIdx((i) => i - 1))}
          className="text-sm font-medium text-slate-500"
        >
          ← {t("form.back")}
        </button>
        <span className="text-xs text-slate-500">
          {sectionIdx + 1} / {sections.length}
        </span>
      </div>

      <div className="mb-1">
        <h1 className="text-xl font-bold text-slate-900">{section.title}</h1>
        <p className="mt-1 text-sm text-slate-600">{section.desc}</p>
      </div>

      {under18Flag ? (
        <div className="my-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">
          ⚠ {lang === "ne" ? "तपाईं १८ वर्षभन्दा कानुन भएको देखिनुहुन्छ र रात्रि काम वा ओभरटाइम उल्लेख गर्नुभयो — कानुनले किशोर श्रमलाई प्रतिबन्ध गर्छ (श्रम ऐन §4)।" : "You appear to be under 18 and have noted night work or overtime — the law restricts child labour (Labour Act §4)."}
        </div>
      ) : null}

      <div className="mt-4 space-y-4">
        {rows.map((row, idx) =>
          Array.isArray(row) ? (
            <GroupRenderer key={idx} group={row} data={data} set={set} />
          ) : (
            <FieldRenderer
              key={row.key}
              field={row}
              data={data}
              set={set}
              toggleChoice={toggleChoice}
              lang={lang}
            />
          ),
        )}
      </div>

      {error ? (
        <p className="mt-4 rounded-lg bg-red-100 px-3 py-2 text-sm text-red-800">{error}</p>
      ) : null}
      {saved ? (
        <p className="mt-4 rounded-lg bg-brand-100 px-3 py-2 text-sm text-brand-800">{t("form.saved")}</p>
      ) : null}

      <button
        type="button"
        onClick={next}
        disabled={busy}
        className="btn-primary mt-6 w-full"
      >
        {busy ? t("form.saving") : sectionIdx === sections.length - 1 ? t("form.submit") : t("form.next")}
      </button>
    </div>
  );
}

function GroupRenderer({
  group,
  data,
  set,
}: {
  group: FieldDef[];
  data: FormData;
  set: (k: string, v: string) => void;
}) {
  const label = group[0]?.label ?? "";
  return (
    <div>
      <FieldLabel text={label} />
      <div className="grid grid-cols-2 gap-3">
        {group.map((f) => (
          <TextField
            key={f.key}
            label={f.groupLabel ?? f.label}
            value={data[f.key] ?? ""}
            onChange={(v) => set(f.key, v)}
            type={f.type === "date" ? "date" : f.type === "time" ? "time" : "number"}
            inputMode="decimal"
            min={f.min}
            max={f.max}
          />
        ))}
      </div>
    </div>
  );
}

function FieldRenderer({
  field,
  data,
  set,
  toggleChoice,
  lang,
}: {
  field: FieldDef;
  data: FormData;
  set: (k: string, v: string) => void;
  toggleChoice: (k: string, v: string) => void;
  lang: "en" | "ne";
}) {
  const value = data[field.key] ?? "";
  const label = field.labelFor ? field.labelFor(data) : field.label;
  const hint = field.hint === "option.hoursGt5" ? (lang === "ne" ? "५ घण्टाभन्दा बढी भए विश्रामको समय सोधिनेछ" : "Asked only if more than 5 hours") : field.hint;

  switch (field.type) {
    case "text":
      return <TextField label={label} value={value} onChange={(v) => set(field.key, v)} />;
    case "number":
      return (
        <TextField
          label={label}
          value={value}
          onChange={(v) => set(field.key, v)}
          type="number"
          inputMode="decimal"
          hint={hint}
          min={field.min}
          max={field.max}
        />
      );
    case "date":
      return <TextField label={label} value={value} onChange={(v) => set(field.key, v)} type="date" />;
    case "time":
      return <TextField label={label} value={value} onChange={(v) => set(field.key, v)} type="time" />;
    case "select": {
      // Province / district are special-cased below.
      if (field.key === "work_province") {
        return (
          <SelectField
            label={label}
            value={value}
            onChange={(v) => {
              set("work_province", v);
              set("work_district", "");
            }}
            options={PROVINCES.map((p) => ({ value: p.id, en: p.en, ne: p.ne }))}
          />
        );
      }
      if (field.key === "work_district") {
        const province = PROVINCES.find((p) => p.id === data.work_province);
        return (
          <SelectField
            label={label}
            value={value}
            onChange={(v) => set(field.key, v)}
            options={province?.districts ?? []}
          />
        );
      }
      return (
        <SelectField
          label={label}
          value={value}
          onChange={(v) => set(field.key, v)}
          options={field.options ?? []}
        />
      );
    }
    case "yesno":
      return <YesNoGroup label={label} value={value} onChange={(v) => set(field.key, v)} hint={hint} />;
    case "chips": {
      let selected: Set<string>;
      try {
        selected = new Set<string>(value ? JSON.parse(value) : []);
      } catch {
        selected = new Set<string>();
      }
      return (
        <fieldset>
          <span className="mb-1.5 block text-sm font-medium text-slate-800">{label}</span>
          <div className="flex flex-wrap gap-2">
            {(field.options ?? []).map((o) => {
              const active = selected.has(o.value);
              return (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => toggleChoice(field.key, o.value)}
                  aria-pressed={active}
                  className={`rounded-full border px-3 py-1.5 text-sm ${
                    active
                      ? "border-brand-600 bg-brand-50 font-medium text-brand-800"
                      : "border-slate-300 bg-white text-slate-700"
                  }`}
                >
                  {lang === "ne" ? o.ne : o.en}
                </button>
              );
            })}
          </div>
        </fieldset>
      );
    }
    case "checkbox":
      return (
        <CheckboxField
          label={label}
          checked={value === "yes"}
          onChange={(v) => set(field.key, v ? "yes" : "no")}
        />
      );
    case "textlist": {
      let items: string[];
      try {
        items = value ? (JSON.parse(value) as string[]) : [];
      } catch {
        items = [];
      }
      const update = (next: string[]) =>
        set(field.key, next.length ? JSON.stringify(next) : "");
      const remove = (index: number) => update(items.filter((_, i) => i !== index));
      return (
        <fieldset>
          <span className="mb-1.5 block text-sm font-medium text-slate-800">{label}</span>
          <div className="space-y-2">
            {items.map((item, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  value={item}
                  placeholder={lang === "ne" ? "सर्त लेख्नुहोस्..." : "Type a clause..."}
                  onChange={(e) =>
                    update(items.map((x, j) => (j === i ? e.target.value : x)))
                  }
                />
                <button
                  type="button"
                  onClick={() => remove(i)}
                  aria-label="Remove clause"
                  className="shrink-0 rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm text-slate-500 active:bg-slate-100"
                >
                  ✕
                </button>
              </div>
            ))}
            <button
              type="button"
              onClick={() => update([...items, ""])}
              className="text-sm font-medium text-brand-700"
            >
              + {lang === "ne" ? "सर्त थप्नुहोस्" : "Add clause"}
            </button>
          </div>
        </fieldset>
      );
    }
    case "note":
      return (
        <>
          <InfoCard text={label} />
          {field.key === "other_deduction_reason" ? (
            <TextField
              label=""
              value={value}
              onChange={(v) => set(field.key, v)}
              placeholder={lang === "ne" ? "जस्तै: उपस्थिति, दण्ड, फारम शुल्क..." : "e.g. attendance fine, uniform, form fee..."}
            />
          ) : null}
        </>
      );
    default:
      return null;
  }
}

function toPayload(data: FormData): Partial<Employer> {
  const p: Partial<Employer> = {};
  const NUMERIC = new Set([
    "tenure_years",
    "tenure_months",
    "contract_hours_per_day",
    "contract_days_per_week",
    "contract_months_per_year",
    "actual_hours_per_day",
    "actual_days_per_week",
    "actual_months_per_year",
    "overtime_hours_per_unit",
    "overtime_rate_other",
    "promised_wage",
    "weekly_leave_days_per_week",
    "notice_given_days",
    "retrenchment_compensation_months",
  ]);
  const BOOL = new Set([
    "contract_break_unspecified",
    "contract_break_days_unspecified",
    "actual_break_unspecified",
    "actual_break_days_unspecified",
    "overtime_rule",
    "night_work",
    "night_allowance",
    "received_annual_increment",
    "festival_expense_paid",
    "weekly_off_day_guaranteed",
    "worked_off_day_paid_and_replaced",
    "public_holiday_paid_leave",
    "sick_leave_denied",
    "pregnant_or_maternity_last_year",
    "maternity_leave_denied",
    "paternity_leave_denied",
    "mourning_leave_denied",
    "has_written_contract",
    "contract_states_wage",
    "contract_states_hours",
    "contract_states_leave",
    "contract_states_termination",
    "contract_explained_in_own_language",
    "ssf_registered",
    "pf_deducted",
    "pf_deposited",
    "gratuity_deducted",
    "gratuity_paid_by_employer",
    "medical_insurance_provided",
    "accidental_insurance_provided",
    "paid_fee_to_get_job",
    "wage_withheld_before_start",
    "employer_holds_documents",
    "free_to_leave_during_off_hours",
    "abuse_experienced",
    "terminated",
    "final_settlement_within_15_days",
    "on_probation",
  ]);
  const ARRAY = new Set(["contract_break_days", "actual_break_days", "other_clauses"]);
  const DATE = new Set(["probation_since"]);

  for (const [key, value] of Object.entries(data)) {
    if (value === "" || value === undefined) continue;
    if (ARRAY.has(key)) {
      const arr = JSON.parse(value) as string[];
      p[key as keyof Employer] = arr as never;
    } else if (BOOL.has(key)) {
      p[key as keyof Employer] = (value === "yes") as never;
    } else if (NUMERIC.has(key)) {
      const n = Number(value);
      if (!Number.isNaN(n)) p[key as keyof Employer] = n as never;
    } else if (DATE.has(key)) {
      p[key as keyof Employer] = value as never;
    } else {
      p[key as keyof Employer] = value as never;
    }
  }
  return p;
}
