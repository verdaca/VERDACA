/**
 * Landing page — arch §1.1, Sophia §E messaging.
 *
 * Hero + How-It-Works + Pricing + CTA + Public Dashboard link.
 * Copy sourced from shell/messaging-and-onboarding.md (Sophia 7.0.2).
 */

import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-6 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-primary sm:text-5xl">
          Strategic analysis with genuine dissent.
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-muted">
          In minutes, not weeks. Multiple AI analysts deliberate on your
          strategic question, surface trade-offs, challenge assumptions, and
          deliver a position you can hold.
        </p>
        <Link
          href="/signup"
          className="mt-8 rounded-lg bg-primary px-8 py-3 text-lg font-medium text-white hover:bg-primary/90"
        >
          Run your first analysis free
        </Link>
      </section>

      {/* How It Works */}
      <section className="bg-white px-6 py-16">
        <h2 className="text-center text-2xl font-bold text-secondary">
          How It Works
        </h2>
        <div className="mx-auto mt-10 grid max-w-4xl gap-8 sm:grid-cols-3">
          {[
            {
              step: "1",
              title: "Ask your question",
              desc: "Paste the strategic question your team is debating.",
            },
            {
              step: "2",
              title: "Analysts deliberate",
              desc: "Multiple AI analysts research, debate, and red-team each other's positions.",
            },
            {
              step: "3",
              title: "Get a defensible position",
              desc: "Receive a structured analysis with trade-offs, dissent, scenarios, and scope limits.",
            },
          ].map((item) => (
            <div key={item.step} className="text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-accent text-white font-bold">
                {item.step}
              </div>
              <h3 className="mt-4 font-semibold text-foreground">
                {item.title}
              </h3>
              <p className="mt-2 text-sm text-muted">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="px-6 py-16">
        <h2 className="text-center text-2xl font-bold text-secondary">
          Pricing
        </h2>
        <p className="mt-2 text-center text-sm text-muted">
          Per-session pricing. No subscription required.
        </p>
        <div className="mx-auto mt-10 grid max-w-2xl gap-6 sm:grid-cols-2">
          <PricingCard
            tier="Quick"
            price="$29"
            duration="~4 minutes"
            features={[
              "2-3 analyst cycles",
              "Core trade-off analysis",
              "Key dissent points",
            ]}
          />
          <PricingCard
            tier="Deep"
            price="$149"
            duration="~12 minutes"
            features={[
              "Full 3-cycle deliberation",
              "Comprehensive trade-offs",
              "Red-team dissent section",
              "Scenario planning",
              "Scope limits analysis",
            ]}
            highlighted
          />
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t px-6 py-8 text-center text-sm text-muted">
        <Link href="/dashboard" className="underline hover:text-foreground">
          Built With Praxis
        </Link>
      </footer>
    </main>
  );
}

function PricingCard({
  tier,
  price,
  duration,
  features,
  highlighted = false,
}: {
  tier: string;
  price: string;
  duration: string;
  features: string[];
  highlighted?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border p-6 ${
        highlighted
          ? "border-accent bg-accent/5 shadow-lg"
          : "border-gray-200"
      }`}
    >
      <h3 className="text-lg font-semibold">{tier}</h3>
      <p className="mt-2 font-mono text-3xl font-bold text-primary">{price}</p>
      <p className="mt-1 text-sm text-muted">{duration}</p>
      <ul className="mt-4 space-y-2">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm">
            <span className="text-success">&#10003;</span>
            {f}
          </li>
        ))}
      </ul>
    </div>
  );
}
