/**
 * Public "Built With Praxis" dashboard — arch §8, ADR-10.
 *
 * Shows aggregate metrics only. No customer data exposed.
 */

import { API_BASE } from "@/lib/utils";

interface PublicStats {
  total_sessions: number;
  avg_cost_usd: number;
  avg_duration_seconds: number;
  sessions_today: number;
  insufficient_data: boolean;
}

async function getStats(): Promise<PublicStats> {
  const res = await fetch(`${API_BASE}/api/public/stats`, {
    next: { revalidate: 60 },
  });
  return res.json();
}

export default async function PublicDashboard() {
  const stats = await getStats();

  return (
    <main className="min-h-screen px-6 py-16">
      <h1 className="text-center text-3xl font-bold text-primary">
        BUILT WITH PRAXIS
      </h1>

      {stats.insufficient_data ? (
        <p className="mt-8 text-center text-muted">
          Not enough data yet. Check back soon.
        </p>
      ) : (
        <>
          <div className="mx-auto mt-10 grid max-w-3xl gap-6 sm:grid-cols-4">
            <StatCard label="Sessions" value={String(stats.total_sessions)} />
            <StatCard
              label="Avg Cost"
              value={`$${stats.avg_cost_usd.toFixed(2)}`}
            />
            <StatCard
              label="Avg Time"
              value={`${Math.round(stats.avg_duration_seconds / 60)} min`}
            />
            <StatCard label="Today" value={String(stats.sessions_today)} />
          </div>
          <blockquote className="mx-auto mt-10 max-w-2xl text-center text-muted italic">
            We built Praxis using Praxis. Every architectural decision in the
            7-stage build pipeline was run through the same analytical process
            you can buy today.
          </blockquote>
        </>
      )}
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-4 text-center">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 font-mono text-2xl font-bold text-primary">{value}</p>
    </div>
  );
}
