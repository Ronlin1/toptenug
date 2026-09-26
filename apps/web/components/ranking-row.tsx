import type { RankingResult } from "../lib/api";
import { ShareRanking } from "./share-ranking";

export function RankingRow({ result }: { result: RankingResult }) {
  const movement = result.movement;
  return (
    <div className="ranking-row">
      <div className="rank">#{result.rank}</div>
      <div><a className="person-name" href={`/people/${result.entity_slug}`}>{result.name}</a><div className="person-meta">{result.provenance.source_count} public evidence signals</div><ShareRanking resultId={result.ranking_result_id} entityName={result.name} /></div>
      <div className="score">{result.score.toFixed(1)}</div>
      <div className={`movement hide-mobile ${movement && movement > 0 ? "up" : movement && movement < 0 ? "down" : ""}`}>{movement == null ? "New" : movement > 0 ? `↑ ${movement}` : movement < 0 ? `↓ ${Math.abs(movement)}` : "—"}</div>
      <div className="hide-mobile"><span className="badge">{Math.round(result.confidence * 100)}% confidence</span></div>
    </div>
  );
}
