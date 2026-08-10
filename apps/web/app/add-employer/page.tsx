"use client";

// Add an employer — renders the full intake form (11 sections, bilingual).

import EmployerForm from "@/components/EmployerForm";
import RequireAuth from "@/components/RequireAuth";
import { useLanguage } from "@/lib/i18n/LanguageContext";

export default function AddEmployerPage() {
  const { t } = useLanguage();

  return (
    <RequireAuth>
      <div>
        <EmployerForm />
      </div>
    </RequireAuth>
  );
}
