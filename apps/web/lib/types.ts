// Shared client types mirroring the FastAPI / Pydantic schemas.

export type EmploymentType =
  | "regular"
  | "work_based"
  | "time_based"
  | "casual"
  | "part_time";

export type Severity = "info" | "warning" | "critical";

export interface SubmissionPayload {
  employment_type: EmploymentType;
  sector?: string | null;
  province?: string | null;
  gender?: string | null;
  hours_per_day?: number | null;
  hours_per_week?: number | null;
  worked_over_5h_without_break?: boolean | null;
  overtime_hours_per_week?: number | null;
  overtime_rate_paid?: number | null;
  daily_wage?: number | null;
  monthly_wage?: number | null;
  wage_payment_interval_days?: number | null;
  months_worked?: number | null;
  years_worked?: number | null;
  received_annual_increment?: boolean | null;
  festival_expense_paid?: boolean | null;
  other_deduction_reason?: string | null;
  weekly_leave_taken_per_month?: number | null;
  sick_leave_denied?: boolean | null;
  maternity_leave_denied?: boolean | null;
  paternity_leave_denied?: boolean | null;
  mourning_leave_denied?: boolean | null;
  has_written_contract?: boolean | null;
  pf_deducted?: boolean | null;
  pf_deposited?: boolean | null;
  gratuity_deducted?: boolean | null;
  gratuity_paid_by_employer?: boolean | null;
  medical_insurance_provided?: boolean | null;
  accidental_insurance_provided?: boolean | null;
  termination_occurred?: boolean | null;
  notice_given_days?: number | null;
  retrenchment_compensation_months_paid?: number | null;
  final_settlement_within_15_days?: boolean | null;
}

export interface Violation {
  rule_id: string;
  section_reference: string;
  severity: Severity;
  plain_explanation_en: string;
  plain_explanation_ne: string;
  suggested_action_en: string;
  suggested_action_ne: string;
}

export interface SubmissionResult {
  submission_id: string;
  created_at: string;
  violations: Violation[];
}

export interface OcrResult {
  candidate_fields: Partial<SubmissionPayload>;
  raw_text: string;
  warning?: string | null;
}

export interface DashboardStats {
  total_submissions: number;
  total_violations: number;
  by_rule: { key: string; count: number }[];
  by_sector: { key: string; count: number }[];
  by_province: { key: string; count: number }[];
  by_severity: { key: string; count: number }[];
}

// ─── Auth / account ────────────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  role: string;
  gender?: string | null;
  date_of_birth?: string | null;
  age?: number | null;
  ethnicity?: string | null;
  education_level?: string | null;
  language: string;
  created_at: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  role?: string;
  gender?: string | null;
  date_of_birth?: string | null;
  ethnicity?: string | null;
  education_level?: string | null;
  language?: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// ─── Employer ──────────────────────────────────────────────────────────────

export interface Employer {
  id: string;
  user_id: string;
  created_at: string;

  employer_name?: string | null;
  work_province?: string | null;
  work_district?: string | null;
  work_address?: string | null;
  skill_level?: string | null;
  industry?: string | null;
  employment_type?: string | null;
  job_title?: string | null;
  hiring_channel?: string | null;
  contractor_name?: string | null;
  tenure_years?: number | null;
  tenure_months?: number | null;
  on_probation?: boolean | null;
  probation_since?: string | null;

  contract_hours_per_day?: number | null;
  contract_break_start?: string | null;
  contract_break_end?: string | null;
  contract_break_unspecified?: boolean | null;
  contract_days_per_week?: number | null;
  contract_break_days?: string[] | null;
  contract_break_days_unspecified?: boolean | null;
  contract_months_per_year?: number | null;
  contract_break_months?: string[] | null;

  actual_hours_per_day?: number | null;
  actual_break_start?: string | null;
  actual_break_end?: string | null;
  actual_break_unspecified?: boolean | null;
  actual_days_per_week?: number | null;
  actual_break_days?: string[] | null;
  actual_break_days_unspecified?: boolean | null;
  actual_months_per_year?: number | null;
  actual_break_months?: string[] | null;

