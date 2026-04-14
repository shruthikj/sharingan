# /sharingan-resume — Resume After Manual Step

Resume a paused Sharingan run. Use this when:
- Sharingan opened a browser for you to log in and you're now ready to continue
- Sharingan wrote `SHARINGAN_NEEDS_HELP.md` asking for human input
- A previous run was interrupted and you want to pick up where it left off

## Steps

1. **Look for `SHARINGAN_NEEDS_HELP.md`** at the project root. Read it to understand what Sharingan was waiting for.

2. **Look for any background `auth-capture.js` process.** Check with `pgrep -fa auth-capture.js`. If one is running:
   - There should be a signal file mentioned in `SHARINGAN_NEEDS_HELP.md` (or use `ls /tmp/sharingan-auth-go-*` to find it).
   - Touch the signal file to unblock it: `touch <signal-file>`
   - Wait for the background process to complete (it captures storageState then exits within a second).
   - Verify the storage state file was created: `cat tests/sharingan/.auth/storage-state.json | head`

3. **If no background process is running** (e.g., terminal was closed and restarted):
   - The browser session was lost. Re-run `/sharingan` from the auth phase.
   - OR ask the user if they'd like to use paste mode (manual cookie paste).

4. **Continue the original `/sharingan` flow** from where it left off:
   - If the auth was the only blocker → continue to Phase 3 (generate tests) and onward
   - If the failure was a fix attempt → re-run the failing test, diagnose, retry
   - If the user has manually fixed something → run the full test suite again

5. **Delete `SHARINGAN_NEEDS_HELP.md`** when resolved. Do NOT delete it if the issue isn't actually resolved.

## --skip flag

If the user runs `/sharingan-resume --skip`, mark the blocker as "needs human review", record it in `SHARINGAN_REPORT.md`, and continue with the rest of the flow without resolving it.

## Safety

- Never store credentials, verification codes, MFA codes, or anything else from the manual step. Sharingan only captures the resulting session cookie.
- If the user's auth flow created a real test user account in their database, that's their responsibility to clean up. Don't try to "tidy up" by deleting users.
