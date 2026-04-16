/**
 * Session history list — arch §1.1.
 */

export default function HistoryPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">Analysis History</h1>
      <p className="mt-2 text-muted">Your past strategic analyses.</p>

      <div className="mt-8">
        <table className="w-full text-left text-sm">
          <thead className="border-b text-xs uppercase text-muted">
            <tr>
              <th className="px-4 py-3">Question</th>
              <th className="px-4 py-3">Depth</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Cost</th>
              <th className="px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="px-4 py-4 text-muted" colSpan={5}>
                No sessions yet. Start your first analysis.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
