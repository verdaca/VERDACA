/**
 * Shareable link view — arch §1.1, ADR-10.
 *
 * Auth-gated per ADR-10 (workspace auth required).
 */

interface Props {
  params: Promise<{ id: string }>;
}

export default async function SharePage({ params }: Props) {
  const { id } = await params;

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-bold text-foreground">
        Shared Analysis
      </h1>
      <p className="mt-2 text-muted">Session {id}</p>
      <div className="mt-8 rounded-lg border p-6">
        <p className="text-muted">
          Shared analysis content will appear here.
        </p>
      </div>
    </div>
  );
}
