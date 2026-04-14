"""Playwright auth fixture generation for authenticated flow tests."""

from __future__ import annotations

from sharingan.auth.test_users import TestUserCredentials
from sharingan.config import SharinganConfig


def generate_auth_setup_file(config: SharinganConfig, creds: TestUserCredentials) -> str:
    """Generate a Playwright auth.setup.ts file that logs in and saves storage state.

    This runs once before authenticated tests. It:
    1. Tries to log in with the test user
    2. If login fails and auto_create is True, signs up the user first
    3. Saves cookies/localStorage to a storage state file
    4. Authenticated tests reuse this state via storageState option

    Args:
        config: Sharingan configuration.
        creds: Test user credentials.

    Returns:
        TypeScript content for auth.setup.ts.
    """
    storage_state = str(config.get_storage_state_path().relative_to(config.get_test_output_path()))
    signup_route = config.test_user.signup_route
    login_route = config.test_user.login_route
    auto_create = "true" if config.test_user.auto_create else "false"

    return f'''import {{ test as setup, expect }} from "@playwright/test";
import path from "path";
import fs from "fs";

const authFile = path.join(__dirname, "{storage_state}");
const email = "{creds.email}";
const password = process.env.SHARINGAN_TEST_PASSWORD || "{creds.password}";
const BASE_URL = "{config.base_url}";
const AUTO_CREATE = {auto_create};

setup("authenticate", async ({{ page }}) => {{
  // Ensure auth directory exists
  const authDir = path.dirname(authFile);
  if (!fs.existsSync(authDir)) {{
    fs.mkdirSync(authDir, {{ recursive: true }});
  }}

  // Attempt login first
  await page.goto(`${{BASE_URL}}{login_route}`);
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).first().fill(password);
  await page.getByRole("button", {{ name: /log in|sign in/i }}).click();

  // Wait a moment for navigation or error
  await page.waitForTimeout(1500);

  const url = page.url();
  const isLoggedIn = !url.includes("/login") && !url.includes("/signin");

  if (!isLoggedIn && AUTO_CREATE) {{
    // Login failed — try to sign up
    await page.goto(`${{BASE_URL}}{signup_route}`);
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).first().fill(password);

    // Handle confirm password field if present
    const confirmField = page.getByLabel(/confirm password/i);
    if (await confirmField.count() > 0) {{
      await confirmField.fill(password);
    }}

    await page.getByRole("button", {{ name: /sign up|register|create account/i }}).click();
    await page.waitForTimeout(2000);

    // After signup, try to log in again
    if (page.url().includes("/login") || page.url().includes("/signin")) {{
      await page.getByLabel(/email/i).fill(email);
      await page.getByLabel(/password/i).first().fill(password);
      await page.getByRole("button", {{ name: /log in|sign in/i }}).click();
      await page.waitForTimeout(1500);
    }}
  }}

  // Verify we're actually logged in by checking for auth indicators
  const finalUrl = page.url();
  const stillOnAuth = finalUrl.includes("/login") || finalUrl.includes("/signin");

  if (stillOnAuth) {{
    // Check if there's an email verification screen — this needs human intervention
    const bodyText = await page.locator("body").textContent();
    if (bodyText && /verify|confirm.*email|check.*inbox/i.test(bodyText)) {{
      throw new Error(
        "SHARINGAN_NEEDS_HELP: Email verification required. " +
        "See SHARINGAN_NEEDS_HELP.md for instructions."
      );
    }}
    throw new Error("Sharingan could not authenticate — login failed and signup did not succeed.");
  }}

  // Save storage state for reuse in authenticated tests
  await page.context().storageState({{ path: authFile }});
}});
'''


def generate_playwright_config(config: SharinganConfig) -> str:
    """Generate a playwright.config.ts file with auth project setup.

    Args:
        config: Sharingan configuration.

    Returns:
        TypeScript content for playwright.config.ts.
    """
    return f'''import {{ defineConfig, devices }} from "@playwright/test";

export default defineConfig({{
  testDir: ".",
  timeout: {config.timeout_ms},
  expect: {{
    timeout: 10000,
    toHaveScreenshot: {{
      maxDiffPixels: {config.visual.max_diff_pixels},
      threshold: {config.visual.threshold},
    }},
  }},
  use: {{
    baseURL: "{config.base_url}",
    screenshot: "{'on' if config.screenshot_every_step else 'only-on-failure'}",
    trace: "on-first-retry",
    video: "retain-on-failure",
  }},
  reporter: [
    ["html", {{ outputFolder: "playwright-report", open: "never" }}],
    ["json", {{ outputFile: "results.json" }}],
    ["list"],
  ],
  projects: [
    {{
      name: "setup",
      testMatch: /.*\\.setup\\.ts/,
    }},
    {{
      name: "unauthenticated",
      testMatch: /unauthenticated\\/.*\\.spec\\.ts/,
      use: {{ ...devices["Desktop Chrome"] }},
    }},
    {{
      name: "authenticated",
      testMatch: /authenticated\\/.*\\.spec\\.ts/,
      use: {{
        ...devices["Desktop Chrome"],
        storageState: ".auth/storage-state.json",
      }},
      dependencies: ["setup"],
    }},
  ],
}});
'''
