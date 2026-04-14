# Sharingan

**The eye that sees all bugs.**

Sharingan is an autonomous QA agent for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Type `/sharingan` in any web project and it will:

1. **Discover** every route, API endpoint, form, and auth-protected page in your codebase
2. **Pause and ask you to log in** by opening a real Chromium window — handles Auth0, OAuth, MFA, email verification, CAPTCHA, anything a human can do
3. **Generate** Playwright tests for navigation, permission guards, forms, authenticated flows, visual regression, performance, and API schema validation
4. **Run** them against your live dev environment
5. **Diagnose** failures as test bugs vs application bugs
6. **Fix** the application code when bugs are real
7. **Report** everything in `SHARINGAN_REPORT.md` with screenshots, bug fixes, and performance metrics

**No tests to write. No Playwright knowledge required. No credentials shared with the agent.** You log in once via the headed browser; Sharingan captures the session and reuses it.

---

## Why use this over plain Playwright?

Playwright is a great library, but it makes you do all the work: write the config, learn fixtures and projects, write each test, debug each failure, write the report. Sharingan does all of that **based on what's actually in your code**.

| What you'd do manually with Playwright | What Sharingan does for you |
|---|---|
| Read Playwright docs, set up `playwright.config.ts`, learn projects/fixtures | Generates the config |
| Inspect your codebase to figure out what to test | Scans the code, lists every route worth testing |
| Write 50+ test files by hand | Generates them from discovered routes |
| Manually write `auth.setup.ts`, figure out where to save storage state | Detects auth method, opens the right browser at the right URL |
| Run tests, see red, open the trace viewer, debug | Reads the trace, diagnoses test bug vs app bug, **patches the app** |
| Sift through Playwright's hashed screenshot dirs | Organizes screenshots by test name in a clean folder |
| Write a report manually | Generates a markdown report with bugs, fixes, screenshots |

The headed-browser pause is the *escape hatch* when automation can't proceed. Everything else — discovery, generation, diagnosis, fixing, reporting — is fully autonomous.