  overtime_rule?: boolean | null;
  overtime_hours_per_unit?: number | null;
  overtime_unit?: string | null;
  overtime_rate?: string | null;
  overtime_rate_other?: number | null;
  overtime_consent?: string | null;
  night_work?: boolean | null;
  night_allowance?: boolean | null;

  pay_unit?: string | null;
  promised_wage?: number | null;
  monthly_salary_calculated?: number | null;
  payment_frequency?: string | null;
  payment_method?: string | null;
  received_annual_increment?: boolean | null;
  festival_expense_paid?: boolean | null;
  other_deduction_reason?: string | null;

  weekly_leave_days_per_week?: number | null;
  weekly_off_day_guaranteed?: boolean | null;
  worked_off_day_paid_and_replaced?: boolean | null;
  public_holiday_paid_leave?: boolean | null;
  sick_leave_denied?: boolean | null;
  pregnant_or_maternity_last_year?: boolean | null;
  maternity_leave_denied?: boolean | null;
  paternity_leave_denied?: boolean | null;
  mourning_leave_denied?: boolean | null;

  has_written_contract?: boolean | null;
  contract_states_wage?: boolean | null;
  contract_states_hours?: boolean | null;
  contract_states_leave?: boolean | null;
  contract_states_termination?: boolean | null;
  contract_explained_in_own_language?: boolean | null;

  ssf_registered?: boolean | null;
  pf_deducted?: boolean | null;
  pf_deposited?: boolean | null;
  gratuity_deducted?: boolean | null;
  gratuity_paid_by_employer?: boolean | null;
  medical_insurance_provided?: boolean | null;
  accidental_insurance_provided?: boolean | null;

  paid_fee_to_get_job?: boolean | null;
  wage_withheld_before_start?: boolean | null;
  employer_holds_documents?: boolean | null;

  free_to_leave_during_off_hours?: boolean | null;
  abuse_experienced?: boolean | null;

  terminated?: boolean | null;
  notice_given_days?: number | null;
  retrenchment_compensation_months?: number | null;
  final_settlement_within_15_days?: boolean | null;

  // Other clauses (free-text list sent to the AI analysis)
  other_clauses?: string[] | null;

  // Server-computed
  contract_daily_hours?: number | null;
  contract_weekly_hours?: number | null;
  contract_monthly_hours?: number | null;
  actual_daily_hours?: number | null;
  actual_weekly_hours?: number | null;
  actual_monthly_hours?: number | null;
}

// ─── Work logs ─────────────────────────────────────────────────────────────

export interface WeeklySetting {
  id: string;
  employer_id: string;
  week_start?: string | null;
  break_days_this_week?: string[] | null;
  promised_payment_day?: string | null;
  daily_promised_wage?: number | null;
  created_at?: string | null;
}

export interface WorkLog {
  id: string;
  user_id: string;
  employer_id: string;
  log_date: string;
  report_time?: string | null;
  scheduled_end_time?: string | null;
  scheduled_break_start?: string | null;
  scheduled_break_end?: string | null;
  work_started_at?: string | null;
  work_ended_at?: string | null;
  breaks?: { start?: string; end?: string }[] | null;
  overtime_minutes: number;
  paid_amount?: number | null;
  promised_amount?: number | null;
  piece_count?: number | null;
  piece_rate?: number | null;
  deductions?: { label?: string; amount?: number }[] | null;
  note?: string | null;
  created_at: string;

  // Dual-consensus signing (ETA 2063 asymmetric cryptosystem).
  content_hash?: string | null;
  approval_status?: "draft" | "pending_employer" | "approved" | "rejected";
  submission_version?: number;
  employee_signature?: string | null;
  employee_signed_at?: string | null;
  employer_signature?: string | null;
  employer_signed_at?: string | null;
  employer_decision_at?: string | null;
  rejection_reason?: string | null;
}

export type WorkLogApprovalStatus = "draft" | "pending_employer" | "approved" | "rejected";

export interface WorkLogVerify {
  worklog_id: string;
  approval_status: WorkLogApprovalStatus;
  stored_content_hash: string;
  recomputed_content_hash: string;
  content_hash_matches: boolean;
  employee_signature_valid: boolean;
  employer_signature_valid: boolean;
  employee_signed_at?: string | null;
  employer_signed_at?: string | null;
}

