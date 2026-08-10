// Thin typed wrapper around the FastAPI backend.
// The backend URL comes from NEXT_PUBLIC_API_URL (set in .env / compose).

import type {
  AiAnalysisResult,
  AnalysisDocument,
  AuthResponse,
  EmployeeLog,
  Employer,
  LinkedEmployee,
  LoginPayload,
  NegotiationResult,
  PendingLog,
  RegisterPayload,
  ShareCodeResponse,
  SubmissionPayload,
  SubmissionResult,
  WeeklySetting,
  WorkLog,
  WorkLogPeriod,
  WorkLogSummary,
  WorkLogVerify,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOKEN_KEY = "shramiksathi.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body.detail) message = String(body.detail);
    } catch {
      // keep default message when the body isn't JSON
    }
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function headers(json = true): HeadersInit {
  const h: Record<string, string> = {};
  const token = getToken();
  if (token) h.Authorization = `Bearer ${token}`;
  if (json) h["Content-Type"] = "application/json";
  return h;
}

// ─── Auth ──────────────────────────────────────────────────────────────────

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  const data = await handle<AuthResponse>(res);
  setToken(data.token);
  return data;
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  const data = await handle<AuthResponse>(res);
  setToken(data.token);
  return data;
}

export async function logout(): Promise<void> {
  try {
    const res = await fetch(`${API_URL}/api/auth/logout`, { method: "POST", headers: headers() });
    await handle<void>(res);
  } finally {
    setToken(null);
  }
}

export async function fetchMe(): Promise<AuthResponse["user"]> {
  const res = await fetch(`${API_URL}/api/auth/me`, { headers: headers() });
  return handle<AuthResponse["user"]>(res);
}

