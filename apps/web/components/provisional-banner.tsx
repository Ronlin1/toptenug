export function ProvisionalBanner({
  reviewedPoolCount,
  cutoffAt,
}: {
  reviewedPoolCount: number;
  cutoffAt: string | null;
}) {
  const cutoffLabel = cutoffAt
    ? new Intl.DateTimeFormat("en", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "Africa/Kampala",
      }).format(new Date(cutoffAt))
    : "the latest reviewed data";

  return (
    <aside className="panel provisional-banner" aria-label="Provisional ranking notice">
      <span className="badge">Live preview</span>
      <h2>Provisional — not an official quarterly ranking</h2>
      <p>
        Based on {reviewedPoolCount} reviewed, eligible developers. Discovery and evidence review are still
        in progress, so positions may change before the official quarter closes.
      </p>
      <p className="subtle">Preview cutoff: {cutoffLabel} · Africa/Kampala</p>
    </aside>
  );
}
