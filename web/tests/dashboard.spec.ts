import { expect, test } from "@playwright/test";

// The pilot dashboard, in demo mode (?demo=1), which needs no pilot code and no
// live /api/aggregate endpoint: the sample data is generated client-side with
// the same shape the server will return. Covers demo rendering, the range
// switch, and the CSV download; the real sign-in path (a pilot code against
// the live API) isn't exercised here since that needs a live campus.

test("demo mode renders the console with the sample-data banner", async ({ page }) => {
  const res = await page.goto("/dashboard/?demo=1");
  expect(res?.status()).toBe(200);
  await expect(page.getByText("Sample data, not a real campus.")).toBeVisible();

  // Overview tab, open by default: KPI tiles and the trend chart.
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await expect(page.getByText("Conversations, this week")).toBeVisible();
  await expect(page.getByText("Crisis hand-offs, this week")).toBeVisible();
  await expect(page.getByRole("img", { name: "Conversations and crisis hand-offs by week" })).toBeVisible();

  // Safety tab: the old "Checked" idea, now for staff, with a link back to /safety/.
  await page.getByRole("button", { name: "Safety" }).click();
  await expect(page.getByRole("heading", { name: "Safety" })).toBeVisible();
  await expect(page.getByText("Replies checked, this week")).toBeVisible();
  await expect(page.getByRole("link", { name: "How the safety check works" })).toHaveAttribute("href", "/safety/");

  // Use tab: focus areas and signed in versus open.
  await page.getByRole("button", { name: "Use" }).click();
  await expect(page.getByRole("heading", { name: "Use" })).toBeVisible();
  await expect(page.getByText("Focus areas, this week")).toBeVisible();
  await expect(page.getByText("Signed in versus open, this week")).toBeVisible();

  // No scroll overflow at this viewport.
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "page scrolls sideways").toBeLessThanOrEqual(1);
});

test("the range switch changes the number of weeks shown", async ({ page }) => {
  await page.goto("/dashboard/?demo=1");
  const table = page.locator("table").first();

  await page.getByRole("button", { name: "4 weeks" }).click();
  await expect(page.getByRole("button", { name: "4 weeks" })).toHaveAttribute("aria-pressed", "true");
  await expect.poll(async () => (await table.locator("tbody tr").count())).toBe(4);

  await page.getByRole("button", { name: "12 weeks" }).click();
  await expect(page.getByRole("button", { name: "12 weeks" })).toHaveAttribute("aria-pressed", "true");
  await expect.poll(async () => (await table.locator("tbody tr").count())).toBe(12);
});

test("Download CSV saves a file with the weekly figures", async ({ page }) => {
  await page.goto("/dashboard/?demo=1");
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Download CSV" }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^zenai-.*\.csv$/);
  const path = await download.path();
  expect(path).toBeTruthy();
});

test("the sign-in card offers the demo without a code", async ({ page }) => {
  await page.goto("/dashboard/");
  await expect(page.getByLabel("Pilot access code")).toBeVisible();
  const demoLink = page.getByRole("link", { name: "See a demo with sample data" });
  await expect(demoLink).toHaveAttribute("href", "/dashboard/?demo=1");
  await demoLink.click();
  await expect(page.getByText("Sample data, not a real campus.")).toBeVisible();
});
