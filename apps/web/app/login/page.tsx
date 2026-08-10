"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { useAuth } from "@/lib/auth";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import Logo from "@/components/Logo";

export default function LoginPage() {
  const { t } = useLanguage();
  const { login } = useAuth();
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !password) {
      setError(t("auth.err.server"));
      return;
    }
    setBusy(true);
    try {
      const u = await login({ username: username.trim(), password });
      router.push(u.role === "employer" ? "/employer" : "/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.err.server"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-dvh flex-col justify-center bg-[#F8FAFC] px-6">
      <div className="mx-auto w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="icon-chip mx-auto h-14 w-14 rounded-2xl bg-brand-50">
            <Logo className="h-full w-full" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-slate-900">{t("auth.loginTitle")}</h1>
        </div>

        <div className="card p-6">
          <form onSubmit={submit} className="space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                {t("auth.username")}
              </span>
              <input
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t("auth.usernameHint")}
                autoComplete="username"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium text-slate-700">
                {t("auth.password")}
              </span>
              <input
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={t("auth.passwordHint")}
                autoComplete="current-password"
              />
            </label>

            {error ? (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
            ) : null}

            <button
              type="submit"
              disabled={busy}
              className="btn-primary w-full"
            >
              {busy ? t("auth.loggingIn") : t("auth.loginBtn")}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-slate-500">
          {t("auth.noAccount")}{" "}
          <Link href="/signup" className="font-semibold text-brand-600 underline">
            {t("onboard.signup")}
          </Link>
        </p>
        <p className="mt-2 text-center">
          <Link href="/" className="text-xs text-slate-400 underline">
            {t("auth.or")} ← {t("onboard.chooseLang")}
          </Link>
        </p>
      </div>
    </div>
  );
}
