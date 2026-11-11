import { expect, test, type Page } from "@playwright/test";

// The crisis path, end to end, on the REAL site (production by default):
//   PROD_URL=https://zenai-app.vercel.app npx playwright test crisis.spec.ts
// Messages are clearly synthetic. Explicit language is caught by the app itself
// (crisis-rules.js); "I can't go on" is caught by the server's rules, so both
// halves of the safety net are exercised. Neither ever reaches a language model.
const PROD = process.env.PROD_URL || "https://zenai-app.vercel.app";
test.use({ baseURL: PROD });

// The hosted app asks visitors to sign in before they can talk. Tests that type
// a message sign in first with an invite code (SMOKE_INVITE, the same one the
// uptime check uses); the sign-in screen's own help is tested signed out.
const INVITE = process.env.SMOKE_INVITE || "";

async function openApp(page: Page) {
  const me = await (await page.request.get("/api/auth/me")).json();
  if (me.required) {
    test.skip(!INVITE, "sign-in is required here: set SMOKE_INVITE to an invite code");
    const r = await page.request.post("/api/auth/invite", {
      data: { code: INVITE }, headers: { "X-ZenAI-Device": "crisis-spec-" + Math.random().toString(36).slice(2, 10) } });
    expect(r.status(), "the invite code signs in").toBe(200);
  }
  await page.goto("/app/");
  // A signed-in student is moved to Talk on their own once the account check answers;
  // only press Start talking if the old welcome is still the screen after that.
  const msg = page.locator("#msg");
  await msg.waitFor({ state: "visible", timeout: 6_000 }).catch(() => {});
  if (!(await msg.isVisible())) await page.locator("#start").click({ timeout: 5_000 });
  await expect(msg).toBeVisible();
}

async function send(page: Page, text: string) {
  await page.fill("#msg", text);
  await page.click("#send");
}

async function expectHandOff(page: Page, isLaptop: boolean) {
  const dialog = page.locator("#crisis");
  await expect(dialog).toBeVisible({ timeout: 15_000 });
  await expect(dialog.getByText("Call 988 now")).toBeVisible();
  await expect(dialog.getByText("Text 988")).toBeVisible();
  await expect(dialog.getByText("Chat online")).toBeVisible();
  await expect(dialog.getByText("Call 911")).toBeVisible();
  await expect(dialog.getByText(/1-800-422-0009/)).toBeVisible();          // the campus 24/7 line, tappable
  await expect(dialog.locator('a[href^="tel:"]').first()).toBeVisible();
  await expect(dialog.locator('a[href*="988lifeline.org/chat"]').first()).toBeVisible();
  const focusInside = await page.evaluate(() => !!document.activeElement?.closest("#crisis"));
  expect(focusInside, "keyboard focus moves into the hand-off").toBe(true);
  // the chat behind is covered and inert: nothing can be typed or tabbed to during a hand-off
  const blocked = await page.evaluate(() => !!document.querySelector("#msg")?.closest("[inert]"));
  expect(blocked, "the message box is inert behind the hand-off").toBe(true);
  if (isLaptop) await expect(dialog.getByText("Chat online").first()).toBeVisible();
}

test("explicit crisis language hands off, caught in the app itself", async ({ page }, info) => {
  await openApp(page);
  await send(page, "synthetic test: I don’t want to be here anymore");
  await expectHandOff(page, info.project.name === "laptop");
  await page.getByText("I'm safe, take me back").first().click();
  await expect(page.locator("#crisis")).toBeHidden();
  await expect(page.locator("#msg")).toBeVisible();
  await expect(page.locator("#helpBtn")).toBeVisible();                     // help stays one tap away
});

test("indirect crisis language hands off, caught by the server", async ({ page }, info) => {
  await openApp(page);
  const reply = page.waitForResponse((r) => r.url().includes("/api/chat") && r.request().method() === "POST");
  await send(page, "synthetic test: I can't go on anymore");
  const r = await reply;
  expect(r.status()).toBe(200);
  expect((await r.json()).escalate).toBe(true);
  await expectHandOff(page, info.project.name === "laptop");
});

test("with the network down, a crisis still hands off", async ({ page }, info) => {
  await openApp(page);
  await page.route("**/api/**", (route) => route.abort());
  await send(page, "synthetic test: I want to end my life");
  await expectHandOff(page, info.project.name === "laptop");
});

test("Get help now opens the same help without ending the conversation", async ({ page }) => {
  await openApp(page);
  await page.click("#helpBtn");
  await expect(page.locator("#crisis").getByText("Call 988 now")).toBeVisible();
});

test("signed out, the sign-in screen still offers help and 988", async ({ browser }) => {
  const ctx = await browser.newContext();                        // no session cookie
  const page = await ctx.newPage();
  const me = await (await page.request.get("/api/auth/me")).json();
  test.skip(!me.required, "this site does not require sign-in");
  await page.goto("/app/");
  const gate = page.locator("#signinGate");                     // signed out, it is the first screen
  await expect(gate).toBeVisible({ timeout: 10_000 });
  await expect(gate.locator('a[href^="tel:988"], a[href^="sms:988"]').first()).toBeVisible();
  await gate.getByText(/Get help now/).first().click();
  await expect(page.locator("#crisis").getByText("Call 988 now")).toBeVisible();
  await ctx.close();
});
