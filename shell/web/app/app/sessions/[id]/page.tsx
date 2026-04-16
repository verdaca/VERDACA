/**
 * Session detail page — arch §1.1.
 *
 * Shows live view during run, results after completion.
 * Includes SessionLiveView (SSE) and SessionResultView.
 */

interface Props {
  params: Promise<{ id: string }>;
}

export default async function SessionDetailPage({ params }: Props) {
  const { id } = await params;

  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">
        Session {id.slice(0, 8)}...
      </h1>

      {/* Live View (shown while running) */}
      <div className="mt-8 rounded-lg border p-6">
        <p className="text-muted">
          Session status and results will appear here.
        </p>
        <div className="mt-4">
          <div className="h-2 w-full rounded-full bg-gray-200">
            <div className="h-2 w-1/3 rounded-full bg-accent" />
          </div>
          <div className="mt-2 flex justify-between text-xs text-muted">
            <span>Cycle 1 of 3</span>
            <span>Est. remaining: ~8 min</span>
          </div>
        </div>
      </div>

      {/* Result View (shown after completion) */}
      <div className="mt-8">
        <h2 className="text-lg font-semibold">Results</h2>
        <p className="mt-2 text-sm text-muted">
          Analysis results will be rendered here in Markdown/HTML format.
        </p>
      </div>
    </div>
  );
}
