import { expect, test } from "@playwright/test";

test("leaderboard route remains usable without horizontal overflow", async ({ page }) => {
  await page.goto("/technology/github-developers");
  await expect(page.getByRole("heading", { name: "Top Ugandan GitHub Developers" })).toBeVisible();
  const fitsViewport = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
  expect(fitsViewport).toBe(true);
  await expect(page.getByRole("link", { name: "Top 50" })).toBeVisible();
});
