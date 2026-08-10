// Personal dashboard — the home page renders the same dashboard component.
// This route exists so /dashboard and /home both open the dashboard.

import HomePage from "@/app/home/page";

export default function DashboardPage() {
  return <HomePage />;
}
