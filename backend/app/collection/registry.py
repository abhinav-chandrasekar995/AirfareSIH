"""Adapter registry: source_code -> adapter class."""
from __future__ import annotations

from app.collection.adapters.aggregators.google_flights_serpapi_adapter import (
    GoogleFlightsSerpApiAdapter,
)
from app.collection.adapters.airlines.air_india_adapter import AirIndiaAdapter
from app.collection.adapters.airlines.air_india_express_adapter import AirIndiaExpressAdapter
from app.collection.adapters.airlines.akasa_adapter import AkasaAdapter
from app.collection.adapters.airlines.indigo_adapter import IndiGoAdapter
from app.collection.adapters.airlines.spicejet_adapter import SpiceJetAdapter
from app.collection.adapters.otas.cleartrip_adapter import CleartripAdapter
from app.collection.adapters.otas.easemytrip_adapter import EaseMyTripAdapter
from app.collection.adapters.otas.goibibo_adapter import GoibiboAdapter
from app.collection.adapters.otas.ixigo_adapter import IxigoAdapter
from app.collection.adapters.otas.makemytrip_adapter import MakeMyTripAdapter
from app.collection.adapters.otas.yatra_adapter import YatraAdapter
from app.collection.base_adapter import BaseSourceAdapter

ADAPTERS: dict[str, type[BaseSourceAdapter]] = {
    cls.source_code: cls
    for cls in (
        IndiGoAdapter,
        AirIndiaAdapter,
        AirIndiaExpressAdapter,
        AkasaAdapter,
        SpiceJetAdapter,
        MakeMyTripAdapter,
        GoibiboAdapter,
        YatraAdapter,
        CleartripAdapter,
        EaseMyTripAdapter,
        IxigoAdapter,
        GoogleFlightsSerpApiAdapter,
    )
}

# Fallback order used when a source goes down: airline-direct first, since a direct
# quote is the fare a traveller actually faces without OTA markup (build prompt Sec.3).
# google_flights (SerpApi, an authorized aggregator API, not a scraped site) sits last -
# not because it's least trustworthy, but because it's an aggregate view rather than a
# single traveller-facing quote; in practice, as of this basket's own robots.txt
# findings, it is also the fallback most likely to actually succeed.
FALLBACK_ORDER = [
    "indigo", "airindia", "akasa", "spicejet", "airindiaexpress",
    "makemytrip", "goibibo", "cleartrip", "yatra", "easemytrip", "ixigo",
    "google_flights",
]


def get_adapter(source_code: str) -> type[BaseSourceAdapter]:
    if source_code not in ADAPTERS:
        raise KeyError(f"no adapter registered for source '{source_code}'")
    return ADAPTERS[source_code]


def fallback_for(source_code: str, available: set[str]) -> str | None:
    """Next usable source when `source_code` is unavailable."""
    candidates = [s for s in FALLBACK_ORDER if s != source_code and s in available]
    return candidates[0] if candidates else None
