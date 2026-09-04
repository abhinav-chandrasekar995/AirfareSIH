"""All ORM models. Imported here so Alembic autogenerate and Base.metadata see them."""
from app.db.models.derived import (
    Anomaly,
    BacktestRun,
    CoreIndexValue,
    CpiSimulation,
    Forecast,
    IndexValue,
    LeadTimeCurve,
    VolatilityMetric,
)
from app.db.models.observations import FareObservation, FareObservationRaw
from app.db.models.operational import ApiKey, AuditLog, DataQualityFlag, ScrapeRun
from app.db.models.reference import (
    Airline,
    Airport,
    CpiReference,
    DgcaBenchmark,
    Event,
    MethodologyVersion,
    Route,
    RouteWeight,
    Source,
)

__all__ = [
    "Airport", "Airline", "Route", "RouteWeight", "Source", "Event",
    "DgcaBenchmark", "CpiReference", "MethodologyVersion",
    "FareObservationRaw", "FareObservation",
    "IndexValue", "CoreIndexValue", "LeadTimeCurve", "VolatilityMetric", "Anomaly",
    "Forecast", "BacktestRun", "CpiSimulation",
    "ScrapeRun", "DataQualityFlag", "ApiKey", "AuditLog",
]
