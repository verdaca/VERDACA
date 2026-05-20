/**
 * Mission Control dashboard — arch §1.1.
 *
 * Shows recent sessions, usage summary, and quick-start CTA.
 */

import Link from "next/link";

export default function MissionControlPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Mission Control</h1>
      <p className="mt-2 text-muted">
        Your strategic analysis dashboard.
      </p>

      <div className="mt-8">
        <Link
          href="/app/sessions/new"
          className="inline-flex items-center rounded-lg bg-primary px-6 py-3 text-white hover:bg-primary/90"
        >
          Start New Analysis
        </Link>
      </div>
    </div>
  );
}
