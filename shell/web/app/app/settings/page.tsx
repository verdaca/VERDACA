/**
 * Settings overview — arch §1.1.
 */

import Link from "next/link";

export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Settings</h1>
      <div className="mt-8 grid max-w-md gap-4">
        <Link
          href="/app/settings/billing"
          className="block rounded-lg border p-4 hover:bg-gray-50"
        >
          <h3 className="font-medium">Billing</h3>
          <p className="text-sm text-muted">Manage payment methods and invoices.</p>
        </Link>
        <Link
          href="/app/settings/team"
          className="block rounded-lg border p-4 hover:bg-gray-50"
        >
          <h3 className="font-medium">Team</h3>
          <p className="text-sm text-muted">Invite members and manage roles.</p>
        </Link>
      </div>
    </div>
  );
}
