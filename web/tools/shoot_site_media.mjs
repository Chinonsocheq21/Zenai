#!/usr/bin/env node
// Captures real screenshots of the hosted ZenAI app for use on the marketing site
// (the home hero, the /students/ page), so the site never shows an illustration where
// it could show the product.
//
// Usage:
//   SMOKE_INVITE=<code> node tools/shoot_site_media.mjs [baseUrl]
//
// baseUrl defaults to https://zenai-app.vercel.app. SMOKE_INVITE is required to reach
// the screens behind sign-in (Talk, Check in, Find help); never hard-code the code
// here or print it. The crisis hand-off needs no sign-in, so it still runs without one.
//
// Written to be easy to re-run: every screen is reached through a stable id or a
// data-go value on the bottom nav, never a pixel position, and each capture is wrapped
// so a screen the app no longer has (for example if tabs are renamed) just logs a
// warning and the rest of the run still finishes. Re-run this after any app change
// to nav, tab names or screen layout, and after the live app is redeployed.
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(here, "..", "public", "media", "app");

const BASE = (process.argv[2] || process.env.SMOKE_BASE_URL || "https://zenai-app.vercel.app").replace(/\/+$/, "");
const INVITE = process.env.SMOKE_INVITE || "";

// Tab names to try, oldest first: the app is moving from five tabs (talk, checkin,
// progress, finder, privacy) to four (talk, checkin, finder, you), so a capture that
// wants "checkin" or "finder" keeps working either way without edits.
const TAB_ALIASES = {
  talk: ["talk"],
  checkin: ["checkin"],
  finder: ["finder"],
};

async function waitVisible(page, selector, timeout = 8000) {
  try {
    await page.locator(selector).first().waitFor({ state: "visible", timeout });
    return true;
  } catch {
    return false;
  }
}

async function goTab(page, key) {
  for (const name of TAB_ALIASES[key] || [key]) {
    const btn = page.locator(`#nav [data-go="${name}"]`);
    if (await btn.count()) {
      await btn.first().click();
      return true;
    }
  }
  return false;
}

// Dismisses the welcome screen and signs in with the invite code, if one was given.
// Returns true once the app is past sign-in (or was already past it, for a returning
// session), false if a screen behind sign-in cannot be reached this run.
async function enterApp(page) {
  if (await waitVisible(page, "#start", 4000)) await page.locator("#start").click();
  if (!(await waitVisible(page, "#signinGate", 3000))) return true; // no gate: already signed in

  if (!INVITE) {
    console.warn("SMOKE_INVITE is not set: skipping sign-in, screens behind it will be missed this run.");
    return false;
  }
  const toggle = page.locator("#sgInviteToggle");
  if (await toggle.count()) await toggle.click();
  await page.locator("#sgCode").fill(INVITE);
  await page.locator("#sgCodeGo").click();
  await waitVisible(page, "#talk", 10_000);
  return true;
}

async function shoot(page, file) {
  await page.waitForTimeout(400); // let the orb settle and any entrance animation finish
  await page.screenshot({ path: path.join(OUT, file) });
  console.log(`  wrote ${file}`);
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({ channel: "chrome" });

  console.log(`Shooting site media from ${BASE}`);

  // Phone: the chat screen, for the hero's phone frame and the /students/ page.
  {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.goto(`${BASE}/app/`, { waitUntil: "networkidle" });
    const in_ = await enterApp(page);
    if (in_ && (await goTab(page, "talk"))) await shoot(page, "app-chat.png");
    else console.warn("  skipped app-chat.png: could not reach Talk");
    await page.close();
  }

  // Laptop: Talk home, for the hero's laptop frame, behind the phone.
  {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    await page.goto(`${BASE}/app/`, { waitUntil: "networkidle" });
    const in_ = await enterApp(page);
    if (in_ && (await goTab(page, "talk"))) await shoot(page, "app-laptop-talk.png");
    else console.warn("  skipped app-laptop-talk.png: could not reach Talk");
    await page.close();
  }

  // Phone: Check in and Find help, for the /students/ page.
  {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.goto(`${BASE}/app/`, { waitUntil: "networkidle" });
    const in_ = await enterApp(page);
    if (in_ && (await goTab(page, "checkin"))) await shoot(page, "app-checkin.png");
    else console.warn("  skipped app-checkin.png: could not reach Check in");
    if (in_ && (await goTab(page, "finder"))) await shoot(page, "app-findhelp.png");
    else console.warn("  skipped app-findhelp.png: could not reach Find help");
    await page.close();
  }

  // Phone: the crisis hand-off, reached straight from Get help now. Needs no sign-in,
  // so it is shot in its own page without calling enterApp's sign-in step.
  {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await page.goto(`${BASE}/app/`, { waitUntil: "networkidle" });
    if (await waitVisible(page, "#start", 4000)) await page.locator("#start").click();
    // Get help now exists in two places: the header once past welcome, or inside the
    // sign-in gate itself when sign-in is required. Either one opens the same crisis screen.
    const helpBtn = (await waitVisible(page, "#signinGate", 3000)) ? page.locator("#sgHelp") : page.locator("#helpBtn");
    if (await helpBtn.count()) {
      await helpBtn.click();
      if (await waitVisible(page, "#crisis")) await shoot(page, "app-crisis.png");
      else console.warn("  skipped app-crisis.png: crisis screen did not open");
    } else {
      console.warn("  skipped app-crisis.png: no Get help now button found");
    }
    await page.close();
  }

  await browser.close();
  console.log(`Done. Screenshots are in ${OUT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
