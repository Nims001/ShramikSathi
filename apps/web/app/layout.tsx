import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

import AppShell from "@/components/AppShell";
import { AuthProvider } from "@/lib/auth";
import { LanguageProvider } from "@/lib/i18n/LanguageContext";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ShramikSathi — AI Labour Rights Assistant",
  description:
    "Know your rights, record your work, and protect your pay — in English or Nepali.",
};

export const viewport: Viewport = {
  themeColor: "#1F75E6",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <LanguageProvider>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
