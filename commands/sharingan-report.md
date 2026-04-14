# /sharingan-report — Regenerate Report from Last Run

Regenerate `SHARINGAN_REPORT.md` from the most recent test results. Useful after manual fixes, or to refresh the report with the current state.

## Steps

1. **Find the results:**
   - `tests/sharingan/results.json`
   - If missing, tell the user to run `/sharingan` or `/sharingan-fix` first

2. **Re-run the test suite** to get the latest state (don't trust stale results):
   ```bash
   cd tests/sharingan && npx playwright test 2>&1 | tail -10
   ```

3. **Re-organize screenshots** (in case there are new ones):
   ```bash
   node ~/.sharingan/scripts/organize-screenshots.js \
     --results tests/sharingan/test-results \
     --output tests/sharingan/screenshots \
     --results-json tests/sharingan/results.json
   ```

4. **Read the results** and count: passed, failed, flaky, marked-as-known-bug.

5. **List bugs found** by grepping the test files for `test.fail(true, "BUG: ...")` comments:
   ```bash
   grep -rn "test.fail.*BUG:" tests/sharingan/
   ```

6. **Detect performance metrics** by grepping the test output for `Perf for ...` lines.

7. **Write `SHARINGAN_REPORT.md`** with the same structure as the main `/sharingan` command:
   - Summary (counts, time, bugs)
   - Test results table by category
   - Bugs found (each with file, severity, fix)
   - Screenshots (link to `tests/sharingan/screenshots/`)
   - Visual baselines (link to snapshot dir)
   - Performance summary
   - How to re-run

8. **Print a 5-line summary** to chat.

This command is non-destructive — it only writes the report file. It does NOT modify tests or application code.
