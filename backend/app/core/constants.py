"""Domain enumerations shared across every layer. Single source of truth."""
from enum import StrEnum


class Region(StrEnum):
    NORTH = "NORTH"
    SOUTH = "SOUTH"
    EAST = "EAST"
    WEST = "WEST"
    NORTHEAST = "NORTHEAST"
    CENTRAL = "CENTRAL"


class SourceType(StrEnum):
    AIRLINE_DIRECT = "AIRLINE_DIRECT"
    OTA = "OTA"


class SourceStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    DISABLED = "DISABLED"


class LeadBucket(StrEnum):
    """The five advance-purchase windows required by the problem statement."""
    T1 = "T1"
    T7 = "T7"
    T15 = "T15"
    T30 = "T30"
    T45 = "T45"

    @property
    def days(self) -> int:
        return {"T1": 1, "T7": 7, "T15": 15, "T30": 30, "T45": 45}[self.value]

    @classmethod
    def ordered(cls) -> list["LeadBucket"]:
        return [cls.T45, cls.T30, cls.T15, cls.T7, cls.T1]

    @classmethod
    def from_lead_days(cls, days: int) -> "LeadBucket | None":
        """Map an arbitrary lead time onto the nearest collection window (+/- 2 days)."""
        for bucket in cls:
            if abs(days - bucket.days) <= 2:
                return bucket
        return None


class FareClass(StrEnum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    LIMITED = "LIMITED"
    SOLD_OUT = "SOLD_OUT"
    UNKNOWN = "UNKNOWN"


class QualityBand(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @classmethod
    def from_score(cls, score: float) -> "QualityBand":
        if score >= 85:
            return cls.HIGH
        if score >= 60:
            return cls.MEDIUM
        return cls.LOW


class IndexLevel(StrEnum):
    NATIONAL = "NATIONAL"
    REGIONAL = "REGIONAL"
    ROUTE = "ROUTE"
    AIRLINE = "AIRLINE"


class Estimator(StrEnum):
    MEAN = "MEAN"
    MEDIAN = "MEDIAN"
    TRIMMED_MEAN_10 = "TRIMMED_MEAN_10"
    WEIGHTED_MEDIAN = "WEIGHTED_MEDIAN"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyClass(StrEnum):
    """Market anomalies and scraper anomalies must never be conflated (build prompt Sec.11)."""
    MARKET = "MARKET"
    SCRAPER = "SCRAPER"


class AnomalyStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Band(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ScrapeStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED_ROBOTS = "SKIPPED_ROBOTS"
    SKIPPED_CHALLENGE = "SKIPPED_CHALLENGE"


class Role(StrEnum):
    PUBLIC = "PUBLIC"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"

    @property
    def rank(self) -> int:
        return {"PUBLIC": 0, "ANALYST": 1, "ADMIN": 2}[self.value]


class DataMode(StrEnum):
    LIVE = "LIVE"
    CACHED = "CACHED"
    REPLAY = "REPLAY"


class Granularity(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
