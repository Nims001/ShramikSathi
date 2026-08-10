"use client";

// Guards employer-only pages: shows a brief spinner while auth loads, then
// redirects to the onboarding page if the user is not an employer.

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

export default function RequireEmployer({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || user.role !== "employer")) router.replace("/");
  }, [loading, user, router]);

  if (loading || !user || user.role !== "employer") {
    return (
      <div className="flex h-dvh items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  return <>{children}</>;
}
