import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Leaderboard } from "../components/leaderboard";
import { ProvisionalBanner } from "../components/provisional-banner";
import type { PreviewRankingResponse, RankingResponse } from "../lib/api";

afterEach(cleanup);

const preview: PreviewRankingResponse = {
  slug: "github-developers",
  name: "GitHub Developers",
  quarter: "2026-Q3",
  ranking_type: "INDEX",
  algorithm_name: "DevRankUG",
  algorithm_version: "1.0.0",
  official: false,
  reviewed_pool_count: 37,
  cutoff_at: "2026-09-27T05:00:00+00:00",
  limit: 10,
  results: [
    {
      ranking_result_id: "preview-r1",
      entity_id: "1",
      entity_slug: "jane",
      name: "Jane",
      rank: 1,
      score: 91.2,
      confidence: 0.94,
      factor_coverage: 1,
      factor_breakdown: {},
      profile_url: "/v1/entities/jane",
    },
  ],
};

const official: RankingResponse = {
  slug: "github-developers",
  quarter: "2026-Q3",
  ranking_type: "INDEX",
  algorithm_name: "DevRankUG",
  algorithm_version: "1.0.0",
  published_at: "2026-10-01T08:00:00Z",
  methodology_url: "/v1/methodology/devrankug-v1",
  results: [],
};

describe("provisional ranking experience", () => {
  it("labels preview data as non-official and shows the reviewed pool", () => {
    render(<ProvisionalBanner reviewedPoolCount={preview.reviewed_pool_count} cutoffAt={preview.cutoff_at} />);

    expect(screen.getByText("Provisional — not an official quarterly ranking")).toBeTruthy();
    expect(screen.getByText(/37 reviewed, eligible developers/i)).toBeTruthy();
  });

  it("keeps the only public size controls at 10, 20, 30 and 50", () => {
    render(<Leaderboard ranking={preview} limit={10} provisional />);

    expect(screen.getByText("Top 10")).toBeTruthy();
    expect(screen.getByText("Top 20")).toBeTruthy();
    expect(screen.getByText("Top 30")).toBeTruthy();
    expect(screen.getByText("Top 50")).toBeTruthy();
    expect(screen.queryByText("Top 100")).toBeNull();
  });

  it("does not expose official share actions for provisional rows", () => {
    render(<Leaderboard ranking={preview} limit={10} provisional />);

    expect(screen.getByRole("link", { name: "Jane" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Share" })).toBeNull();
  });

  it("explains an empty provisional pool instead of pretending there is an official ranking", () => {
    render(<Leaderboard ranking={{ ...preview, results: [] }} limit={10} provisional />);

    expect(screen.getByText("Discovery and evidence review are still in progress. No provisional rows are available yet.")).toBeTruthy();
  });

  it("keeps published rankings free of provisional labelling", () => {
    render(<Leaderboard ranking={official} limit={10} />);

    expect(screen.queryByText("Provisional — not an official quarterly ranking")).toBeNull();
    expect(screen.getByText("No official ranking has been published yet.")).toBeTruthy();
  });
});
