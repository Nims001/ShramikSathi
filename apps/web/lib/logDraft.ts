// In-progress log draft persisted to localStorage so a running timer and the
// values already entered survive navigating to another page (or a refresh).
// Elapsed time keeps counting because the draft stores wall-clock start times
// and the display is always `now - startedAt`.

export type LogStatus = "idle" | "working" | "on_break";
export type LogStep = "presets" | "schedule" | "timer" | "payment" | "sign";

export type LogDraft = {
  version: 1;
  date: string;
  employerId: string;
  step: LogStep;
  status: LogStatus;
  startedAt: string | null;
  breakStart: string | null;
  endedAt: string | null;
  breaks: { start: string; end?: string }[];
  manualBreaks: { start: string; end: string }[];
  reportTime: string;
  scheduledEnd: string;
  schedBreakStart: string;
  schedBreakEnd: string;
  promised: string;
  pieces: string;
  pieceRate: string;
  paid: string;
  deductions: { label: string; amount: string }[];
  note: string;
  presetBreakDays: string[];
  presetPaymentDay: string;
  presetDailyWage: string;
};

export const LOG_DRAFT_KEY = "shramiksathi.log-draft.v1";

export function loadLogDraft(): LogDraft | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(LOG_DRAFT_KEY);
    if (!raw) return null;
    const draft = JSON.parse(raw) as LogDraft;
    if (!draft || draft.version !== 1) return null;
    return draft;
  } catch {
    return null;
  }
}

export function clearLogDraft(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(LOG_DRAFT_KEY);
  } catch {
    /* storage unavailable — nothing to clear */
  }
}
