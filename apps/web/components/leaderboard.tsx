import type { DisplayRankingResponse } from "../lib/api";
import { RankingRow } from "./ranking-row";

const LIMITS = [10, 20, 30, 50] as const;

export function Leaderboard({
  ranking,
  limit,
  provisional = false,
}: {
  ranking: DisplayRankingResponse;
  limit: number;
  provisional?: boolean;
}) {
  const emptyCopy = provisional
    ? "Discovery and evidence review are still in progress. No provisional rows are available yet."
    : "No official ranking has been published yet.";

  return (
    <section className="panel">
      <div className="leaderboard-head">
        <div>
          <span className="badge">{ranking.ranking_type}</span>
          <p className="subtle">{ranking.quarter} · {ranking.algorithm_name} {ranking.algorithm_version}</p>
        </div>
        <div className="limit-tabs" aria-label="Leaderboard size">
          {LIMITS.map(value => (
            <a key={value} className={`limit-tab ${limit === value ? "active" : ""}`} href={`?limit=${value}`}>
              Top {value}
            </a>
          ))}
        </div>
      </div>
      {ranking.results.length
        ? ranking.results.map(result => (
            <RankingRow
              key={result.entity_id}
              result={result}
              shareEnabled={!provisional}
            />
          ))
        : <div className="empty">{emptyCopy}</div>}
    </section>
  );
}
