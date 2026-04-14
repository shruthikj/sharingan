#!/usr/bin/env node
/**
 * Sharingan v0.3 — Screenshot Organizer
 *
 * Playwright stores screenshots in hashed directory names like
 * `dashboard-Authenticated-Da-e829f-ws-can-access-settings-page-authenticated/test-finished-1.png`.
 * This script flattens them into a clean, browseable folder named
 * by test, with a numeric prefix that preserves test order.
 *
 * Usage:
 *   node organize-screenshots.js \
 *     --results <test-results-dir> \
 *     --output <screenshots-dir> \
 *     [--results-json <playwright-results.json>]
 *
 * If results-json is provided, screenshots are sorted by test execution
 * order. Otherwise alphabetical by directory name.
 */

const fs = require("fs");
const path = require("path");

function parseArgs() {
  const args = {};
  for (let i = 2; i < process.argv.length; i++) {
    const flag = process.argv[i];
    const value = process.argv[i + 1];
    if (flag === "--results") { args.results = value; i++; }
    else if (flag === "--output") { args.output = value; i++; }
    else if (flag === "--results-json") { args.resultsJson = value; i++; }
  }
  if (!args.results || !args.output) {
    console.error("Usage: organize-screenshots.js --results <test-results-dir> --output <screenshots-dir>");
    process.exit(2);
  }
  return args;
}

function log(msg) {
  console.log(`[sharingan] ${msg}`);
}

function safeName(s) {
  return s.replace(/[^a-zA-Z0-9-_]+/g, "-").replace(/^-+|-+$/g, "");
}

function findScreenshots(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      const subDir = path.join(dir, entry.name);
      const pngs = fs.readdirSync(subDir).filter((f) => f.endsWith(".png"));
      const finished = pngs.find((f) => f.startsWith("test-finished"));
      const failed = pngs.find((f) => f.startsWith("test-failed"));
      const screenshot = finished || failed || pngs[0];
      if (screenshot) {
        out.push({
          dirName: entry.name,
          fullPath: path.join(subDir, screenshot),
        });
      }
    }
  }
  return out;
}

function getOrderedTests(resultsJsonPath) {
  if (!resultsJsonPath || !fs.existsSync(resultsJsonPath)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(resultsJsonPath, "utf-8"));
    const tests = [];
    function walk(suites) {
      for (const s of suites || []) {
        for (const spec of s.specs || []) {
          tests.push({
            title: spec.title,
            file: s.file || "",
            project: spec.projectName || "",
          });
        }
        walk(s.suites);
      }
    }
    walk(data.suites);
    return tests;
  } catch {
    return null;
  }
}

function main() {
  const args = parseArgs();

  fs.mkdirSync(args.output, { recursive: true });

  const screenshots = findScreenshots(args.results);
  if (screenshots.length === 0) {
    log(`no screenshots found in ${args.results}`);
    return;
  }

  log(`found ${screenshots.length} screenshots`);

  // Try to get test order from results.json
  const tests = getOrderedTests(args.resultsJson);

  // Build a mapping: dirName → ordering index
  const indexMap = {};
  if (tests) {
    tests.forEach((t, i) => {
      // Playwright dir naming: <file-stem>-<describe>-<test-title-truncated>-<project>
      // We do a fuzzy match by checking if the test title is in the dir name
      const safeTitle = safeName(t.title).toLowerCase();
      for (const s of screenshots) {
        if (s.dirName.toLowerCase().includes(safeTitle.substring(0, 20))) {
          if (indexMap[s.dirName] === undefined) {
            indexMap[s.dirName] = i;
          }
        }
      }
    });
  }

  // Sort: indexed first by their index, then unindexed alphabetically
  screenshots.sort((a, b) => {
    const ai = indexMap[a.dirName];
    const bi = indexMap[b.dirName];
    if (ai !== undefined && bi !== undefined) return ai - bi;
    if (ai !== undefined) return -1;
    if (bi !== undefined) return 1;
    return a.dirName.localeCompare(b.dirName);
  });

  // Copy with NN- prefix
  let count = 0;
  for (let i = 0; i < screenshots.length; i++) {
    const s = screenshots[i];
    // Strip Playwright's hash suffix and project name from dir name
    let cleanName = s.dirName
      .replace(/-(unauthenticated|authenticated|visual|perf|schema|setup)(-retry\d+)?$/i, "")
      .replace(/-[a-f0-9]{5}-/g, "-");
    cleanName = safeName(cleanName);
    const outName = `${String(i + 1).padStart(2, "0")}-${cleanName}.png`;
    const outPath = path.join(args.output, outName);
    try {
      fs.copyFileSync(s.fullPath, outPath);
      count++;
    } catch (err) {
      log(`failed to copy ${s.fullPath}: ${err.message}`);
    }
  }

  log(`organized ${count} screenshots → ${args.output}`);
}

main();
