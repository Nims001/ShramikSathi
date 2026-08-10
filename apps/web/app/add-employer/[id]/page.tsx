"use client";

// Edit an existing employer — loads the record then shows the same form
// pre-filled, and deletes it from the profile flow.

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import EmployerForm from "@/components/EmployerForm";
import RequireAuth from "@/components/RequireAuth";
import { listEmployers } from "@/lib/api";
import type { Employer } from "@/lib/types";

export default function EditEmployerPage() {
  const params = useParams<{ id: string }>();
  const [employer, setEmployer] = useState<Employer | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    listEmployers()
      .then((list) => {
        if (!active) return;
        setEmployer(list.find((e) => e.id === params.id) ?? null);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  if (!employer) {
    return <p className="text-sm text-slate-500">Not found</p>;
  }

  return (
    <RequireAuth>
      <EmployerForm existing={employer} />
    </RequireAuth>
  );
}
