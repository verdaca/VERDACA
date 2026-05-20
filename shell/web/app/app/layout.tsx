/**
 * Authenticated app layout — arch §1.2.
 *
 * All /app routes are wrapped in ClerkProtect + sidebar nav.
 */

import Link from "next/link";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <nav className="w-56 border-r bg-white px-4 py-6">
        <div className="mb-8 text-lg font-bold text-primary">Praxis</div>
        <ul className="space-y-2">
          <NavItem href="/app" label="Mission Control" />
          <NavItem href="/app/sessions/new" label="New Analysis" />
          <NavItem href="/app/history" label="History" />
          <NavItem href="/app/settings" label="Settings" />
        </ul>
      </nav>

      {/* Main content */}
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}

function NavItem({ href, label }: { href: string; label: string }) {
  return (
    <li>
      <Link
        href={href}
        className="block rounded-md px-3 py-2 text-sm text-muted hover:bg-gray-50 hover:text-foreground"
      >
        {label}
      </Link>
    </li>
  );
}
