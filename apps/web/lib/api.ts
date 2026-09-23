const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type DashboardData = {
  current_quarter: string | null;
  indexed_entities: number;
  active_rankings: number;
  published_snapshots: number;
};

export type RankingResult = {
  result_id: string | null;
  entity_id: string;
  slug: string;
  name: string;
  rank: number;
  score: number;
  previous_rank: number | null;
  movement: number | null;
  confidence: number;
  provenance_count: number;
};

export type RankingResponse = {
  slug: string;
  quarter: string;
  ranking_type: "METRIC" | "INDEX" | "TREND";
  algorithm_name: string;
  algorithm_version: string;
  published_at: string;
  methodology_url: string;
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
  entity_id: string;
  slug: string;
  name: string;
  current_rankings: Array<{
    ranking: string; quarter: string; rank: number; score: number; confidence: number;
    factor_breakdown: Record<string, { normalized?: number | null; weight?: number }>;
    evidence_urls: string[];
  }>;
};

export type EntityHistoryResponse = { slug: string; history: Array<{ ranking: string; quarter: string; rank: number; score: number }> };
export type MethodologyResponse = { name:string; version:string; ranking_type:string; eligibility_policy:string; missing_data_policy:string; minimum_factor_coverage:number; tie_breaker:string; factors:Array<{name:string;weight:number;metric:string;normalization:string}>; limitations:string[] };
export type ShareMetadata = { ranking_result_id:string; entity_id:string; slug:string; name:string; category:string; quarter:string; ranking_type:string; algorithm_name:string; algorithm_version:string; rank:number; score:number; previous_rank:number|null; movement:number|null; canonical_url:string };
