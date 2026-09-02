"""robots.txt awareness. Fetched once per host and cached."""
from __future__ import annotations

import urllib.robotparser
from urllib.parse import urlparse

USER_AGENT = "IndiaAirfareIntelligence/1.0 (statistical research; contact via API portal)"


class RobotsGuard:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    async def is_allowed(self, url: str, source_code: str = "") -> bool:
        """Return whether USER_AGENT may fetch `url`.

        A robots.txt that cannot be read is treated as permissive for the base path,
        matching standard crawler behaviour - but the source is still subject to every
        other guard (rate limit, challenge detection, circuit breaker).
        """
        if not self.enabled:
            return True

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True

        host = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._cache.get(host)
        if parser is None:
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(f"{host}/robots.txt")
            try:
                parser.read()
            except Exception:
                return True
            self._cache[host] = parser

        return parser.can_fetch(USER_AGENT, url)
