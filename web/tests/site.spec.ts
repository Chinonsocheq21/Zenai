import { expect, test } from "@playwright/test";

const PAGES = ["/", "/how-it-works/", "/safety/", "/help/", "/privacy/", "/terms/"];

for (const path of PAGES) {
  test(`${path} loads, fits the screen, and has the way to help and to the app`, async ({ page, isMobile }) => {
    const res = await page.goto(path);
    expect(res?.status()).toBe(200);
    await expect(page.locator("h1").first()).toBeVisible();

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, "page scrolls sideways").toBeLessThanOrEqual(1);

    await expect(page.getByRole("link", { name: "Get help now" }).first()).toBeVisible();
    if (isMobile) await page.getByRole("button", { name: "Open menu" }).click();
    await expect(page.locator('header a[href="/app/"]:visible').first()).toBeVisible();

    await expect(page.locator("footer")).toContainText("988");
    await expect(page.locator('footer a[href="/privacy/"]')).toBeVisible();
  });
}

test("every internal link on every page resolves", async ({ page, request }) => {
  const seen = new Set<string>();
  for (const path of PAGES) {
    await page.goto(path);
    const hrefs = await page.locator("a[href]").evaluateAll((as) => as.map((a) => a.getAttribute("href") || ""));
    hrefs.filter((h) => h.startsWith("/") && !h.startsWith("//")).forEach((h) => seen.add(h.split("#")[0]));
  }
  const broken: string[] = [];
  for (const h of seen) {
    const r = await request.get(h);
    if (r.status() !== 200) broken.push(`${h} -> ${r.status()}`);
  }
  expect(broken, "broken links").toEqual([]);
  expect(seen.size).toBeGreaterThanOrEqual(7);   // the six pages and the app
});

test("the app links back to the site", async ({ page, request }) => {
  await page.goto("/app/");
  const start = page.locator("#start");           // the first-visit welcome screen has no header
  if (await start.isVisible()) await start.click();
  for (const name of ["Home", "Help"]) {
    await expect(page.getByRole("link", { name }).first()).toBeVisible();
    const href = await page.getByRole("link", { name }).first().getAttribute("href");
    expect(href).toBeTruthy();
    expect((await request.get(href!)).status(), `${name} -> ${href}`).toBe(200);
  }
});

test("the help page needs no sign-in and leads with 988", async ({ page }) => {
  await page.goto("/help/");
  await expect(page.getByRole("link", { name: "Call 988" })).toHaveAttribute("href", "tel:988");
  await expect(page.getByRole("link", { name: "Text 988" })).toHaveAttribute("href", "sms:988");
  await expect(page.getByText("Counseling Center").first()).toBeVisible();
});

test("an unknown page shows the 404 with a way home", async ({ page }) => {
  const res = await page.goto("/no-such-page/");
  expect(res?.status()).toBe(404);
  await expect(page.locator('header a[href="/"]').first()).toBeVisible();
});