// ─── Work log summary (dashboard) ──────────────────────────────────────────

export type WorkLogPeriod = "daily" | "weekly" | "monthly";

export interface SummaryRow {
  key: string;
  label: string;
  hours: number;
  overtime: number;
  promised: number;
  paid: number;
  days: number;
}

export interface EmployerSlice {
  name: string;
  value: number;
}

export interface WorkLogSummary {
  period: WorkLogPeriod;
  rows: SummaryRow[];
  by_employer: EmployerSlice[];
  total_logs: number;
}

// ─── Analysis document ─────────────────────────────────────────────────────

export interface DeterministicFinding {
  rule_id: string;
  section_reference: string;
  severity: "info" | "warning" | "critical";
  plain_explanation_en: string;
  plain_explanation_ne: string;
  suggested_action_en: string;
  suggested_action_ne: string;
}

export interface AnalysisDocument {
  meta: {
    generated_at: string;
    law_framework: string;
    analysis_mode: string;
  };
  user: {
    id: string;
    age?: number | null;
    gender?: string | null;
    ethnicity?: string | null;
    education_level?: string | null;
    language: string;
  };
  employers: {
    employer: Partial<Employer> & { id: string };
    weekly_setting: Partial<WeeklySetting> | null;
    logs: (Partial<WorkLog> & { id: string })[];
    deterministic_findings: DeterministicFinding[];
  }[];
  stats: {
    today: StatsSlice;
    last_7_days: StatsSlice;
    last_30_days: StatsSlice;
    last_90_days: StatsSlice;
    employer_count: number;
  };
}

export interface StatsSlice {
  days_worked: number;
  overtime_minutes: number;
  overtime_hours_rounded: number;
  paid_amount: number;
  promised_amount: number;
  amount_due: number;
}

// ─── "Analyse with AI" (RAG) ───────────────────────────────────────────────

export interface AiFinding {
  rule_id: string;
  section_reference: string;
  severity: Severity;
  plain_explanation_en: string;
  plain_explanation_ne?: string | null;
  suggested_action_en: string;
  suggested_action_ne?: string | null;
}

export interface AiEmployerFindings {
  employer_id: string;
  employer_name: string;
  findings: AiFinding[];
}

export interface AiAnalysisResult {
  ai_findings: AiEmployerFindings[];
  warning?: string | null;
  validation_errors?: string[];
}

// ─── Negotiation script (AI-generated) ─────────────────────────────────────

export interface EmployerScript {
  employer_id: string;
  employer_name: string;
  opening_en: string;
  opening_ne?: string | null;
  points_en: string[];
  points_ne?: string[] | null;
  closing_en: string;
  closing_ne?: string | null;
}

export interface NegotiationResult {
  scripts: EmployerScript[];
  warning?: string | null;
}

// ─── Employer portal ────────────────────────────────────────────────────────

export interface ShareCodeResponse {
  code: string;
}

export interface LinkedEmployee {
  employee_id: string;
  username: string;
  note?: string | null;
  linked_at: string;
  log_count: number;
}

export interface PendingLog extends EmployeeLog {
  employee_id: string;
  username: string;
}

export interface EmployeeLog {
  log_id: string;
  log_date: string;
  report_time?: string | null;
  scheduled_end_time?: string | null;
  scheduled_break_start?: string | null;
  scheduled_break_end?: string | null;
  work_started_at?: string | null;
  work_ended_at?: string | null;
  breaks?: { start?: string; end?: string }[] | null;
  overtime_minutes: number;
  paid_amount?: number | null;
  promised_amount?: number | null;
  piece_count?: number | null;
  piece_rate?: number | null;
  deductions?: { label?: string; amount?: number }[] | null;
  note?: string | null;
  workplace_name?: string | null;
  workplace_district?: string | null;

  // Dual-consensus signing (ETA 2063 asymmetric cryptosystem).
  approval_status?: WorkLogApprovalStatus;
  submission_version?: number;
  content_hash?: string | null;
  employee_signature?: string | null;
  employee_signed_at?: string | null;
  employer_signature?: string | null;
  employer_signed_at?: string | null;
  employer_decision_at?: string | null;
  rejection_reason?: string | null;
}
