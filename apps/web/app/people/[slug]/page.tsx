import { RankHistoryChart } from "../../../components/rank-history-chart";
import { ScoreBreakdown } from "../../../components/score-breakdown";
import { safeApiGet, type EntityHistoryResponse, type EntityResponse } from "../../../lib/api";

export default async function PersonPage({ params }: { params: Promise<{slug:string}> }) {
  const { slug } = await params;
  const entity = await safeApiGet<EntityResponse | null>(`/v1/entities/${slug}`, null);
  const history = await safeApiGet<EntityHistoryResponse>(`/v1/entities/${slug}/history`, {slug,history:[]});
  if (!entity) return <main><div className="empty">This public profile is not available yet.</div></main>;
  const current = entity.current_rankings[0];
  return <main><div className="breadcrumb"><a href="/">TopTenUG</a> / People / {entity.name}</div>
    <section className="hero"><span className="eyebrow">Evidence-backed public profile</span><h1 className="page-title">{entity.name}</h1>{current && <p className="hero-copy">#{current.rank} in {current.ranking} · {current.quarter} · score {current.score.toFixed(1)} · {Math.round(current.confidence*100)}% evidence confidence</p>}</section>
    <div className="profile-grid"><RankHistoryChart points={history.history}/><ScoreBreakdown factors={current?.factor_breakdown ?? {}} /></div>
    {current?.evidence_urls?.length ? <section><div className="section-head"><h2>Public evidence</h2></div><ul className="evidence-list">{current.evidence_urls.map(url => <li key={url}><a href={url} target="_blank" rel="noreferrer">{url}</a></li>)}</ul></section> : null}
  </main>;
}
