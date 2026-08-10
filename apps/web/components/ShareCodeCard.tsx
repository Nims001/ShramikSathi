"use client";

// Worker "share code" card: generates/rotates the code the worker can give to
// their employer so the employer's portal can view this worker's logs. The
// code is stored server-side only as a hash; the plaintext is shown once here.

import { useState } from "react";

import { generateShareCode } from "@/lib/api";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function ShareCodeCard() {
  const { t } = useLanguage();
  const [code, setCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    setBusy(true);
    setError(null);
    setCopied(false);
    try {
      const res = await generateShareCode();
      setCode(res.code);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.err.server"));
    } finally {
      setBusy(false);
    }
  };

  const copy = async () => {
    if (!code) return;
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard unavailable — user can still copy manually
    }
  };

  return (
    <section className="card p-4">
      <h2 className="font-semibold text-slate-800">{t("employer.codeTitle")}</h2>
      <p className="mt-1 text-sm text-slate-500">{t("employer.codeSubtitle")}</p>

      {code ? (
        <div className="mt-4">
          <div className="flex items-center justify-between gap-2 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3">
            <span className="text-lg font-bold tracking-widest text-brand-800">{code}</span>
            <button
              type="button"
              onClick={copy}
              className="shrink-0 rounded-lg bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white"
            >
              {copied ? t("employer.copied") : t("employer.copy")}
            </button>
          </div>
          <button
            type="button"
            onClick={generate}
            disabled={busy}
            className="mt-3 w-full rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700"
          >
            {t("employer.regenerate")}
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={generate}
          disabled={busy}
          className="btn-primary mt-4 w-full"
        >
          {busy ? "…" : t("employer.generate")}
        </button>
      )}

      {error ? (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}
    </section>
  );
}
