import { safeApiGet, type MethodologyResponse } from "../../../lib/api";

export default async function MethodologyPage({ params }: { params: Promise<{slug:string}> }) {
  const { slug } = await params;
  const data = await safeApiGet<MethodologyResponse | null>(`/v1/methodology/${slug}`, null);
  if (!data) return <main><div className="empty">Methodology not found.</div></main>;
  return <main><div className="breadcrumb"><a href="/">TopTenUG</a> / Methodology</div>
    <section className="hero"><span className="eyebrow">Transparent by design</span><h1 className="page-title">{data.name} {data.version}</h1><p className="hero-copy">Official TopTenUG scores are calculated by versioned deterministic algorithms. Google/Gemini helps discover and structure evidence; it does not choose the winners.</p></section>
    <section className="panel" style={{padding:24}}><div className="grid metrics"><div className="metric"><div className="metric-label">Type</div><div className="metric-value" style={{fontSize:22}}>{data.ranking_type}</div></div><div className="metric"><div className="metric-label">Missing data</div><div className="metric-value" style={{fontSize:18}}>{data.missing_data_policy}</div></div><div className="metric"><div className="metric-label">Min coverage</div><div className="metric-value" style={{fontSize:22}}>{Math.round(data.minimum_factor_coverage*100)}%</div></div><div className="metric"><div className="metric-label">Tie breaker</div><div className="metric-value" style={{fontSize:16}}>{data.tie_breaker}</div></div></div>
    <table className="method-table"><thead><tr><th>Factor</th><th>Weight</th><th>Metric</th><th>Normalization</th></tr></thead><tbody>{data.factors.map(f => <tr key={f.name}><td>{f.name.replaceAll("_"," ")}</td><td>{Math.round(f.weight*100)}%</td><td><code>{f.metric}</code></td><td>{f.normalization}</td></tr>)}</tbody></table>
    <h2>Known limitations</h2><ul className="evidence-list">{data.limitations.map(item => <li key={item}>{item}</li>)}</ul></section>
  </main>;
}
