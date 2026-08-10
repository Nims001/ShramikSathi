"use client";

// Voice-guided rights check (stretch goal).
//
// A fixed question sequence (no open-ended chat) that reads each question
// aloud with the browser's TTS and accepts spoken answers via the Web Speech
// API, with big on-screen buttons as a fallback for low-literacy users. The
// answers map to the same form data model as the form-based check
// (POST /api/submissions), so the results come from the deterministic rule
// engine — never from an LLM.

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import ViolationCard from "@/components/ViolationCard";
import { submitCheck } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { SubmissionPayload, SubmissionResult, Violation } from "@/lib/types";

type StepKey =
  | "employment_type"
  | "hours_per_day"
  | "hours_per_week"
  | "worked_over_5h_without_break"
  | "monthly_wage"
  | "weekly_leave_taken_per_month"
  | "has_written_contract";

type Answer = string | number | boolean;

interface Step {
  key: StepKey;
  kind: "choice" | "number" | "money" | "yesno";
  options?: string[];
  max?: number;
  unit?: string;
}

const STEPS: Step[] = [
  { key: "employment_type", kind: "choice", options: ["regular", "work_based", "time_based", "casual", "part_time"] },
  { key: "hours_per_day", kind: "number", max: 24, unit: "hrs" },
  { key: "hours_per_week", kind: "number", max: 168, unit: "hrs" },
  { key: "worked_over_5h_without_break", kind: "yesno" },
  { key: "monthly_wage", kind: "money" },
  { key: "weekly_leave_taken_per_month", kind: "number", max: 31, unit: "days" },
  { key: "has_written_contract", kind: "yesno" },
];

type Phase = "intro" | "qa" | "review" | "done" | "error";

function speak(text: string, lang: "en" | "ne") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang === "ne" ? "ne-NP" : "en-US";
  u.rate = 0.95;
  // Prefer a voice matching the language (or Hindi as a fallback for Nepali).
  const voices = window.speechSynthesis.getVoices();
  const match = voices.find((v) => v.lang.startsWith(u.lang)) || (lang === "ne" && voices.find((v) => v.lang.startsWith("hi")));
  if (match) u.voice = match;
  window.speechSynthesis.speak(u);
}

