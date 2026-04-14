"""Tests for the intervention module."""

from __future__ import annotations

from pathlib import Path

from sharingan.config import SharinganConfig
from sharingan.intervention.detector import (
    InterventionReason,
    detect_intervention_needed,
)
from sharingan.intervention.prompter import (
    clear_intervention_prompt,
    write_intervention_prompt,
)


class TestDetectInterventionNeeded:
    """Tests for detect_intervention_needed."""

    def test_detect_email_verification(self) -> None:
        """Should detect email verification requests."""
        result = detect_intervention_needed(
            visible_text="Please verify your email address. Check your inbox.",
            test_name="signup_flow",
            current_url="http://localhost/verify",
        )
        assert result is not None
        assert result.reason == InterventionReason.EMAIL_VERIFICATION

    def test_detect_sms_verification(self) -> None:
        """Should detect SMS verification."""
        result = detect_intervention_needed(
            visible_text="Enter the verification code we sent to your phone.",
            test_name="signup",
            current_url="http://localhost/verify-phone",
        )
        assert result is not None
        assert result.reason == InterventionReason.SMS_VERIFICATION

    def test_detect_captcha(self) -> None:
        """Should detect CAPTCHA."""
        result = detect_intervention_needed(
            visible_text="Please complete the CAPTCHA to continue",
            test_name="signup",
            current_url="http://localhost/signup",
        )
        assert result is not None
        assert result.reason == InterventionReason.CAPTCHA

    def test_detect_oauth(self) -> None:
        """Should detect OAuth redirects."""
        result = detect_intervention_needed(
            visible_text="Continue with Google",
            test_name="login",
            current_url="http://localhost/login",
        )
        assert result is not None
        assert result.reason == InterventionReason.OAUTH_REDIRECT

    def test_detect_payment(self) -> None:
        """Should detect payment flows."""
        result = detect_intervention_needed(
            visible_text="Enter your credit card details to complete checkout",
            test_name="upgrade",
            current_url="http://localhost/billing",
        )
        assert result is not None
        assert result.reason == InterventionReason.PAYMENT

    def test_detect_mfa(self) -> None:
        """Should detect MFA prompts."""
        result = detect_intervention_needed(
            visible_text="Enter the code from your authenticator app",
            test_name="login",
            current_url="http://localhost/mfa",
        )
        assert result is not None
        assert result.reason == InterventionReason.MFA

    def test_no_intervention_for_normal_page(self) -> None:
        """Should not flag normal pages."""
        result = detect_intervention_needed(
            visible_text="Welcome to the dashboard. You have 5 new messages.",
            test_name="dashboard",
            current_url="http://localhost/dashboard",
        )
        assert result is None

    def test_request_includes_context(self) -> None:
        """Intervention request should include useful context."""
        result = detect_intervention_needed(
            visible_text="Please verify your email",
            test_name="signup_test",
            current_url="http://localhost/verify",
            page_title="Verify Email",
            screenshot_path="/tmp/screenshot.png",
        )
        assert result is not None
        assert result.test_name == "signup_test"
        assert result.current_url == "http://localhost/verify"
        assert result.screenshot_path == "/tmp/screenshot.png"
        assert result.instructions


class TestWriteInterventionPrompt:
    """Tests for write_intervention_prompt."""

    def test_writes_markdown_file(self, tmp_path: Path) -> None:
        """Should write a markdown file with the prompt."""
        config = SharinganConfig(project_dir=tmp_path)
        request = detect_intervention_needed(
            visible_text="Please verify your email",
            test_name="signup",
            current_url="http://localhost/verify",
        )
        assert request is not None

        write_intervention_prompt(request, config)
        prompt_path = config.get_intervention_prompt_path()

        assert prompt_path.exists()
        content = prompt_path.read_text()
        assert "Sharingan Needs Your Help" in content
        assert "signup" in content
        assert "verify" in content.lower()

    def test_clear_removes_file(self, tmp_path: Path) -> None:
        """clear_intervention_prompt should remove the file."""
        config = SharinganConfig(project_dir=tmp_path)
        request = detect_intervention_needed(
            visible_text="CAPTCHA",
            test_name="test",
            current_url="http://localhost/",
        )
        assert request is not None
        write_intervention_prompt(request, config)

        clear_intervention_prompt(config)
        assert not config.get_intervention_prompt_path().exists()

    def test_clear_handles_missing_file(self, tmp_path: Path) -> None:
        """clear_intervention_prompt should not fail if file doesn't exist."""
        config = SharinganConfig(project_dir=tmp_path)
        # Should not raise
        clear_intervention_prompt(config)

    def test_includes_resume_instructions(self, tmp_path: Path) -> None:
        """Prompt should include how to resume."""
        config = SharinganConfig(project_dir=tmp_path)
        request = detect_intervention_needed(
            visible_text="Verify email",
            test_name="signup",
            current_url="http://localhost/verify",
        )
        assert request is not None

        write_intervention_prompt(request, config)
        content = config.get_intervention_prompt_path().read_text()
        assert "/sharingan-resume" in content
