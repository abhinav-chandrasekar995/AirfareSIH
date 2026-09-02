"""Circuit breaker per source.

After repeated failures the circuit opens and the source is skipped for a cooldown
period. This protects the source as much as it protects us: continuing to hammer a
site that is returning errors is exactly the behaviour that earns a permanent block.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

FAILURE_THRESHOLD = 5
COOLDOWN_SECONDS = 900


@dataclass
class _State:
    failures: int = 0
    opened_at: float | None = None
    successes: int = 0


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = FAILURE_THRESHOLD,
        cooldown_seconds: int = COOLDOWN_SECONDS,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._states: dict[str, _State] = {}

    def _state(self, source_code: str) -> _State:
        return self._states.setdefault(source_code, _State())

    def is_open(self, source_code: str) -> bool:
        state = self._state(source_code)
        if state.opened_at is None:
            return False
        if time.time() - state.opened_at >= self.cooldown_seconds:
            # Cooldown elapsed: half-open, allow one probe request through.
            state.opened_at = None
            state.failures = 0
            return False
        return True

    def record_failure(self, source_code: str) -> None:
        state = self._state(source_code)
        state.failures += 1
        if state.failures >= self.failure_threshold and state.opened_at is None:
            state.opened_at = time.time()

    def record_success(self, source_code: str) -> None:
        state = self._state(source_code)
        state.failures = 0
        state.opened_at = None
        state.successes += 1

    def status(self, source_code: str) -> str:
        state = self._state(source_code)
        if self.is_open(source_code):
            return "UNAVAILABLE"
        return "DEGRADED" if state.failures > 0 else "ACTIVE"
