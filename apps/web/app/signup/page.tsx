"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import {
  ChoiceGroup,
  SelectField,
  TextField,
} from "@/components/controls";
import { useAuth } from "@/lib/auth";
import { EDUCATION_LEVELS, ETHNICITIES, GENDERS } from "@/lib/constants";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function SignupPage() {
  const { t } = useLanguage();
  const { register } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<0 | 1>(0);
  const [role, setRole] = useState("worker");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Identity & demographics (signup only).
  const [gender, setGender] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [ethnicity, setEthnicity] = useState("");
  const [education, setEducation] = useState("");

  const credentialsOk = () => {
    if (username.trim().length < 3) {
      setError(t("auth.err.usernameShort"));
      return false;
    }
    if (password.length < 6) {
      setError(t("auth.err.passwordShort"));
      return false;
    }
    if (password !== confirm) {
      setError(t("auth.err.match"));
      return false;
    }
    return true;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (step === 0) {
      if (credentialsOk()) setStep(1);
      return;
    }
    setBusy(true);
    try {
      const u = await register({
        username: username.trim(),
        password,
        role,
        gender: gender || null,
        date_of_birth: dateOfBirth || null,
        ethnicity: ethnicity || null,
        education_level: education || null,
      });
      router.push(u.role === "employer" ? "/employer" : "/home");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.err.server"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-dvh bg-[#F8FAFC] px-6 py-10">
      <div className="mx-auto w-full max-w-sm">
        <h1 className="text-2xl font-bold text-slate-900">{t("auth.signupTitle")}</h1>
        <p className="mt-1 text-sm text-slate-500">{t("auth.signupSubtitle")}</p>

        <form onSubmit={submit} className="mt-6 space-y-4">
          <div className="card space-y-4 p-6">
            {step === 0 ? (
              <>
                <ChoiceGroup
                  label={t("auth.role")}
                  value={role}
                  onChange={setRole}
                  options={[
                    { value: "worker", en: t("auth.roleWorker"), ne: t("auth.roleWorker") },
                    { value: "employer", en: t("auth.roleEmployer"), ne: t("auth.roleEmployer") },
                  ]}
                />
                <TextField label={t("auth.username")} value={username} onChange={setUsername} placeholder={t("auth.usernameHint")} />
                <TextField
                  label={t("auth.password")}
                  value={password}
                  onChange={setPassword}
                  type="password"
                  placeholder={t("auth.passwordHint")}
                />
                <TextField label={t("auth.confirmPassword")} value={confirm} onChange={setConfirm} type="password" />
              </>
            ) : (
              <>
                <h2 className="text-lg font-semibold text-slate-900">{t("idf.title")}</h2>
                <p className="text-sm text-slate-500">{t("idf.subtitle")}</p>

                <ChoiceGroup label={t("idf.gender")} value={gender} onChange={setGender} options={GENDERS} />

                <TextField label={t("idf.dob")} value={dateOfBirth} onChange={setDateOfBirth} type="date" />

                <SelectField
                  label={t("idf.ethnicity")}
                  value={ethnicity}
                  onChange={setEthnicity}
                  options={ETHNICITIES.map((name) => ({ value: name, en: name, ne: name }))}
                  emptyLabel={t("option.choose")}
                />
                <p className="-mt-2 text-xs text-slate-400">{t("idf.ethnicityHint")}</p>

                <SelectField label={t("idf.education")} value={education} onChange={setEducation} options={EDUCATION_LEVELS} />
              </>
            )}
          </div>

          {error ? (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
          ) : null}

          {step === 0 ? (
            <button
              type="submit"
              className="btn-primary w-full"
            >
              {t("form.next")}
            </button>
          ) : (
            <div className="space-y-2">
              <button
                type="submit"
                disabled={busy}
                className="btn-primary w-full"
              >
                {busy ? t("auth.creating") : t("idf.next")}
              </button>
                <button
                  type="button"
                  onClick={() => {
                    setBusy(true);
                    register({
                      username: username.trim(),
                      password,
                      role,
                      gender: null,
                      date_of_birth: null,
                      ethnicity: null,
                      education_level: null,
                    })
                      .then((u) => router.push(u.role === "employer" ? "/employer" : "/home"))
                      .catch((err) => setError(err instanceof Error ? err.message : t("auth.err.server")))
                      .finally(() => setBusy(false));
                  }}
                  className="btn-secondary w-full"
                >
                  {t("idf.skip")}
                </button>
              <button
                type="button"
                onClick={() => setStep(0)}
                className="w-full text-center text-sm text-slate-500 underline"
              >
                {t("form.back")}
              </button>
            </div>
          )}
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          {t("auth.haveAccount")}{" "}
          <Link href="/login" className="font-semibold text-brand-600 underline">
            {t("auth.loginBtn")}
          </Link>
        </p>
      </div>
    </div>
  );
}
