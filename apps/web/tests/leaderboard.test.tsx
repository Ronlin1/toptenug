import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Leaderboard } from "../components/leaderboard";

const ranking = {
  slug:"github-developers",
  quarter:"2026-Q3",
  ranking_type:"INDEX" as const,
  algorithm_name:"DevRankUG",
  algorithm_version:"1.0.0",
  published_at:"2026-09-30",
  methodology_url:"/v1/methodology/devrankug-v1",
  results:[{
    ranking_result_id:"r1",
    entity_id:"1",
    entity_slug:"jane",
    name:"Jane",
    avatar_url:null,
    rank:1,
    score:91.2,
    previous_rank:3,
    movement:2,
    confidence:.94,
    factor_coverage:1,
    factor_breakdown:{},
    provenance:{source_count:5,source_urls:[]},
    profile_url:"/v1/entities/jane",
  }],
};

describe("Leaderboard", () => {
  it("shows official context, rank movement and limit controls", () => {
    render(<Leaderboard ranking={ranking} limit={10} />);
    expect(screen.getByText("Jane")).toBeTruthy();
    expect(screen.getByText("5 public evidence signals")).toBeTruthy();
    expect(screen.getByText("↑ 2")).toBeTruthy();
    expect(screen.getByText("Top 50")).toBeTruthy();
    expect(screen.getByText("INDEX")).toBeTruthy();
  });
});
