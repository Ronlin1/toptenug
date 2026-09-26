const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type DashboardData = {
  current_quarter: string | null;
  indexed_entities: number;
  active_rankings: number;
  published_results: number;
  source_links: number;
  biggest_movers: unknown[];
  categories: Array<{ slug: string; name: string; ranking_type: "METRIC" | "INDEX" | "TREND" }>;
};

type FactorBreakdown = Record<string, {
  raw?: number | null;
  normalized?: number | null;
  weight?: number;
  contribution?: number;
  missing_policy?: string;
}>;

export type RankingResult = {
  ranking_result_id: string;
  entity_id: string;
  entity_slug: string;
  name: string;
  avatar_url: string | null;
  rank: number;
  score: number;
  previous_rank: number | null;
  movement: number | null;
  confidence: number;
  factor_coverage: number;
  factor_breakdown: FactorBreakdown;
  provenance: { source_count: number; source_urls: string[] };
  profile_url: string | null;
};

export type RankingResponse = {
  slug: string;
  name?: string;
  quarter: string;
  ranking_type: "METRIC" | "INDEX" | "TREND";
  algorithm_name: string;
  algorithm_version: string;
  published_at: string;
  methodology_url: string;
  limit?: number;
  results: RankingResult[];
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`TopTenUG API request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export async function safeApiGet<T>(path: string, fallback: T): Promise<T> {
  try { return await apiGet<T>(path); } catch { return fallback; }
}

export type EntityResponse = {
  id: string;
  slug: string;
  name: string;
  avatar_url: string | null;
  summary: string | null;
  evidence_urls: string[];
  current_rankings: Array<{
    ranking_result_id: string;
    category_slug: string;
    category_name: string;
    quarter: string;
    rank: number;
    score: number;
    previous_rank: number | null;
    movement: number | null;
    confidence: number;
    factor_coverage: number;
    factor_breakdown: FactorBreakdown;
    methodology_url: string;
  }>;
};

export type EntityHistoryResponse = {
  entity_slug: string;
  history: Array<{
    category_slug: string;
    quarter: string;
    rank: number;
    score: number;
    factor_coverage: number;
  }>;
};

export type MethodologyResponse = {
  slug: string;
  name: string;
  version: string;
  ranking_type: string;
  eligibility_policy: string;
  missing_data_policy: string;
  minimum_factor_coverage: number;
  tie_breaker: string;
  factors: Record<string, { weight: number; metric: string; normalization: string }>;
  limitations: string[];
};

export type ShareMetadata = {
  ranking_result_id: string;
  rank: number;
  score: number;
  movement: number | null;
  entity_name: string;
  entity_slug: string;
  category_name: string;
  category_slug: string;
  ranking_type: string;
  quarter: string;
  algorithm_name: string;
  algorithm_version: string;
  canonical_url: string;
  image_path: string;
};
