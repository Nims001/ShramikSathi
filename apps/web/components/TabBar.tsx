"use client";

// Bottom tab bar — the primary navigation for the app. Stays centered with
// the phone-width shell on desktop and floats above the safe area on mobile.

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useLanguage } from "@/lib/i18n/LanguageContext";

interface Tab {
  href: string;
  key: string;
  icon: React.ReactNode;
}

function Icon({ children }: { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-6 w-6"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

const tabs: Tab[] = [
  {
    href: "/home",
    key: "nav.dashboard",
    icon: (
      <Icon>
        <rect x="3" y="3" width="7" height="9" rx="1" />
        <rect x="14" y="3" width="7" height="5" rx="1" />
        <rect x="14" y="12" width="7" height="9" rx="1" />
        <rect x="3" y="16" width="7" height="5" rx="1" />
      </Icon>
    ),
  },
  {
    href: "/logs",
    key: "nav.logs",
    icon: (
      <Icon>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </Icon>
    ),
  },
  {
    href: "/analysis",
    key: "nav.analysis",
    icon: (
      <Icon>
        <circle cx="12" cy="12" r="9" />
        <path d="m9 11 3 3 4-5" />
      </Icon>
    ),
  },
  {
    href: "/profile",
    key: "nav.profile",
    icon: (
      <Icon>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
      </Icon>
    ),
  },
];

export default function TabBar() {
  const { t } = useLanguage();
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/home"
      ? pathname === "/home" || pathname === "/" || pathname === "/dashboard"
      : pathname.startsWith(href);

  return (
    <nav
      className="fixed bottom-0 left-1/2 z-20 w-full max-w-md -translate-x-1/2 border-t border-slate-200 bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur"
      aria-label="Primary"
    >
      <div className="grid grid-cols-4">
        {tabs.map((tab) => {
          const active = isActive(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              aria-current={active ? "page" : undefined}
              className={`flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${
                active ? "text-brand-700" : "text-slate-500"
              }`}
            >
              <span
                className={`flex h-7 w-14 items-center justify-center rounded-full transition-colors ${
                  active ? "bg-brand-50 text-brand-600" : "text-slate-400"
                }`}
              >
                {tab.icon}
              </span>
              <span>{t(tab.key)}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
