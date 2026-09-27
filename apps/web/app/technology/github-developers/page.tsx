import { Leaderboard } from "../../../components/leaderboard";
import { ProvisionalBanner } from "../../../components/provisional-banner";
import {
  safeApiGet,
  type PreviewRankingResponse,
  type RankingResponse,
} from "../../../lib/api";

const allowed = new Set([10, 20, 30, 50]);
const previewEnabled = process.env.NEXT_PUBLIC_ENABLE_PROVISIONAL_PREVIEW === "true";
const previewQuarter = process.env.NEXT_PUBLIC_PREVIEW_QUARTER ?? "2026-Q3";

export default async function GitHubDevelopersPage({
  searchParams,
}: {
  searchParams: Promise<{ limit?: string }>;
}) {
  const params = await searchParams;
  const requested = Number(params.limit ?? 10);
  const limit = allowed.has(requested) ? requested : 10;

  if (previewEnabled) {
    const emptyPreview: PreviewRankingResponse = {
      slug: "github-developers",
      name: "GitHub Developers",
      quarter: previewQuarter,
      ranking_type: "INDEX",
      algorithm_name: "DevRankUG",
      algorithm_version: "1.0.0",
      official: false,
      reviewed_pool_count: 0,
      cutoff_at: null,
      limit,
      results: [],
    };
    const ranking = await safeApiGet<PreviewRankingResponse>(
      `/v1/preview/rankings/github-developers?limit=${limit}&quarter=${previewQuarter}`,
      emptyPreview,
    );
    return (
      <main>
        <div className="breadcrumb"><a href="/">TopTenUG</a> / <a href="/technology">Technology</a> / GitHub Developers</div>
        <section className="hero">
          <span className="eyebrow">Live evidence preview</span>
          <h1 className="page-title">Top Ugandan GitHub Developers</h1>
          <p className="hero-copy">
            A transparent preview of the reviewed pool using the same deterministic DevRankUG engine intended for the official quarterly index.
          </p>
          <div className="actions"><a className="button secondary" href="/methodology/devrankug-v1">View methodology</a></div>
        </section>
        <ProvisionalBanner
          reviewedPoolCount={ranking.reviewed_pool_count}
          cutoffAt={ranking.cutoff_at}
        />
        <Leaderboard ranking={ranking} limit={limit} provisional />
      </main>
    );
  }

  const empty: RankingResponse = {
    slug: "github-developers",
    quarter: "Awaiting first official quarter",
    ranking_type: "INDEX",
    algorithm_name: "DevRankUG",
    algorithm_version: "1.0.0",
    published_at: "",
    methodology_url: "/v1/methodology/devrankug-v1",
    results: [],
  };
  const ranking = await safeApiGet<RankingResponse>(
    `/v1/rankings/github-developers?limit=${limit}`,
    empty,
  );
  return (
    <main>
      <div className="breadcrumb"><a href="/">TopTenUG</a> / <a href="/technology">Technology</a> / GitHub Developers</div>
      <section className="hero">
        <span className="eyebrow">Official quarterly index</span>
        <h1 className="page-title">Top Ugandan GitHub Developers</h1>
        <p className="hero-copy">
          Ranked by TopTenUG&apos;s deterministic DevRankUG algorithm using project adoption, contribution activity, project breadth, audience and collaboration signals.
        </p>
        <div className="actions"><a className="button secondary" href="/methodology/devrankug-v1">View methodology</a></div>
      </section>
      <Leaderboard ranking={ranking} limit={limit} />
    </main>
  );
}
