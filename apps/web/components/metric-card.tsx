export function MetricCard({ value, label }: { value: string | number; label: string }) {
  return <div className="metric"><div className="metric-value">{value}</div><div className="metric-label">{label}</div></div>;
}
