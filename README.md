# Sharingan

**The eye that sees all bugs.**

Sharingan is an autonomous testing agent for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). It discovers what to test in your web application, generates and runs Playwright end-to-end tests, diagnoses whether failures are test bugs or **application bugs**, fixes the application code, and re-runs until everything passes.

One command: `/sharingan`

---

## How It Works

Sharingan runs a 7-step autonomous loop:

```
DISCOVER → GENERATE → RUN → DIAGNOSE → FIX → LOOP → REPORT
    │          │        │        │         │      │       │
    │          │        │        │         │      │       └─ SHARINGAN_REPORT.md
    │          │        │        │         │      └─ Repeat steps 3-5
    │          │        │        │         └─ Edit app or test code
    │          │        │        └─ Test bug? or App bug?
    │          │        └─ Playwright with JSON reporter
    │          └─ Playwright test files
    └─ Scan routes, endpoints, forms
```

1. **Discover** — Detects your framework (Next.js, React, FastAPI, Express, Django) and scans the codebase for routes, API endpoints, forms, and auth-protected pages.
2. **Generate** — Creates Playwright e2e tests for auth flows, navigation, form validation, API endpoints, permission guards, and basic accessibility.
3. **Run** — Executes all tests with JSON reporting and failure screenshots.
4. **Diagnose** — For each failure, reads the test code *and* the application source to determine: is this a **test bug** (wrong selector, timing) or an **application bug** (missing route, broken logic)?
5. **Fix** — Applies the fix to the correct file (test or app), with safety checks.
6. **Loop** — Re-runs failing tests. Max 3 attempts per test before marking as "needs human review."
7. **Report** — Generates `SHARINGAN_REPORT.md` with discovery stats, results table, bugs found, and items needing review.

## Key Differentiator

| Tool | Finds test bugs | Finds app bugs | Auto-fixes app | Framework-aware | Ships as slash command |
|------|:-:|:-:|:-:|:-:|:-:|
| Playwright Agents | Yes | No | No | No | No |
| Ralph Loop | - | - | - | No | No |
| QA Skills | - | - | No | Partial | Yes |
| **Sharingan** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

Sharingan doesn't just fix broken tests — it finds broken applications and fixes them too.

## Quick Start

### Install

```bash
pip install sharingan-testing
```

Or with uv:

```bash
uv pip install sharingan-testing-testing
```

Then initialize in your project:

```bash
cd your-project
sharingan init
```

This copies the slash commands into `.claude/commands/`.

### Install Playwright

If you don't already have Playwright set up:

```bash
npm init playwright@latest
npx playwright install chromium
```

### Use

In Claude Code, type:

```
/sharingan
```

That's it. Sharingan handles the rest.

## Slash Commands

| Command | Description |
|---------|-------------|
| `/sharingan` | Full autonomous loop: discover, test, diagnose, fix, report |
| `/sharingan-scan` | Discover routes only — outputs `SHARINGAN_PLAN.md` |
| `/sharingan-test` | Generate and run tests only — no auto-fixing |
| `/sharingan-fix` | Diagnose and fix failures from the last run |
| `/sharingan-report` | Regenerate report from the last run |

## Supported Frameworks

| Framework | Detection | Route Discovery |
|-----------|-----------|-----------------|
| Next.js (App Router) | `package.json` → `next` | `src/app/` directory structure |
| React (CRA/Vite) | `package.json` → `react` (no `next`) | `<Route path="...">` in JSX |
| FastAPI | `requirements.txt` → `fastapi` | `@app.get/post(...)` decorators |
| Express.js | `package.json` → `express` | `app.get/post(...)` calls |
| Django | `manage.py` + `django` in requirements | `path(...)` in `urls.py` |

## Configuration

Sharingan works with zero configuration. To customize, create a `sharingan.json` in your project root:

```json
{
  "base_url": "http://localhost:3000",
  "api_base_url": "http://localhost:8000",
  "max_fix_attempts": 3,
  "max_iterations": 5,
  "timeout_ms": 30000,
  "headless": true,
  "browser": "chromium"
}
```

## CLI

```bash
sharingan init              # Install slash commands in current project
sharingan scan --dir .      # Scan project and print discovered routes
sharingan report --dir .    # Generate report from last test run
```

## Sample App

The `examples/sample-app/` directory contains a Next.js + FastAPI app with 3 intentional bugs for demo purposes:

1. **Signup form** doesn't validate password confirmation
2. **Dashboard** is accessible without authentication
3. **Create item API** returns 500 on empty request body

Run Sharingan against it to see all three discovered and fixed.

## Development

```bash
git clone https://github.com/ctoapplymatic/sharingan.git
cd sharingan
pip install -e ".[dev]"
pytest
```

## Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Write tests for new functionality
4. Submit a PR

## Why "Sharingan"?

Named after the Sharingan eye from Naruto. The Sharingan can see through illusions, copy techniques, and predict an opponent's next move. Like its namesake, this tool sees through the surface of your application to find hidden bugs, copies testing patterns, and anticipates where failures will occur.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

Built by [Shruthi Krithika](https://github.com/shruthikj) at [Applymatic](https://applymatic.ai).
