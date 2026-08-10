"use client";

// App chrome: decides whether to show the header / footer / tab bar.
// Onboarding, login and signup are full-screen pages without the app chrome.

import { usePathname } from "next/navigation";

import Header from "@/components/Header";
import TabBar from "@/components/TabBar";
import { useAuth } from "@/lib/auth";

const BARE_PATHS = new Set(["/", "/login", "/signup", "/voice"]);

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, loading } = useAuth();

  const bare = BARE_PATHS.has(pathname) || !user || pathname.startsWith("/employer");

  if (bare || loading) {
    return <>{children}</>;
  }

  return (
    <>
      <div className="mx-auto flex min-h-dvh w-full max-w-md flex-col bg-white shadow-soft-lg sm:border-x sm:border-slate-200">
        <Header />
        <main className="flex-1 px-4 pb-24 pt-4">{children}</main>
      </div>
      <TabBar />
    </>
  );
}
