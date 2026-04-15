<div align="center">

<img src="assets/sharingan.svg" alt="Sharingan" width="220">

```
   ____   _   _    _    ____  ___ _   _  ____    _    _   _
  / ___| | | | |  / \  |  _ \|_ _| \ | |/ ___|  / \  | \ | |
  \___ \ | |_| | / _ \ | |_) || ||  \| | |  _  / _ \ |  \| |
   ___) ||  _  |/ ___ \|  _ < | || |\  | |_| |/ ___ \| |\  |
  |____/ |_| |_/_/   \_\_| \_\___|_| \_|\____/_/   \_\_| \_|
```

### Zero-config end-to-end testing for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-FFD700?style=for-the-badge)](https://claude.com/claude-code)
[![Version](https://img.shields.io/badge/version-0.3.0-blueviolet?style=for-the-badge)](https://github.com/ctoapplymatic/sharingan/releases)
[![Built with](https://img.shields.io/badge/Built%20with-Playwright-2EAD33?style=for-the-badge&logo=playwright)](https://playwright.dev)

</div>

**Type `/sharingan` in any web project and an autonomous QA agent walks through your codebase, opens a real browser for you to log in, generates a complete Playwright test suite based on what it finds, runs it, diagnoses failures as test bugs vs application bugs, patches your code when bugs are real, and writes a markdown report.** No tests to write. No Playwright knowledge required. No credentials shared with the agent.

The hard part of testing isn't writing assertions — it's **knowing what to test**, **getting through your auth flow**, **figuring out why something failed**, and **organizing the output**. Sharingan does all four. The only thing it asks of you is to log in once, manually, in a browser window it opens for you. That's it.

<table>
<tr><td><b>Sees your code</b></td><td>Scans your repo to find every route, API endpoint, form, and auth-protected page. Works with Next.js (App + Pages router), React, FastAPI, Express, and Django. No config files, no test specs, no fixture wiring — Sharingan reads what's there.</td></tr>
<tr><td><b>Logs in like a human</b></td><td>When auth is needed, Sharingan opens a real Chromium window pointed at your login page. You complete the flow yourself — Auth0, OAuth, MFA, email verification, CAPTCHA, anything a human can do. When you reach your dashboard, Sharingan captures the session and reuses it for every authenticated test. <b>Your password is never seen by the agent.</b></td></tr>
<tr><td><b>Generates the whole suite</b></td><td>From the discovered routes, Sharingan generates ~30-50 Playwright tests across 6 categories: navigation, permission guards, form validation, authenticated flows, visual regression baselines, performance metrics, and OpenAPI schema validation. The tests use real best practices — semantic locators, storage-state reuse, font/CSS readiness waits, no flaky timeouts.</td></tr>
<tr><td><b>Diagnoses, then fixes</b></td><td>When a test fails, Sharingan reads the trace + the source code for the failing route, decides whether it's a test bug (wrong selector, timing) or an application bug (broken validation, missing route, race condition), and patches the right file. Fixes are minimal and never bypass safety — `.env`, lock files, migrations, and `node_modules/` are off-limits.</td></tr>
<tr><td><b>Organizes everything</b></td><td>Screenshots are flattened from Playwright's hashed directories into a clean `screenshots/` folder named by test execution order. The final `SHARINGAN_REPORT.md` lists every bug found with file, severity, and a code-snippet fix. The HTML report links every assertion to the trace viewer.</td></tr>
<tr><td><b>Pure Claude Code skill</b></td><td>No pip install, no npm package, no PyPI uploads. Sharingan is a single git repo with `commands/*.md` (the slash command prompts) and `scripts/*.js` (the Playwright orchestration). Distribution is one curl-pipe-bash. The intelligence lives in the LLM via the prompt — there's no compiled Python pretending to be smart.</td></tr>
</table>

---

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/ctoapplymatic/sharingan/main/install.sh | bash
```

Clones to `~/.sharingan/`, symlinks slash commands into `~/.claude/commands/`, installs Playwright + Chromium for the auth-capture script. Re-run the same command to update.

**Requirements:** [Claude Code](https://claude.com/claude-code), Node 18+, a project with a running dev server.

---

## Usage

In Claude Code, inside your project directory:

```
/sharingan
```

That's it. The agent walks through everything. The flow:

1. *"I see you use Next.js + FastAPI with Auth0. Found 19 frontend routes and 38 API endpoints. I'll generate ~40 tests across navigation, forms, authenticated flows, visual regression, performance, and API schema validation. OK to proceed?"*
2. You say **yes**.
3. *"I'm opening a Chromium window at http://localhost:3000/login. Please log in there however you normally would — Auth0, MFA, email verification, all OK. Take your time. When you're back at the dashboard, just say 'done' here in chat."*
4. Browser opens. You log in like a normal human.
5. You say **done** (or just navigate to /dashboard — Sharingan auto-detects).
6. Sharingan captures your session, generates and runs the test suite, diagnoses failures, fixes bugs in your application code, and writes `SHARINGAN_REPORT.md`.

Total time: 5–15 minutes depending on app size and how long you take to log in.

---

## How the human-in-the-loop actually works

This is the part most testing tools punt on. Here's exactly what happens when Sharingan needs auth:

```
┌───────────────────┐    ┌────────────────────┐    ┌──────────────────┐
│  Claude Code:     │    │  Real Chromium     │    │  You:            │
│  /sharingan       │    │  (headed mode)     │    │  reading chat    │
└─────────┬─────────┘    └──────────┬─────────┘    └────────┬─────────┘
          │                         │                       │
          │  spawn auth-capture.js  │                       │
          │────────────────────────▶│                       │
          │                         │                       │
          │                         │  navigate to /login   │
          │                         │──────────────────────▶│
          │                         │                       │
          │  "browser open, please  │                       │
          │   log in & say 'done'"  │                       │
          │─────────────────────────────────────────────────▶│
          │                         │                       │
          │                         │  (you log in via Auth0,
          │                         │   email verify, MFA,
          │                         │   whatever — at your pace)
          │                         │                       │
          │                "done"   │                       │
          │◀─────────────────────────────────────────────────│
          │                         │                       │
          │  touch signal-file      │                       │
          │────────────────────────▶│                       │
          │                         │                       │
          │                         │  capture storageState │
          │                         │  close browser, exit  │
          │                         │                       │
          │  resume test generation │                       │
          ▼                         ▼                       ▼
```

Sharingan **never sees your password**. It only captures the cookies + localStorage that result from your successful login. The same way a browser captures a session.

If your environment can't open a browser window (remote SSH, headless CI, bare server), there's a **paste-mode fallback**: log in elsewhere, copy your cookies from DevTools, paste them in chat. Same end result.

---

## Slash commands

| Command | Description |
|---|---|
| `/sharingan` | Full autonomous flow: discover → auth → generate → run → diagnose → fix → report |
| `/sharingan-scan` | Discovery only. Outputs `SHARINGAN_PLAN.md`. Read-only — no tests generated. |
| `/sharingan-fix` | Diagnose and fix failures from the last run. Useful after manual edits. |
| `/sharingan-report` | Regenerate `SHARINGAN_REPORT.md` from the current state of `tests/sharingan/`. |
| `/sharingan-resume` | Continue after a manual step (e.g., the headed browser login). |

---

## What Sharingan generates

```
your-project/
├── tests/sharingan/
│   ├── playwright.config.ts           ← 5 projects: unauth, auth, visual, perf, schema
│   ├── helpers/wait-for-styled.ts     ← waits for CSS+fonts (critical for dev mode)
│   ├── .auth/storage-state.json       ← captured from your manual login
│   ├── unauthenticated/
│   │   ├── navigation.spec.ts         ← every public page loads
│   │   ├── permission.spec.ts         ← protected routes redirect
│   │   ├── api-public.spec.ts         ← public endpoints work
│   │   └── form-validation.spec.ts    ← signup/form validation via backend
│   ├── authenticated/
│   │   ├── pages.spec.ts              ← every protected page reachable
│   │   └── api.spec.ts                ← authenticated endpoints
│   ├── visual/regression.spec.ts      ← pixel-diff snapshots
│   ├── perf/vitals.spec.ts            ← FCP, LCP, load time
│   ├── schema/api-schema.spec.ts      ← validates against /openapi.json
│   ├── screenshots/                   ← organized by test, browseable
│   │   ├── 01-navigation-home.png
│   │   ├── 02-permission-dashboard.png
│   │   ├── 03-authenticated-dashboard.png
│   │   └── ...
│   └── html-report/                   ← Playwright's interactive report
└── SHARINGAN_REPORT.md                ← the executive summary
```

---

## Supported frameworks

| Framework | Detection | Discovery |
|---|---|---|
| Next.js (App Router) | `package.json` → `next` | `src/app/` directory tree, route groups respected |
| Next.js (Pages Router) | `package.json` → `next` | `pages/` directory |
| React (Vite/CRA) | `package.json` → `react` (no `next`) | `<Route>` JSX |
| FastAPI | `requirements.txt` / `pyproject.toml` → `fastapi` | `@app.get` / `@router.post` decorators |
| Django | `manage.py` + `django` in deps | `urls.py` patterns |
| Express.js | `package.json` → `express` | `app.get(`/`router.get(` calls |

**Auth providers detected:** Auth0, NextAuth, Clerk, Supabase, custom JWT, session cookies.

---

## Comparison

| Tool | Auto-discovers tests | Generates tests | Headed pause for human auth | Diagnoses bugs | Fixes app code | Distribution |
|---|:-:|:-:|:-:|:-:|:-:|---|
| **Sharingan** | ✓ | ✓ | ✓ | ✓ | ✓ | Claude Code skill |
| Playwright Codegen | ✗ | partial (record) | ✓ (`page.pause()`) | ✗ | ✗ | npm |
| Playwright Agents | ✗ | ✗ | ✗ | partial | ✗ | npm |
| Cypress Studio | ✗ | partial | ✗ | ✗ | ✗ | npm |
| Selenium IDE | ✗ | partial (record) | ✗ | ✗ | ✗ | browser ext |

The pause-for-human-login part is what makes the rest of it feasible. Without it, every other "AI testing tool" hits a wall the moment your app uses Auth0 or any OAuth provider — and they either fail silently or take ugly shortcuts. Sharingan stops, asks, and waits.

---

## Contributing

Sharingan is two things: **prompts** (`commands/*.md`) and **scripts** (`scripts/*.js`). To hack on it:

```bash
git clone https://github.com/ctoapplymatic/sharingan
cd sharingan
SHARINGAN_INSTALL_DIR=$(pwd) ./install.sh    # symlinks your local copy
# edit commands/sharingan.md or scripts/auth-capture.js
# then run /sharingan in any project to test
```

PRs welcome. The prompt in `commands/sharingan.md` is the soul of the project — improvements there are the highest-impact contribution.

---

## License

[MIT](LICENSE).
