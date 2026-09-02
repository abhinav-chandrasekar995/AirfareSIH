"""Anti-bot challenge detection.

The purpose of this guard is the opposite of what a scraping toolkit usually does: it
detects a CAPTCHA, login wall or block page so collection can STOP. The platform never
attempts to solve, bypass or evade an access control (build prompt Sec.3).
"""
from __future__ import annotations

CHALLENGE_MARKERS = (
    "captcha",
    "recaptcha",
    "hcaptcha",
    "cf-challenge",
    "cloudflare",
    "are you a robot",
    "unusual traffic",
    "access denied",
    "please verify you are human",
    "bot detection",
    "sign in to continue",
    "log in to view fares",
)

CHALLENGE_STATUS_CODES = {401, 403, 429, 503}


class ChallengeDetector:
    def is_challenged(self, payload) -> bool:
        """True when the response is an access control rather than fare data."""
        status = getattr(payload, "http_status", None)
        if status in CHALLENGE_STATUS_CODES:
            return True

        content = getattr(payload, "content", None)
        if isinstance(content, str):
            lowered = content.lower()
            return any(marker in lowered for marker in CHALLENGE_MARKERS)
        return False
