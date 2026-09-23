import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ShareRanking } from "../components/share-ranking";

describe("ShareRanking", () => {
  it("derives official image only from immutable ranking result id", () => {
    render(<ShareRanking resultId="official-result-123" entityName="Jane" />);
    const link = screen.getByText("Download card").getAttribute("href") ?? "";
    expect(link).toContain("official-result-123");
    expect(link).not.toContain("rank=");
    expect(link).not.toContain("score=");
  });
});
