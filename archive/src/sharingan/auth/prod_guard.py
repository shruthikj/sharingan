"""Safety guard to prevent running Sharingan against production."""

from __future__ import annotations

from urllib.parse import urlparse

from sharingan.config import SharinganConfig


class ProdGuardError(Exception):
    """Raised when Sharingan would run against what looks like production."""


SAFE_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
SAFE_SUFFIXES = (".local", ".localhost", ".test", ".internal")
PROD_INDICATORS = ("prod", "production", "live", "www.")


def is_safe_url(url: str) -> bool:
    """Check if a URL looks safe (local, staging, or dev).

    Returns True if the URL points to localhost, a .local/.test domain,
    or an obvious development/staging host. Returns False if it looks
    like a production URL.

    Args:
        url: The URL to check.

    Returns:
        True if the URL is safe to target automatically.
    """
    parsed = urlparse(url if "://" in url else f"http://{url}")
    host = (parsed.hostname or "").lower()

    if not host:
        return False

    if host in SAFE_HOSTS:
        return True

    if host.endswith(SAFE_SUFFIXES):
        return True

    # 192.168.x.x, 10.x.x.x, 172.16-31.x.x are private ranges
    if host.startswith(("192.168.", "10.", "172.")):
        return True

    # dev/staging subdomains
    if any(seg in host for seg in ("dev.", "staging.", "stage.", "test.", "qa.")):
        return True

    # Explicit production indicators
    if any(ind in host for ind in PROD_INDICATORS):
        return False

    # Anything else with a real TLD is probably prod
    if "." in host and not host.endswith((".local", ".test", ".internal", ".localhost")):
        return False

    return True


def check_prod_guard(config: SharinganConfig) -> None:
    """Check that Sharingan is not about to run against production.

    Raises ProdGuardError if base_url or api_base_url look like production
    and allow_prod is not set.

    Args:
        config: Sharingan configuration.

    Raises:
        ProdGuardError: If running against what looks like production.
    """
    if config.allow_prod:
        return

    unsafe_urls: list[str] = []
    if not is_safe_url(config.base_url):
        unsafe_urls.append(config.base_url)
    if not is_safe_url(config.api_base_url):
        unsafe_urls.append(config.api_base_url)

    if unsafe_urls:
        raise ProdGuardError(
            f"Sharingan refuses to run against what looks like production:\n"
            f"  {', '.join(unsafe_urls)}\n"
            f"If this is a dev/staging environment, set allow_prod=True in config "
            f"or use --allow-prod on the CLI.\n"
            f"If this is actually production, do NOT proceed — Sharingan will "
            f"create test users and run destructive tests."
        )