export default function VoicePage() {
  const { t, lang } = useLanguage();
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("intro");
  const [stepIndex, setStepIndex] = useState(0);
  const [answers, setAnswers] = useState<Partial<Record<StepKey, Answer>>>({});
  const [keypad, setKeypad] = useState("");
  const [listening, setListening] = useState(false);
  const [micSupport, setMicSupport] = useState<boolean | null>(null);
  const [result, setResult] = useState<SubmissionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const recRef = useRef<{ stop: () => void } | null>(null);

  const step = STEPS[stepIndex];
  const qText = (s: Step) =>
    s.kind === "choice"
      ? `${t(`voice.q.${s.key}`)} ${s.options?.map((o) => t(`voice.opt.${o}`)).join(", ")}.`
      : t(`voice.q.${s.key}`);

  // Read the current question aloud whenever it changes.
  useEffect(() => {
    if (phase === "qa") {
      const timer = setTimeout(() => speak(qText(step), lang), 250);
      return () => clearTimeout(timer);
    }
  }, [phase, stepIndex, lang]); // eslint-disable-line react-hooks/exhaustive-deps

  // Stop speaking / listening when leaving the page.
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
      recRef.current?.stop();
    };
  }, []);

  function goNext() {
    if (stepIndex + 1 < STEPS.length) setStepIndex((i) => i + 1);
    else setPhase("review");
    setKeypad("");
  }

  function goBack() {
    if (stepIndex > 0) setStepIndex((i) => i - 1);
    else setPhase("intro");
    setKeypad("");
  }

  function commit(key: StepKey, value: Answer) {
    setAnswers((a) => ({ ...a, [key]: value }));
    goNext();
  }

  function parseNumber(text: string): number | null {
    const m = text.match(/\d+(?:\.\d+)?/);
    return m ? parseFloat(m[0]) : null;
  }

  function parseYesNo(text: string): boolean | null {
    const s = text.toLowerCase();
    if (/\b(yes|yeah|yep|sure|ho|cha|hunchha)\b/.test(s)) return true;
    if (/\b(no|nope|nah|hoina|chaina)\b/.test(s)) return false;
    return null;
  }

  function handleTranscript(text: string) {
    if (step.kind === "yesno") {
      const v = parseYesNo(text);
      if (v !== null) commit(step.key, v);
      return;
    }
    if (step.kind === "number" || step.kind === "money") {
      const n = parseNumber(text);
      if (n !== null) {
        commit(step.key, step.kind === "money" ? Math.round(n) : n);
        return;
      }
    }
    if (step.kind === "choice" && step.options) {
      const s = text.toLowerCase();
      const hit = step.options.find((o) => s.includes(o.replace("_", " ")) || s.includes(o));
      if (hit) {
        commit(step.key, hit);
        return;
      }
    }
    // Unclear — speak a short prompt to try again.
    speak(t("voice.tryAgain"), lang);
  }

  function startListening() {
    const w = window as unknown as { SpeechRecognition?: new () => SpeechRecognition; webkitSpeechRecognition?: new () => SpeechRecognition };
    const SR = typeof window !== "undefined" ? w.SpeechRecognition || w.webkitSpeechRecognition : undefined;
    if (!SR) {
      setMicSupport(false);
      return;
    }
    setMicSupport(true);
    const rec = new SR();
    rec.lang = lang === "ne" ? "ne-NP" : "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e: SpeechRecognitionEvent) => {
      const text = e.results[e.resultIndex][0].transcript.trim();
      setListening(false);
      if (text) handleTranscript(text);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    setListening(true);
    rec.start();
  }

  function buildPayload(): SubmissionPayload {
    const empType = (answers.employment_type as string) || "regular";
    return {
      employment_type: (["regular", "work_based", "time_based", "casual", "part_time"].includes(empType)
        ? empType
        : "regular") as SubmissionPayload["employment_type"],
      hours_per_day: typeof answers.hours_per_day === "number" ? answers.hours_per_day : null,
      hours_per_week: typeof answers.hours_per_week === "number" ? answers.hours_per_week : null,
      worked_over_5h_without_break: typeof answers.worked_over_5h_without_break === "boolean" ? answers.worked_over_5h_without_break : null,
      monthly_wage: typeof answers.monthly_wage === "number" ? answers.monthly_wage : null,
      weekly_leave_taken_per_month: typeof answers.weekly_leave_taken_per_month === "number" ? answers.weekly_leave_taken_per_month : null,
      has_written_contract: typeof answers.has_written_contract === "boolean" ? answers.has_written_contract : null,
    };
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const res = await submitCheck(buildPayload());
      setResult(res);
      setPhase("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("error");
    } finally {
      setBusy(false);
    }
  }

  const restart = () => {
    setPhase("intro");
    setStepIndex(0);
    setAnswers({});
    setKeypad("");
    setResult(null);
    setError(null);
  };

  const answerLabel = (key: StepKey, value: Answer) => {
    if (typeof value === "boolean") return value ? t("voice.yes") : t("voice.no");
    if (key === "employment_type") return t(`voice.opt.${value}`);
    return String(value);
  };

  return (
    <div className="min-h-dvh bg-[#F8FAFC]">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-md items-center justify-between px-4 py-3">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600"
          >
            ← {t("voice.back")}
          </button>
          <div className="text-center">
            <h1 className="text-lg font-bold text-slate-900">{t("voice.title")}</h1>
            <p className="text-xs text-slate-500">{t("voice.subtitle")}</p>
          </div>
          {phase !== "intro" ? (
            <button
              type="button"
              onClick={() => speak(qText(step), lang)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600"
            >
              🔊 {t("voice.repeat")}
            </button>
          ) : (
            <span className="w-[76px]" />
          )}
        </div>
      </header>

      <main className="mx-auto w-full max-w-md px-4 py-6">
        {phase === "intro" ? (
          <div className="space-y-4">
            <div className="card p-6 text-center">
              <p className="text-3xl">🎙️</p>
              <h2 className="mt-2 text-lg font-bold text-slate-900">{t("voice.welcome")}</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{t("voice.welcomeDesc")}</p>
              <button
                type="button"
                onClick={() => {
                  setPhase("qa");
                  speak(qText(STEPS[0]), lang);
                }}
                className="btn-primary mt-5 w-full py-3 text-base"
              >
                {t("voice.start")}
              </button>
            </div>
            <p className="text-center text-[11px] text-slate-400">{t("ai.disclaimer")}</p>
          </div>
        ) : null}

        {phase === "qa" ? (
          <div className="space-y-4">
            {/* Progress */}
            <div className="flex items-center gap-1.5">
              {STEPS.map((s, i) => (
                <span
                  key={s.key}
                  className={`h-1.5 flex-1 rounded-full ${i < stepIndex ? "bg-brand-600" : i === stepIndex ? "bg-brand-400" : "bg-slate-200"}`}
                />
              ))}
            </div>

            <div className="card p-6 text-center">
              <p className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                {t("voice.question")} {stepIndex + 1} / {STEPS.length}
              </p>
              <h2 className="mt-3 text-xl font-bold leading-snug text-slate-900">{qText(step)}</h2>

              {/* Mic button */}
              <button
                type="button"
                onClick={startListening}
                disabled={listening}
                className={`mt-6 flex h-20 w-20 items-center justify-center rounded-full text-3xl transition-colors ${
                  listening ? "animate-pulse bg-red-100" : "bg-brand-600"
                }`}
                aria-label={t("voice.mic")}
              >
                {listening ? "🔴" : "🎙️"}
              </button>
              <p className="mt-3 text-sm text-slate-500">
                {listening ? t("voice.listening") : micSupport === false ? t("voice.noMic") : t("voice.micHint")}
              </p>
            </div>

            {/* Answer controls */}
            <div className="card p-4">
              {step.kind === "choice" ? (
                <div className="grid gap-2">
                  {step.options?.map((o) => (
                    <button
                      key={o}
                      type="button"
                      onClick={() => commit(step.key, o)}
                      className="rounded-xl border border-slate-300 bg-white px-4 py-3.5 text-left text-base font-medium text-slate-800 active:bg-slate-50"
                    >
                      {t(`voice.opt.${o}`)}
                    </button>
                  ))}
                </div>
              ) : null}

              {step.kind === "yesno" ? (
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => commit(step.key, true)}
                    className="rounded-xl bg-brand-600 px-4 py-4 text-lg font-semibold text-white"
                  >
                    {t("voice.yes")}
                  </button>
                  <button
                    type="button"
                    onClick={() => commit(step.key, false)}
                    className="rounded-xl border border-slate-300 bg-white px-4 py-4 text-lg font-semibold text-slate-800"
                  >
                    {t("voice.no")}
                  </button>
                </div>
              ) : null}

              {step.kind === "number" || step.kind === "money" ? (
                <div>
                  <div className="mb-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-3xl font-bold text-slate-900">
                    {keypad || "—"}
                    {keypad && step.unit ? (
                      <span className="ml-2 text-sm font-medium text-slate-400">{t(`voice.unit.${step.unit}`)}</span>
                    ) : null}
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((d) => (
                      <button
                        key={d}
                        type="button"
                        onClick={() => setKeypad((k) => (k + d).slice(0, 6))}
                        className="rounded-xl border border-slate-200 bg-white py-4 text-xl font-semibold text-slate-800 active:bg-slate-50"
                      >
                        {d}
                      </button>
                    ))}
                    <button
                      type="button"
                      onClick={() => setKeypad((k) => k.slice(0, -1))}
                      className="rounded-xl border border-slate-200 bg-white py-4 text-lg font-semibold text-slate-600"
                    >
                      ⌫
                    </button>
                    <button
                      type="button"
                      onClick={() => setKeypad((k) => (k + "0").slice(0, 6))}
                      className="rounded-xl border border-slate-200 bg-white py-4 text-xl font-semibold text-slate-800 active:bg-slate-50"
                    >
                      0
                    </button>
                    <button
                      type="button"
                      onClick={() => setKeypad("")}
                      className="rounded-xl border border-slate-200 bg-white py-4 text-base font-medium text-slate-600"
                    >
                      {t("voice.clear")}
                    </button>
                  </div>
                  <button
                    type="button"
                    disabled={!keypad}
                    onClick={() => commit(step.key, parseFloat(keypad))}
                    className="btn-primary mt-3 w-full py-3.5 text-base disabled:opacity-40"
                  >
                    {t("voice.next")} →
                  </button>
                </div>
              ) : null}
            </div>

            <button type="button" onClick={goBack} className="w-full text-center text-sm font-medium text-slate-500">
              ← {t("voice.back")}
            </button>
          </div>
        ) : null}

        {phase === "review" ? (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900">{t("voice.review")}</h2>
            <div className="card divide-y divide-slate-100 p-0">
              {STEPS.map((s) => (
                <div key={s.key} className="flex items-center justify-between gap-2 px-4 py-3">
                  <span className="text-sm text-slate-600">{t(`voice.q.${s.key}`)}</span>
                  <span className="shrink-0 text-sm font-semibold text-slate-900">
                    {answers[s.key] !== undefined ? answerLabel(s.key, answers[s.key] as Answer) : "—"}
                  </span>
                </div>
              ))}
            </div>
            <button
              type="button"
              onClick={submit}
              disabled={busy}
              className="btn-primary w-full py-3.5 text-base disabled:cursor-wait"
            >
              {busy ? t("voice.submitting") : t("voice.submit")}
            </button>
            <button type="button" onClick={restart} className="w-full text-center text-sm font-medium text-slate-500">
              ← {t("voice.restart")}
            </button>
          </div>
        ) : null}

        {phase === "error" ? (
          <div className="card p-6 text-center">
            <p className="text-lg font-bold text-red-700">{t("voice.error")}</p>
            <p className="mt-2 text-sm text-slate-600">{error}</p>
            <button type="button" onClick={restart} className="btn-primary mt-5 w-full">
              {t("voice.restart")}
            </button>
          </div>
        ) : null}

        {phase === "done" && result ? (
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900">{t("voice.results")}</h2>
            {result.violations.length === 0 ? (
              <div className="rounded-card border border-brand-200 bg-brand-50 p-6 text-center">
                <p className="text-base font-medium text-brand-800">{t("dash.noViolations")}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {result.violations.map((v: Violation, i) => (
                  <ViolationCard key={`${v.rule_id}-${i}`} violation={v} />
                ))}
              </div>
            )}
            <button type="button" onClick={restart} className="btn-secondary w-full">
              {t("voice.restart")}
            </button>
            <p className="text-center text-[11px] text-slate-400">{t("ai.disclaimer")}</p>
          </div>
        ) : null}
      </main>
    </div>
  );
}
