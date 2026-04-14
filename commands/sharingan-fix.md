# /sharingan-fix — Diagnose and Fix Failures from Last Run

Read the most recent test results and attempt to fix failures. Use this after `/sharingan` if you want to re-attempt fixes without re-discovering or re-generating tests. Or run it standalone after manual edits to verify everything still passes.

## Steps

1. **Find the most recent run:**
   - Look for `tests/sharingan/results.json`
   - If not found, ask the user to run `/sharingan` first

2. **Read the results JSON** and list every failed test (excluding `test.fail()` markers which are intentional).

3. **Run the suite once first** to get fresh failures (in case anything changed):
   ```bash
   cd tests/sharingan && npx playwright test 2>&1
   ```

4. **For each real failure:**

   a. **Read the error context:**
      ```bash
      find tests/sharingan/test-results -name "error-context.md" | xargs grep -l "<test name>"
      ```
      Then `cat` the file.

   b. **Diagnose:** test bug or app bug?
      - **Test bug indicators:** "locator resolved to 0 elements", "timeout waiting for", strict mode violations, wrong selectors. Fix by editing the test file.
      - **App bug indicators:** 500 errors, 404s on routes that should exist, TypeErrors in the app, broken validation, race conditions. Fix by editing application source.
      - **Environment indicators:** ECONNREFUSED, ENOTFOUND, port conflicts, missing modules. Tell the user, don't try to fix.

   c. **Read the source code** for the file you're about to fix. Use `Read` on at least 30 lines of context around the issue.

   d. **Apply the fix** with `Edit`. Be minimal — only change what's needed. Never:
      - Modify `.env*`, lock files, migrations, `node_modules/`
      - Delete data or drop tables
      - Skip auth checks to make a test pass
      - Add `// @ts-ignore` or similar suppressions

   e. **Re-run only that test:**
      ```bash
      cd tests/sharingan && npx playwright test --grep "<exact test name>" 2>&1
      ```

   f. **If it passes:** record the fix in your fix log.
   g. **If it still fails:** try again, but at most 3 attempts per test. After 3, mark the test with `test.fail(true, "BUG: <description>")` and add it to `SHARINGAN_NEEDS_HELP.md`.

5. **Re-run the full suite** to confirm nothing regressed:
   ```bash
   cd tests/sharingan && npx playwright test 2>&1 | tail -10
   ```

6. **Update `SHARINGAN_REPORT.md`** with:
   - What was fixed (file, before/after summary)
   - What still needs human review
   - New test results table

## Safety

- NEVER bypass auth to "fix" an authenticated test
- NEVER hardcode secrets or credentials in test files
- NEVER swallow exceptions to make tests pass
- If you can't figure out a fix, write to `SHARINGAN_NEEDS_HELP.md` and ask the user