export async function updateMe(
  payload: Partial<Pick<AuthResponse["user"], "gender" | "date_of_birth" | "ethnicity" | "education_level" | "language">>,
): Promise<AuthResponse["user"]> {
  const res = await fetch(`${API_URL}/api/auth/me`, {
    method: "PATCH",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  return handle<AuthResponse["user"]>(res);
}

// ─── Employers ─────────────────────────────────────────────────────────────

export async function listEmployers(): Promise<Employer[]> {
  const res = await fetch(`${API_URL}/api/employers`, { headers: headers() });
  return handle<Employer[]>(res);
}

export async function createEmployer(payload: Partial<Employer>): Promise<Employer> {
  const res = await fetch(`${API_URL}/api/employers`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  return handle<Employer>(res);
}

export async function updateEmployer(
  id: string,
  payload: Partial<Employer>,
): Promise<Employer> {
  const res = await fetch(`${API_URL}/api/employers/${id}`, {
    method: "PATCH",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  return handle<Employer>(res);
}

export async function deleteEmployer(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/employers/${id}`, {
    method: "DELETE",
    headers: headers(),
  });
  return handle<void>(res);
}

// ─── Weekly settings & work logs ───────────────────────────────────────────

export async function upsertWeeklySettings(
  employerId: string,
  payload: Partial<WeeklySetting>,
): Promise<WeeklySetting> {
  const res = await fetch(`${API_URL}/api/employers/${employerId}/weekly-settings`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  return handle<WeeklySetting>(res);
}

export async function listWeeklySettings(): Promise<WeeklySetting[]> {
  const res = await fetch(`${API_URL}/api/weekly-settings`, { headers: headers() });
  return handle<WeeklySetting[]>(res);
}

export async function listWorklogs(): Promise<WorkLog[]> {
  const res = await fetch(`${API_URL}/api/worklogs`, { headers: headers() });
  return handle<WorkLog[]>(res);
}

export async function getWorklogSummary(period: WorkLogPeriod): Promise<WorkLogSummary> {
  const tzOffset = -new Date().getTimezoneOffset();
  const res = await fetch(
    `${API_URL}/api/worklogs/summary?period=${period}&tz_offset=${tzOffset}`,
    { headers: headers() },
  );
  return handle<WorkLogSummary>(res);
}

export async function createWorklog(payload: Partial<WorkLog>): Promise<WorkLog> {
  const res = await fetch(`${API_URL}/api/worklogs`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  return handle<WorkLog>(res);
}

export async function updateWorklog(
  id: string,
  payload: Partial<WorkLog>,
): Promise<WorkLog> {
  const res = await fetch(`${API_URL}/api/worklogs/${id}`, {
    method: "PATCH",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  return handle<WorkLog>(res);
}

export async function signWorklog(id: string): Promise<WorkLog> {
  const res = await fetch(`${API_URL}/api/worklogs/${id}/sign`, {
    method: "POST",
    headers: headers(),
  });
  return handle<WorkLog>(res);
}

export async function verifyWorklog(id: string): Promise<WorkLogVerify> {
  const res = await fetch(`${API_URL}/api/worklogs/${id}/verify`, {
    headers: headers(),
  });
  return handle<WorkLogVerify>(res);
}

// ─── Anonymous rights check (voice / quick intake) ─────────────────────────

export async function submitCheck(payload: SubmissionPayload): Promise<SubmissionResult> {
  const res = await fetch(`${API_URL}/api/submissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handle<SubmissionResult>(res);
}

// ─── Analysis ──────────────────────────────────────────────────────────────

export async function getAnalysis(): Promise<AnalysisDocument> {
  const res = await fetch(`${API_URL}/api/analysis`, { headers: headers() });
  return handle<AnalysisDocument>(res);
}

export async function analyseWithAI(): Promise<AiAnalysisResult> {
  const res = await fetch(`${API_URL}/api/analysis/ai`, {
    method: "POST",
    headers: headers(),
  });
  return handle<AiAnalysisResult>(res);
}

export async function generateNegotiationScript(): Promise<NegotiationResult> {
  const res = await fetch(`${API_URL}/api/analysis/negotiate`, {
    method: "POST",
    headers: headers(),
  });
  return handle<NegotiationResult>(res);
}

// ─── Integration stubs (Nagarik SSO / Sharmsansar export) ─────────────────

export async function nagarikSso(): Promise<{ detail?: string }> {
  const res = await fetch(`${API_URL}/api/integrations/nagarik/sso`, {
    method: "POST",
    headers: headers(),
  });
  return handle<{ detail?: string }>(res);
}

export async function sharmsansarExport(): Promise<unknown> {
  const res = await fetch(`${API_URL}/api/integrations/sharmsansar/export`, {
    headers: headers(),
  });
  return handle<unknown>(res);
}

// ─── Employer portal ────────────────────────────────────────────────────────

export async function generateShareCode(): Promise<ShareCodeResponse> {
  const res = await fetch(`${API_URL}/api/me/share-code`, {
    method: "POST",
    headers: headers(),
  });
  return handle<ShareCodeResponse>(res);
}

export async function linkEmployee(code: string): Promise<LinkedEmployee> {
  const res = await fetch(`${API_URL}/api/employer-portal/link`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ code }),
  });
  return handle<LinkedEmployee>(res);
}

export async function listLinkedEmployees(): Promise<LinkedEmployee[]> {
  const res = await fetch(`${API_URL}/api/employer-portal/employees`, {
    headers: headers(),
  });
  return handle<LinkedEmployee[]>(res);
}

export async function getEmployeeLogs(employeeId: string): Promise<EmployeeLog[]> {
  const res = await fetch(`${API_URL}/api/employer-portal/employees/${employeeId}/logs`, {
    headers: headers(),
  });
  return handle<EmployeeLog[]>(res);
}

export async function listPendingLogs(): Promise<PendingLog[]> {
  const res = await fetch(`${API_URL}/api/employer-portal/pending-logs`, {
    headers: headers(),
  });
  return handle<PendingLog[]>(res);
}

export async function approveLog(employeeId: string, logId: string): Promise<EmployeeLog> {
  const res = await fetch(
    `${API_URL}/api/employer-portal/employees/${employeeId}/logs/${logId}/approve`,
    { method: "POST", headers: headers() },
  );
  return handle<EmployeeLog>(res);
}

export async function rejectLog(
  employeeId: string,
  logId: string,
  reason: string,
): Promise<EmployeeLog> {
  const res = await fetch(
    `${API_URL}/api/employer-portal/employees/${employeeId}/logs/${logId}/reject`,
    { method: "POST", headers: headers(), body: JSON.stringify({ reason }) },
  );
  return handle<EmployeeLog>(res);
}
