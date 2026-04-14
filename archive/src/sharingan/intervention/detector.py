"""Detect when a test needs human intervention."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field


class InterventionReason(str, Enum):
    """Why human intervention is needed."""

    EMAIL_VERIFICATION = "email_verification"
    SMS_VERIFICATION = "sms_verification"
    CAPTCHA = "captcha"
    OAUTH_REDIRECT = "oauth_redirect"
    PAYMENT = "payment"
    MFA = "mfa"
    TERMS_ACCEPTANCE = "terms_acceptance"
    UNKNOWN_MODAL = "unknown_modal"
    UNKNOWN = "unknown"


class InterventionRequest(BaseModel):
    """A request for human intervention during a test."""

    reason: InterventionReason = Field(description="Why intervention is needed")
    test_name: str = Field(description="Name of the test that needs help")
    current_url: str = Field(description="URL where the test is stuck")
    page_title: str = Field(default="", description="Title of the current page")
    visible_text: str = Field(default="", description="Visible text snippet for context")
    screenshot_path: str = Field(default="", description="Path to a screenshot of the page")
    instructions: str = Field(description="Instructions for the human to resolve the issue")


# Patterns that indicate different intervention reasons
INTERVENTION_PATTERNS: list[tuple[re.Pattern[str], InterventionReason, str]] = [
    (
        re.compile(r"verify.*email|check.*inbox|confirmation.*email|click.*link.*email", re.IGNORECASE),
        InterventionReason.EMAIL_VERIFICATION,
        "Check the email inbox for a verification link, click it, then run /sharingan-resume.",
    ),
    (
        re.compile(r"verify.*phone|sms.*code|text.*code|verification.*code", re.IGNORECASE),
        InterventionReason.SMS_VERIFICATION,
        "Enter the SMS verification code from your phone, then run /sharingan-resume.",
    ),
    (
        re.compile(r"captcha|recaptcha|i'?m not a robot|hcaptcha", re.IGNORECASE),
        InterventionReason.CAPTCHA,
        "Solve the CAPTCHA manually, then run /sharingan-resume.",
    ),
    (
        re.compile(r"continue with google|sign in with google|oauth|authorize", re.IGNORECASE),
        InterventionReason.OAUTH_REDIRECT,
        "Complete the OAuth flow manually, then run /sharingan-resume.",
    ),
    (
        re.compile(r"payment|credit card|stripe|checkout|billing", re.IGNORECASE),
        InterventionReason.PAYMENT,
        "This test hit a payment flow. Use Stripe test cards (4242 4242 4242 4242) and resume.",
    ),
    (
        re.compile(r"two.?factor|2fa|authenticator|totp|one.?time.?password", re.IGNORECASE),
        InterventionReason.MFA,
        "Enter the MFA code from your authenticator app, then run /sharingan-resume.",
    ),
    (
        re.compile(r"accept.*terms|agree.*terms|terms.*service|privacy.*policy", re.IGNORECASE),
        InterventionReason.TERMS_ACCEPTANCE,
        "Accept the terms of service, then run /sharingan-resume.",
    ),
]


def detect_intervention_needed(
    visible_text: str,
    test_name: str,
    current_url: str,
    page_title: str = "",
    screenshot_path: str = "",
) -> InterventionRequest | None:
    """Detect whether a test needs human intervention based on page content.

    Scans the visible text on the page for patterns that indicate
    a human-only step (email verification, CAPTCHA, OAuth, etc.).

    Args:
        visible_text: Text visible on the page.
        test_name: Name of the running test.
        current_url: URL of the current page.
        page_title: Page title.
        screenshot_path: Path to a screenshot of the page state.

    Returns:
        InterventionRequest if human help is needed, None otherwise.
    """
    for pattern, reason, instructions in INTERVENTION_PATTERNS:
        if pattern.search(visible_text) or pattern.search(page_title):
            return InterventionRequest(
                reason=reason,
                test_name=test_name,
                current_url=current_url,
                page_title=page_title,
                visible_text=_truncate(visible_text, 500),
                screenshot_path=screenshot_path,
                instructions=instructions,
            )

    return None


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
