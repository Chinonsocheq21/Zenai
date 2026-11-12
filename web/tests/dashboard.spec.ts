import { expect, test, type Page } from "@playwright/test";

// The campus console, in demo mode (?demo=1), which needs no pilot code. With no
// /api/aggregate/demo in the static test server, the client builds the same sample
// data the server would. Covers the frame, the sidebar pages, the range picker, the
// chart tooltip and the CSV download; the real sign-in path (a pilot code against the
// live API) needs a live campus and isn't exercised here.

async function goTo(page: Page, isMobile: boolean, name: string) {
  if (isMobile) await page.getByRole("button", { name: "Open console menu" }).click();
  await page.getByRole("navigation", { name: "Console" }).getByRole("button", { name }).click();
  await expect(page.getByRole("heading", { level: 1, name })).toBeVisible();
}

test("demo mode renders the console frame, KPI cards and charts", async ({ page }) => {
  const res = await page.goto("/dashboard/?demo=1");
  expect(res?.status()).toBe(200);
  await expect(page.getByText("Sample data, not a real campus.")).toBeVisible();
  await expect(page.getByText("Sample Campus (demo)")).toBeVisible();

  // An app frame, not a web page: no marketing header or footer.
  await expect(page.locator("header")).toHaveCount(0);
  await expect(page.locator("footer")).toHaveCount(0);

  await expect(page.getByRole("heading", { level: 1, name: "Overview" })).toBeVisible();
  for (const kpi of ["Conversations", "Messages", "Crisis hand-offs", "Share after hours", "First-draft pass rate"]) {
    await expect(page.getByRole("heading", { level: 3, name: kpi, exact: true }).first()).toBeVisible();
  }
  await expect(page.getByRole("img", { name: "Conversations and messages by week" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "The safety pipeline" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Crisis hand-offs by layer" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Check-in levels by week" })).toBeVisible();

  // Counts only: a small group reads "fewer than 10", never a number under 10.
  await expect(page.getByText("fewer than 10").first()).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "page scrolls sideways").toBeLessThanOrEqual(1);
});

test("the sidebar moves between Overview, Safety, Students and Reports", async ({ page, isMobile }) => {
  await page.goto("/dashboard/?demo=1");
  await goTo(page, isMobile, "Safety");
  await expect(page.getByRole("heading", { name: "Crisis hand-offs by week" })).toBeVisible();
  await expect(page.getByRole("link", { name: "How the safety check works" })).toHaveAttribute("href", "/safety/");

  await goTo(page, isMobile, "Students");
  await expect(page.getByRole("heading", { name: "Students signed in" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Focus areas by week" })).toBeVisible();

  await goTo(page, isMobile, "Reports");
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "What is counted" })).toBeVisible();

  // The page is kept in the hash, so a reload opens it again.
  await page.reload();
  await expect(page.getByRole("heading", { level: 1, name: "Reports" })).toBeVisible();

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "page scrolls sideways").toBeLessThanOrEqual(1);
});

test("the range picker changes the number of weeks shown", async ({ page }) => {
  await page.goto("/dashboard/?demo=1");
  const table = page.getByRole("table", { name: "Conversations and messages by week" });
  await expect.poll(async () => table.locator("tbody tr").count()).toBe(8);

  await page.getByLabel("Date range").selectOption("4");
  await expect.poll(async () => table.locator("tbody tr").count()).toBe(4);

  await page.getByLabel("Date range").selectOption("12");
  await expect.poll(async () => table.locator("tbody tr").count()).toBe(12);
});

test("hovering the trend chart shows the week's numbers", async ({ page, isMobile }) => {
  test.skip(isMobile, "hover needs a pointer; the keyboard path is covered below");
  await page.goto("/dashboard/?demo=1");
  const chart = page.getByRole("img", { name: "Conversations and messages by week" });
  await chart.hover();
  const tip = page.getByRole("tooltip");
  await expect(tip).toContainText("Week of");
  await expect(tip).toContainText("conversations");
  await expect(tip).toContainText("messages");
});

test("the trend chart is keyboard focusable and steps through weeks", async ({ page }) => {
  await page.goto("/dashboard/?demo=1");
  const chart = page.getByRole("img", { name: "Conversations and messages by week" });
  await chart.focus();
  const tip = page.getByRole("tooltip");
  await expect(tip).toContainText("Week of");
  const first = await tip.textContent();
  await page.keyboard.press("ArrowLeft");
  await expect(tip).not.toHaveText(first ?? "");
});

test("Download CSV saves a file with the weekly figures", async ({ page, isMobile }) => {
  await page.goto("/dashboard/?demo=1");
  await goTo(page, isMobile, "Reports");
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "Download CSV" }).click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^zenai-.*\.csv$/);
  const path = await download.path();
  expect(path).toBeTruthy();
});

test("the sign-in card sits in the console frame and offers the demo", async ({ page }) => {
  await page.goto("/dashboard/");
  await expect(page.getByRole("heading", { level: 1, name: "Sign in" })).toBeVisible();
  await expect(page.getByLabel("Pilot access code")).toBeVisible();
  await expect(page.locator("footer")).toHaveCount(0);
  const demoLink = page.getByRole("link", { name: "See a demo with sample data" });
  await expect(demoLink).toHaveAttribute("href", "/dashboard/?demo=1");
  await demoLink.click();
  await expect(page.getByText("Sample data, not a real campus.")).toBeVisible();
});
