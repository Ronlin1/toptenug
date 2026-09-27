import type { RankingResult } from "../lib/api";
import { ShareRanking } from "./share-ranking";

export function RankingRow({
  result,
  shareEnabled = true,
}: {
  result: RankingResult;
  shareEnabled?: boolean;
}) {
  const movement = result.movement;
  const sourceCount = result.provenance?.source_count;
  return (
    <div className="ranking-row">
      <div className="rank">#{result.rank}</div>
      <div>
        <a className="person-name" href={`/people/${result.entity_slug}`}>{result.name}</a>
        <div className="person-meta">
          {sourceCount == null ? "Evidence reviewed" : `${sourceCount} public evidence signals`}
        </div>
        {shareEnabled ? <ShareRanking resultId={result.ranking_result_id} entityName={result.name} /> : null}
      </div>
      <div className="score">{result.score.toFixed(1)}</div>
      <div className={`movement hide-mobile ${movement && movement > 0 ? "up" : movement && movement < 0 ? "down" : ""}`}>
        {movement == null ? "New" : movement > 0 ? `↑ ${movement}` : movement < 0 ? `↓ ${Math.abs(movement)}` : "—"}
      </div>
      <div className="hide-mobile"><span className="badge">{Math.round(result.confidence * 100)}% confidence</span></div>
    </div>
  );
}
