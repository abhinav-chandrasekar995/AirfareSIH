"""Guard chain assembled once and injected into every adapter."""
from dataclasses import dataclass

from app.collection.guards.challenge_detector import ChallengeDetector
from app.collection.guards.circuit_breaker import CircuitBreaker
from app.collection.guards.rate_limiter import RateLimiter
from app.collection.guards.robots_guard import RobotsGuard


@dataclass
class GuardChain:
    robots: RobotsGuard
    limiter: RateLimiter
    breaker: CircuitBreaker
    challenge: ChallengeDetector


def build_guards(redis=None, respect_robots: bool = True) -> GuardChain:
    return GuardChain(
        robots=RobotsGuard(enabled=respect_robots),
        limiter=RateLimiter(redis=redis),
        breaker=CircuitBreaker(),
        challenge=ChallengeDetector(),
    )


__all__ = [
    "GuardChain", "build_guards", "RobotsGuard", "RateLimiter",
    "CircuitBreaker", "ChallengeDetector",
]
