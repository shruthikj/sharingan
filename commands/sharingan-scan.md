# /sharingan-scan — Discovery Only

Scan the user's project to discover routes, endpoints, forms, and auth methods. Print a test plan. **Do NOT generate or run any tests.** This is a dry run.

Useful for: previewing what `/sharingan` will do, generating a test plan for review, or just understanding the scope of an unfamiliar codebase.

## Steps

1. **Verify you're in a project root** (`pwd`, look for `package.json` or `pyproject.toml`).

2. **Detect frameworks** by reading config files:
   - `package.json` → look for `next`, `react`, `vue`, `express`, `@auth0/*`
   - `requirements.txt` / `pyproject.toml` → look for `fastapi`, `django`, `flask`
   - `manage.py` → Django

3. **Discover frontend routes:**
   - Next.js App Router: scan `src/app/` or `app/` for `page.tsx`. Remember `(group)` directories don't add to URL.
   - Next.js Pages Router: scan `pages/`.
   - React: grep for `<Route path="..."` in JSX/TSX files.
   - For each route, note: path, has-form (look for `<form>` or `onSubmit`), needs-auth (look for `useSession`, `useAuth`, middleware match).

4. **Discover backend endpoints:**
   - FastAPI: grep `@app.get|post|put|patch|delete` and `@router.get|post|...`
   - Express: grep `app.get|post|...` and `router.get|post|...`
   - Django: read `urls.py`

5. **Detect auth method:**
   - Check `package.json` for `@auth0/*`, `next-auth`, `@clerk/*`, `@supabase/*`
   - Check for `middleware.ts` and what it protects
   - Check `.env.example` for `AUTH0_*`, `NEXTAUTH_*`, `CLERK_*` keys
   - Look for `/login`, `/signin`, `/signup` page files

6. **Detect API spec:**
   - Try `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/openapi.json` (and other common paths)
   - If 200, fetch and report the title and number of paths

7. **Write `SHARINGAN_PLAN.md`** at the project root:

```markdown
# Sharingan Test Plan

*Generated: <timestamp>*
*This is a dry run — no tests have been generated.*

## Detected stack

- Frontend: <framework + version>
- Backend: <framework + version>
- Auth: <method>
- OpenAPI: <yes/no, path>

## Discovered routes

### Frontend (N pages)

| Path | Type | Has form | Needs auth | Source file |
|---|---|---|---|---|
| / | page | no | no | src/app/page.tsx |
| /login | page | yes | no | src/app/login/page.tsx |
| /dashboard | page | no | yes | src/app/(app)/dashboard/page.tsx |
| ... |

### API (N endpoints)

| Method | Path | Auth | Source file |
|---|---|---|---|
| GET | /api/v1/health | no | backend/app/api/v1/health.py |
| POST | /api/v1/auth/login | no | backend/app/api/v1/auth.py |
| GET | /api/v1/auth/me | yes | backend/app/api/v1/auth.py |
| ... |

## Tests that would be generated

| Category | Count | Requires |
|---|---|---|
| Navigation (public pages) | X | dev server running |
| Permission guards | Y | dev server running |
| Form validation (backend) | Z | backend running |
| Public API | A | backend running |
| Authenticated pages | B | dev server running + you log in via headed browser |
| Authenticated API | C | dev server running + you log in via headed browser |
| Visual regression | D | dev server running |
| Performance metrics | E | dev server running |
| API schema validation | F | OpenAPI spec available |
| **Total** | **N** | |

## Auth method requires human-in-the-loop

[If Auth0 or similar:]
This project uses <method>. When you run `/sharingan`, Sharingan will:
1. Open a real Chromium window at `http://localhost:3000/login`
2. Wait for you to log in (handles Auth0, OAuth, email verification, MFA)
3. Capture your session and reuse it for all authenticated tests

You don't need to share your password with Sharingan.

## To run

When you're ready, type `/sharingan` to execute this plan.
```

8. **Print a 5-line summary to chat** with the totals and next-step prompt.

This command is read-only. It MUST NOT:
- Create test files
- Modify any application code
- Open a browser
- Read credentials from `.env*` (just look for variable names, not values)
- Make destructive changes
