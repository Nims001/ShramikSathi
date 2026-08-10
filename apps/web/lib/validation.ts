"use client";

// Client-side validation matching the backend Pydantic schema shapes, so bad
// input is caught before it ever reaches the API.

import { z } from "zod";

import type { SubmissionPayload } from "./types";

// A helper that accepts "" or null for optional values.
const optionalNumber = z
  .union([z.number(), z.string(), z.null()])
  .transform((v) => {
    if (v === "" || v === null) return null;
    const n = typeof v === "number" ? v : Number(v);
    return Number.isFinite(n) ? n : null;
  });

const optionalBool = z
  .union([z.boolean(), z.enum(["", "true", "false"]), z.null()])
  .transform((v) => (v === "true" ? true : v === "false" ? false : null));

export const submissionSchema = z.object({
  employment_type: z.enum(["regular", "work_based", "time_based", "casual", "part_time"]),
  sector: z.string().trim().max(80).optional().or(z.literal("")),
  province: z.string().optional().or(z.literal("")),
  gender: z.string().optional().or(z.literal("")),
  hours_per_day: optionalNumber.optional(),
  hours_per_week: optionalNumber.optional(),
  worked_over_5h_without_break: optionalBool.optional(),
  overtime_hours_per_week: optionalNumber.optional(),
  overtime_rate_paid: optionalNumber.optional(),
  daily_wage: optionalNumber.optional(),
  monthly_wage: optionalNumber.optional(),
  wage_payment_interval_days: optionalNumber.optional(),
  months_worked: optionalNumber.optional(),
  years_worked: optionalNumber.optional(),
  received_annual_increment: optionalBool.optional(),
  festival_expense_paid: optionalBool.optional(),
  other_deduction_reason: z.string().trim().max(200).optional().or(z.literal("")),
  weekly_leave_taken_per_month: optionalNumber.optional(),
  sick_leave_denied: optionalBool.optional(),
  maternity_leave_denied: optionalBool.optional(),
  paternity_leave_denied: optionalBool.optional(),
  mourning_leave_denied: optionalBool.optional(),
  has_written_contract: optionalBool.optional(),
  pf_deducted: optionalBool.optional(),
  pf_deposited: optionalBool.optional(),
  gratuity_deducted: optionalBool.optional(),
  gratuity_paid_by_employer: optionalBool.optional(),
  medical_insurance_provided: optionalBool.optional(),
  accidental_insurance_provided: optionalBool.optional(),
  termination_occurred: optionalBool.optional(),
  notice_given_days: optionalNumber.optional(),
  retrenchment_compensation_months_paid: optionalNumber.optional(),
  final_settlement_within_15_days: optionalBool.optional(),
});

export type FormValues = z.input<typeof submissionSchema>;

// Convert the raw form values (strings) into the API payload (numbers/null).
export function toPayload(form: FormValues): SubmissionPayload {
  const parsed = submissionSchema.parse(form);
  return {
    employment_type: parsed.employment_type,
    sector: parsed.sector || null,
    province: parsed.province || null,
    gender: parsed.gender || null,
    hours_per_day: parsed.hours_per_day ?? null,
    hours_per_week: parsed.hours_per_week ?? null,
    worked_over_5h_without_break: parsed.worked_over_5h_without_break ?? null,
    overtime_hours_per_week: parsed.overtime_hours_per_week ?? null,
    overtime_rate_paid: parsed.overtime_rate_paid ?? null,
    daily_wage: parsed.daily_wage ?? null,
    monthly_wage: parsed.monthly_wage ?? null,
    wage_payment_interval_days: parsed.wage_payment_interval_days ?? null,
    months_worked: parsed.months_worked ?? null,
    years_worked: parsed.years_worked ?? null,
    received_annual_increment: parsed.received_annual_increment ?? null,
    festival_expense_paid: parsed.festival_expense_paid ?? null,
    other_deduction_reason: parsed.other_deduction_reason || null,
    weekly_leave_taken_per_month: parsed.weekly_leave_taken_per_month ?? null,
    sick_leave_denied: parsed.sick_leave_denied ?? null,
    maternity_leave_denied: parsed.maternity_leave_denied ?? null,
    paternity_leave_denied: parsed.paternity_leave_denied ?? null,
    mourning_leave_denied: parsed.mourning_leave_denied ?? null,
    has_written_contract: parsed.has_written_contract ?? null,
    pf_deducted: parsed.pf_deducted ?? null,
    pf_deposited: parsed.pf_deposited ?? null,
    gratuity_deducted: parsed.gratuity_deducted ?? null,
    gratuity_paid_by_employer: parsed.gratuity_paid_by_employer ?? null,
    medical_insurance_provided: parsed.medical_insurance_provided ?? null,
    accidental_insurance_provided: parsed.accidental_insurance_provided ?? null,
    termination_occurred: parsed.termination_occurred ?? null,
    notice_given_days: parsed.notice_given_days ?? null,
    retrenchment_compensation_months_paid: parsed.retrenchment_compensation_months_paid ?? null,
    final_settlement_within_15_days: parsed.final_settlement_within_15_days ?? null,
  };
}
