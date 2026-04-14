#!/usr/bin/env node
/**
 * Sharingan v0.3 — Auth Capture
 *
 * Opens a real Chromium window so the user can log in manually
 * (handles Auth0, OAuth, email verification, MFA, CAPTCHA, anything).
 * When the user signals "done", captures the authenticated session as
 * a Playwright storageState file that all subsequent tests can reuse.
 *
 * Usage:
 *   node auth-capture.js \
 *     --url <login-url> \
 *     --state <storage-state-output-path> \
 *     --signal <signal-file-path> \
 *     [--ready-url <success-url-pattern>] \
 *     [--timeout-minutes <N>]
 *
 * The script polls the signal file every 500ms. When the file appears,
 * it captures storageState, deletes the signal file, closes the browser,
 * and exits 0.
 *
 * Optionally, if --ready-url is given, the script auto-signals when the
 * page URL matches the pattern AND has been stable for 3 seconds. This
 * is a convenience for users who don't want to type "done" — the moment
 * they reach the dashboard, the capture happens automatically.
 *
 * If the user closes the browser window manually, the script exits 1
 * without capturing.
 */

const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

function parseArgs() {
  const args = { timeoutMinutes: 30 };
  for (let i = 2; i < process.argv.length; i++) {
    const flag = process.argv[i];
    const value = process.argv[i + 1];
    if (flag === "--url") { args.url = value; i++; }
    else if (flag === "--state") { args.state = value; i++; }
    else if (flag === "--signal") { args.signal = value; i++; }
    else if (flag === "--ready-url") { args.readyUrl = value; i++; }
    else if (flag === "--timeout-minutes") { args.timeoutMinutes = Number(value); i++; }
    else if (flag === "--help" || flag === "-h") {
      console.log(__doc__ || "See script header for usage.");
      process.exit(0);
    }
  }
  if (!args.url || !args.state || !args.signal) {
    console.error("Usage: auth-capture.js --url <login-url> --state <output-path> --signal <signal-file>");
    process.exit(2);
  }
  return args;
}

function log(msg) {
  // Prefix all output so users see clearly it's from Sharingan
  console.log(`[sharingan] ${msg}`);
}

async function main() {
  const args = parseArgs();

  // Clean any stale signal from a previous run
  if (fs.existsSync(args.signal)) {
    try { fs.unlinkSync(args.signal); } catch {}
  }

  // Make sure output directory exists
  fs.mkdirSync(path.dirname(args.state), { recursive: true });

  log("launching headed Chromium...");
  const browser = await chromium.launch({
    headless: false,
    args: ["--start-maximized"],
  });

  let context;
  try {
    context = await browser.newContext({
      viewport: null, // Use full window size
    });
  } catch (err) {
    log(`failed to create browser context: ${err.message}`);
    await browser.close();
    process.exit(1);
  }

  const page = await context.newPage();

  // Navigate to the login URL
  log(`navigating to ${args.url}`);
  try {
    await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 30000 });
  } catch (err) {
    log(`failed to load ${args.url}: ${err.message}`);
    log("is your dev server running?");
    await browser.close();
    process.exit(1);
  }

  log("");
  log("=========================================================");
  log("  BROWSER OPEN — log in at your own pace.");
  log("  Email verification / OAuth / MFA / CAPTCHA all OK.");
  log("");
  log("  When you're done, tell Claude Code: \"done\"");
  log(`  (or touch ${args.signal})`);
  if (args.readyUrl) {
    log(`  (or just navigate to ${args.readyUrl} — auto-detected)`);
  }
  log("=========================================================");
  log("");

  const startedAt = Date.now();
  const timeoutMs = args.timeoutMinutes * 60 * 1000;
  let stableUrl = null;
  let stableSince = 0;

  // Poll for signal OR auto-detect via URL
  while (true) {
    if (fs.existsSync(args.signal)) {
      log("signal received, capturing session...");
      break;
    }

    if (!browser.isConnected()) {
      log("browser closed before signal — aborting");
      process.exit(1);
    }

    if (args.readyUrl) {
      try {
        const currentUrl = page.url();
        if (currentUrl.match(new RegExp(args.readyUrl))) {
          if (stableUrl === currentUrl) {
            if (Date.now() - stableSince > 3000) {
              log(`auto-detected ready URL: ${currentUrl}`);
              break;
            }
          } else {
            stableUrl = currentUrl;
            stableSince = Date.now();
          }
        } else {
          stableUrl = null;
          stableSince = 0;
        }
      } catch {
        // page closed mid-read — handled by isConnected check
      }
    }

    if (Date.now() - startedAt > timeoutMs) {
      log(`timed out after ${args.timeoutMinutes} minutes`);
      await browser.close();
      process.exit(1);
    }

    await new Promise((r) => setTimeout(r, 500));
  }

  // Capture the session
  let finalUrl = "";
  try {
    finalUrl = page.url();
  } catch {}

  try {
    await context.storageState({ path: args.state });
  } catch (err) {
    log(`failed to capture storage state: ${err.message}`);
    await browser.close();
    process.exit(1);
  }

  log(`captured session to ${args.state}`);
  if (finalUrl) log(`final URL: ${finalUrl}`);

  // Cleanup
  try { fs.unlinkSync(args.signal); } catch {}
  await browser.close();
  process.exit(0);
}

main().catch((err) => {
  console.error(`[sharingan] auth-capture crashed: ${err.message}`);
  process.exit(1);
});
