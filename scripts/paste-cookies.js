#!/usr/bin/env node
/**
 * Sharingan v0.3 — Cookie Paste Fallback
 *
 * For users on remote servers without a display, or anyone who'd rather
 * log in elsewhere and paste cookies. Reads JSON from stdin and converts
 * it into a Playwright storageState file.
 *
 * Accepts two input formats:
 *
 * 1. Playwright storageState JSON (full export from another browser context)
 * 2. Browser DevTools cookie export (array of cookie objects)
 *
 * Usage:
 *   cat cookies.json | node paste-cookies.js \
 *     --state <output-path> \
 *     --origin <origin-url>
 *
 * Or interactively:
 *   node paste-cookies.js --state ./tests/sharingan/.auth/storage-state.json --origin http://localhost:3000
 *   <paste JSON>
 *   <Ctrl+D>
 */

const fs = require("fs");
const path = require("path");

function parseArgs() {
  const args = {};
  for (let i = 2; i < process.argv.length; i++) {
    const flag = process.argv[i];
    const value = process.argv[i + 1];
    if (flag === "--state") { args.state = value; i++; }
    else if (flag === "--origin") { args.origin = value; i++; }
  }
  if (!args.state || !args.origin) {
    console.error("Usage: paste-cookies.js --state <output-path> --origin <origin-url>");
    process.exit(2);
  }
  return args;
}

function log(msg) {
  console.log(`[sharingan] ${msg}`);
}

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.on("data", (chunk) => (data += chunk));
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

function buildStorageState(input, origin) {
  const parsed = JSON.parse(input);

  // Already a storageState file?
  if (parsed.cookies && parsed.origins) {
    return parsed;
  }

  // Just an array of cookies?
  if (Array.isArray(parsed)) {
    const url = new URL(origin);
    const cookies = parsed.map((c) => ({
      name: c.name,
      value: c.value,
      domain: c.domain || url.hostname,
      path: c.path || "/",
      expires: c.expires || c.expirationDate || -1,
      httpOnly: c.httpOnly || false,
      secure: c.secure || url.protocol === "https:",
      sameSite: c.sameSite || "Lax",
    }));
    return { cookies, origins: [] };
  }

  // Object with cookies key?
  if (parsed.cookies && Array.isArray(parsed.cookies)) {
    return { cookies: parsed.cookies, origins: parsed.origins || [] };
  }

  throw new Error("Unrecognized input format. Expected storageState JSON, cookie array, or {cookies: [...]}.");
}

async function main() {
  const args = parseArgs();

  log("paste cookie/storageState JSON below, then press Ctrl+D:");
  const input = await readStdin();

  if (!input.trim()) {
    log("no input received");
    process.exit(1);
  }

  let storageState;
  try {
    storageState = buildStorageState(input, args.origin);
  } catch (err) {
    log(`parse error: ${err.message}`);
    process.exit(1);
  }

  fs.mkdirSync(path.dirname(args.state), { recursive: true });
  fs.writeFileSync(args.state, JSON.stringify(storageState, null, 2));

  log(`wrote ${storageState.cookies.length} cookies to ${args.state}`);
}

main().catch((err) => {
  console.error(`[sharingan] paste-cookies crashed: ${err.message}`);
  process.exit(1);
});
