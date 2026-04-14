# DEPRECATED: pip package

The `sharingan-autotest` pip package (v0.1, v0.2) is **deprecated** as of v0.3.

## What changed

v0.1 and v0.2 shipped as a Python package with helper modules and a slash command. The slash command described what to do, but the Python code never actually ran during a Playwright execution — so the human-in-the-loop modules were dormant code that never got triggered.

In v0.3, Sharingan is **pure Claude Code skill**. The slash command IS the product. No Python, no pip, no PyPI uploads, no version bumps. Distribution is `git clone` via `install.sh`.

The pip package is still on PyPI for old users, but it won't be updated. The Python modules (`discover/`, `generate/`, `intervention/`, etc.) are preserved in `archive/` for reference.

## Migration

If you installed via:

```bash
pip install sharingan-autotest
```

Uninstall it:

```bash
pip uninstall sharingan-autotest
```

Then install v0.3:

```bash
curl -fsSL https://raw.githubusercontent.com/ctoapplymatic/sharingan/main/install.sh | bash
```

Your slash commands at `~/.claude/commands/sharingan*.md` will be replaced by symlinks to the new versions. Existing tests in your projects' `tests/sharingan/` directories are not affected — you can re-run them with the v0.3 commands.

## Why the redesign

The v0.2 promise was "human-in-the-loop testing". The v0.2 reality was: the LLM (Claude Code) running a slash command tried to find clever workarounds (reading `seed.py`, hardcoding credentials, injecting localStorage) instead of actually pausing and asking the user to log in. The Python intervention modules existed but had no way to interrupt a Playwright subprocess.

v0.3 does the human-in-the-loop properly:
1. The slash command launches a real Chromium window via `scripts/auth-capture.js`
2. The script polls a signal file
3. The user takes as long as they need to log in, then says "done" in Claude Code chat
4. Claude Code touches the signal file
5. The script captures `storageState` and exits
6. All authenticated tests reuse the captured session

The user's password is never seen by the agent. The session is captured the same way a browser captures it.