---

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/ctoapplymatic/sharingan/main/install.sh | bash
```

This clones to `~/.sharingan/` and symlinks the slash commands into `~/.claude/commands/`. Updates: re-run the same command.

**Requirements:**
- [Claude Code](https://claude.com/claude-code) installed and working
- Node 18+ (for Playwright)
- A web project with a running dev server

That's it. **No pip, no npm package, no PyPI.** Sharingan is a pure Claude Code skill — distribution is git, intelligence is the LLM.

---

## Usage

In Claude Code, inside your project directory:

```
/sharingan
```

Sharingan will walk you through everything. The flow looks like this:

1. *"I see you use Next.js + FastAPI with Auth0. I found 19 frontend routes and 38 API endpoints. I'll generate ~40 tests across navigation, forms, authenticated flows, visual regression, performance, and API schema validation. OK to proceed?"*
2. You say **yes**.
3. *"I'm opening a Chromium window at http://localhost:3000/login. Please log in there however you normally would — Auth0, email verification, MFA, all OK. Take your time. When you're back at the dashboard, just say 'done' here."*
4. The browser window opens. You log in like a human.
5. You say **done**.
6. Sharingan captures your session, generates and runs the tests, diagnoses failures, fixes bugs in your application code, and writes a report.

Total time: 5–15 minutes depending on your app size, mostly spent waiting for you to log in.

## Slash commands

| Command | Description |
|---|---|
| `/sharingan` | Full autonomous flow: discover → auth → generate → run → fix → report |
| `/sharingan-scan` | Discovery only — outputs `SHARINGAN_PLAN.md`, no tests generated |
| `/sharingan-fix` | Diagnose and fix failures from the last run |
| `/sharingan-report` | Regenerate `SHARINGAN_REPORT.md` from current state |
| `/sharingan-resume` | Continue after manual intervention (e.g., browser login) |

---

## What Sharingan generates

```
your-project/
├── tests/sharingan/
│   ├── playwright.config.ts          ← 5 projects: unauth, auth, visual, perf, schema
│   ├── helpers/wait-for-styled.ts    ← waits for CSS+fonts (critical for dev mode)
│   ├── .auth/storage-state.json      ← captured from your manual login
│   ├── unauthenticated/
│   │   ├── navigation.spec.ts        ← every public page loads
│   │   ├── permission.spec.ts        ← protected routes redirect
│   │   ├── api-public.spec.ts        ← public API endpoints work
│   │   └── form-validation.spec.ts   ← signup/form validation via backend
│   ├── authenticated/
│   │   ├── pages.spec.ts             ← protected pages reachable as logged-in user
│   │   └── api.spec.ts               ← authenticated API endpoints
│   ├── visual/
│   │   └── regression.spec.ts        ← pixel-diff snapshots
│   ├── perf/
│   │   └── vitals.spec.ts            ← FCP, LCP, load time
│   ├── schema/
│   │   └── api-schema.spec.ts        ← validates against /openapi.json
│   ├── screenshots/                  ← named by test, browseable
│   │   ├── 01-navigation-home.png
│   │   ├── 02-navigation-login.png
│   │   ├── 03-permission-dashboard.png
│   │   ├── 04-authenticated-dashboard.png    ← the real signed-in dashboard
│   │   └── ...
│   └── html-report/                  ← Playwright's interactive report
└── SHARINGAN_REPORT.md               ← the executive summary
```

---

## How the human-in-the-loop works

This is the differentiator. When Sharingan needs authentication, it does NOT:
- Read your `.env` files for credentials
- Guess test user passwords from `seed.py`
- Inject tokens into `localStorage`
- Bypass your auth provider

It does:

1. Opens a real Chromium window using Playwright in headed mode
2. Navigates to your login page
3. **Hands you the keyboard**
4. Polls a signal file every 500ms
5. When you say "done" in chat, Sharingan touches the signal file
6. The browser script captures `storageState` (cookies + localStorage)
7. Closes the browser
8. Every authenticated test now reuses that session

You can take 30 seconds or 30 minutes. You can do email verification, MFA, OAuth consent screens, CAPTCHA — anything a human can do, Sharingan can wait for.

If your dev environment can't open a browser window (remote SSH server, headless CI), Sharingan falls back to **paste mode**: you log in elsewhere, copy your cookies from DevTools, paste them in chat. Same end result.

**Sharingan never sees your password.** It only sees the resulting session cookie.

---

## Supported frameworks

| Framework | Detection | Discovery |
|---|---|---|
| Next.js (App Router) | `package.json` → `next` | `src/app/` directory tree |
| Next.js (Pages Router) | `package.json` → `next` | `pages/` directory |
| React (Vite/CRA) | `package.json` → `react` (no `next`) | `<Route>` JSX |
| FastAPI | `requirements.txt` / `pyproject.toml` → `fastapi` | `@app.get` decorators |
| Django | `manage.py` + `django` in deps | `urls.py` |
| Express.js | `package.json` → `express` | `app.get(`/`router.get(` |

Auth providers detected:
- Auth0 (`@auth0/auth0-react`, `@auth0/nextjs-auth0`)
- NextAuth (`next-auth`)
- Clerk (`@clerk/*`)
- Supabase (`@supabase/*`)
- Custom JWT
- Session cookies

---

## Examples

The `examples/sample-app/` directory contains a tiny Next.js + FastAPI app with three intentional bugs for Sharingan to find. Use it to see Sharingan in action without touching your real project.

---

## Comparison

| Tool | Auto-discovers tests | Generates tests | Headed browser pause | Diagnoses bugs | Fixes app code | Distribution |
|---|---|---|---|---|---|---|
| **Sharingan** | ✓ | ✓ | ✓ | ✓ | ✓ | Claude Code skill |
| Playwright Codegen | ✗ | partial (record) | ✓ (`page.pause()`) | ✗ | ✗ | npm |
| Playwright Agents | ✗ | ✗ | ✗ | partial | ✗ | npm |
| Cypress Studio | ✗ | partial | ✗ | ✗ | ✗ | npm |
| Ralph Loop | ✗ | ✗ | ✗ | ✗ | ✗ | manual |

Sharingan is the only one that does **all** of: discovery, generation, headed pause, diagnosis, fixing, and shipping as a Claude Code skill.

---

## Why "Sharingan"?

The Sharingan eye from Naruto can see through illusions, copy techniques, and predict the opponent's next move. Like its namesake, this tool sees through the surface of your application to find hidden bugs, copies testing patterns from your own code, and anticipates where failures will occur.

---

## Versioning

| Version | Notes |
|---|---|
| **v0.3.0** (current) | Pure Claude Code skill. No pip package. Headed browser auth. |
| v0.2.0 | Hybrid pip package + skill. Deprecated — was missing real human-in-the-loop. |
| v0.1.0 | Initial Python + slash command. Deprecated. |

The PyPI package `sharingan-autotest` (v0.1, v0.2) is **deprecated**. New users should use the install script above.

---

## Contributing

PRs welcome. The whole product is `commands/*.md` + `scripts/*.js`. To test changes:

```bash
git clone https://github.com/ctoapplymatic/sharingan
cd sharingan
# Edit commands/sharingan.md or scripts/auth-capture.js
SHARINGAN_INSTALL_DIR=$(pwd) ./install.sh  # symlinks your local copy
```

Then run `/sharingan` in a project to test.

---

## License

MIT. See [LICENSE](LICENSE).
