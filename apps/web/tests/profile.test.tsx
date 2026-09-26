import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreBreakdown } from "../components/score-breakdown";

describe("ScoreBreakdown", () => {
  it("shows factor score and official weight", () => {
    render(<ScoreBreakdown factors={{project_adoption:{normalized:.82,weight:.30}}}/>);
    expect(screen.getByText("project adoption")).toBeTruthy();
    expect(screen.getByText("82/100 · 30%")).toBeTruthy();
  });
});
