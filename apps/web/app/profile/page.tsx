"use client";

// Profile: edit your identity details, manage your employers (edit / remove),
// switch language and log out.

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import RequireAuth from "@/components/RequireAuth";
import ShareCodeCard from "@/components/ShareCodeCard";
import { ChoiceGroup, SelectField, TextField } from "@/components/controls";
import { deleteEmployer, listEmployers, sharmsansarExport } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { EDUCATION_LEVELS, ETHNICITIES, GENDERS } from "@/lib/constants";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import type { Employer } from "@/lib/types";

export default function ProfilePage() {
  const { user, logout, updateUser } = useAuth();
  const { t, lang, setLang } = useLanguage();
  const router = useRouter();

  const [employers, setEmployers] = useState<Employer[]>([]);
  const [gender, setGender] = useState(user?.gender ?? "");
  const [dob, setDob] = useState(user?.date_of_birth ?? "");
  const [ethnicity, setEthnicity] = useState(user?.ethnicity ?? "");
  const [education, setEducation] = useState(user?.education_level ?? "");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportNote, setExportNote] = useState<string | null>(null);

  useEffect(() => {
    listEmployers()
      .then(setEmployers)
      .catch(() => setEmployers([]));
  }, []);

  useEffect(() => {
    setGender(user?.gender ?? "");
    setDob(user?.date_of_birth ?? "");
    setEthnicity(user?.ethnicity ?? "");
    setEducation(user?.education_level ?? "");
  }, [user]);

  const saveIdentity = async () => {
    setBusy(true);
    setSaved(false);
    try {
      await updateUser({
        gender: gender || null,
        date_of_birth: dob || null,
        ethnicity: ethnicity || null,
        education_level: education || null,
      });
      setSaved(true);
    } catch {
      setSaved(false);
    } finally {
      setBusy(false);
    }
  };

  const removeEmployer = async (e: Employer) => {
    if (!window.confirm(t("profile.confirmDelete"))) return;
    try {
      await deleteEmployer(e.id);
      setEmployers((list) => list.filter((x) => x.id !== e.id));
    } catch {
      // keep the list unchanged
    }
  };

  const doLogout = async () => {
    await logout();
    router.replace("/");
  };

  // Sharmsansar export stub: downloads the worker's data as JSON. The real
  // mapping to Sharmsansar's API is future work (backend returns a placeholder).
  const doExport = async () => {
    setExporting(true);
    setExportNote(null);
    try {
      const data = await sharmsansarExport();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `shramiksathi-export-${user?.username ?? "me"}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExportNote(t("profile.exportDone"));
    } catch (e) {
      setExportNote(e instanceof Error ? e.message : t("profile.exportFailed"));
    } finally {
      setExporting(false);
    }
  };

  return (
    <RequireAuth>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t("profile.title")}</h1>
        </div>

        {/* Identity */}
        <section className="card p-4">
          <h2 className="mb-3 font-semibold text-slate-800">{t("profile.self")}</h2>
          <div className="space-y-3">
            <div>
              <span className="mb-1.5 block text-sm font-medium text-slate-800">
                {t("auth.username")}
              </span>
              <p className="text-sm text-slate-600">{user?.username}</p>
            </div>
            <ChoiceGroup label={t("idf.gender")} value={gender} onChange={setGender} options={GENDERS} />
            <TextField label={t("idf.dob")} type="date" value={dob} onChange={setDob} />
            <SelectField
              label={t("idf.ethnicity")}
              value={ethnicity}
              onChange={setEthnicity}
              options={ETHNICITIES.map((name) => ({ value: name, en: name, ne: name }))}
            />
            <SelectField
              label={t("idf.education")}
              value={education}
              onChange={setEducation}
              options={EDUCATION_LEVELS}
            />
            <button
              type="button"
              onClick={saveIdentity}
              disabled={busy}
              className="btn-primary w-full"
            >
              {busy ? t("form.saving") : t("profile.save")}
            </button>
            {saved ? (
              <p className="rounded-lg bg-brand-100 px-3 py-2 text-sm text-brand-800">
                {t("profile.saved")}
              </p>
            ) : null}
          </div>
        </section>

        {/* Share code (worker accounts only) */}
        {user?.role !== "employer" ? <ShareCodeCard /> : null}

        {/* Employers */}
        <section className="card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-slate-800">{t("profile.employers")}</h2>
            <Link href="/add-employer" className="text-sm font-medium text-brand-700">
              + {t("home.addEmployer")}
            </Link>
          </div>
          {employers.length === 0 ? (
            <p className="text-sm text-slate-500">{t("profile.noEmployers")}</p>
          ) : (
            <div className="space-y-2">
              {employers.map((e) => (
                <div
                  key={e.id}
                  className="flex items-center justify-between gap-2 rounded-lg border border-slate-200 px-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">
                      {e.employer_name ?? "—"}
                    </p>
                    <p className="truncate text-xs text-slate-500">
                      {[e.work_district, e.industry].filter(Boolean).join(" · ")}
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    <Link
                      href={`/add-employer/${e.id}`}
                      className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs font-medium text-slate-700"
                    >
                      {t("profile.edit")}
                    </Link>
                    <button
                      type="button"
                      onClick={() => removeEmployer(e)}
                      className="rounded-lg border border-rose-300 px-2.5 py-1.5 text-xs font-medium text-rose-700"
                    >
                      {t("profile.delete")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Data export (S harmsansar placeholder) */}
        <section className="card p-4">
          <h2 className="mb-1 font-semibold text-slate-800">{t("profile.export")}</h2>
          <p className="mb-3 text-xs text-slate-500">{t("profile.exportDesc")}</p>
          <button
            type="button"
            onClick={doExport}
            disabled={exporting}
            className="btn-secondary w-full"
          >
            {exporting ? t("profile.exporting") : t("profile.exportBtn")}
          </button>
          {exportNote ? (
            <p className="mt-3 rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600">
              {exportNote}
            </p>
          ) : null}
        </section>

        {/* Language + logout */}
        <section className="card p-4">
          <h2 className="mb-3 font-semibold text-slate-800">{t("profile.language")}</h2>          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setLang("en")}
              className={`rounded-full border px-4 py-2 text-sm font-medium ${
                lang === "en"
                  ? "border-brand-600 bg-brand-50 text-brand-800"
                  : "border-slate-300 text-slate-600"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLang("ne")}
              className={`rounded-full border px-4 py-2 text-sm font-medium ${
                lang === "ne"
                  ? "border-brand-600 bg-brand-50 text-brand-800"
                  : "border-slate-300 text-slate-600"
              }`}
            >
              नेपाली
            </button>
          </div>

          <button
            type="button"
            onClick={doLogout}
            className="mt-4 w-full rounded-xl border border-rose-300 px-4 py-3 text-sm font-semibold text-rose-700 active:bg-rose-50"
          >
            {t("profile.logout")}
          </button>
        </section>
      </div>
    </RequireAuth>
  );
}
