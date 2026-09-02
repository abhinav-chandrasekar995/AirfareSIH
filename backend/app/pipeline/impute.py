"""Stage 2.4 - Controlled missing-value handling.

Imputation is deliberately minimal and always recorded. An imputed field is a modelled
value, and a statistical product that cannot say which numbers it invented is not
auditable - so every imputation appends to `imputed_fields` on the stored row.
"""
from __future__ import annotations

# Typical Indian domestic UDF share of base fare, used only when the source omits the
# component but the total still reconciles.
DEFAULT_UDF_RATE = 0.06
DEFAULT_TAX_RATE = 0.12


def impute_components(obs: dict) -> tuple[dict, list[str]]:
    """Fill only fare components that can be derived from what the source did report."""
    imputed: list[str] = []
    result = dict(obs)

    base = float(result.get("base_fare") or 0)
    total = float(result.get("total_fare") or 0)

    if base <= 0 or total <= 0:
        return result, imputed

    reported = sum(
        float(result.get(k) or 0)
        for k in ("taxes", "udf", "airport_charges", "convenience_fee")
    )
    gap = total - base - reported

    # Only distribute a positive, material residual, and only into components the
    # source actually left blank.
    if gap > 1.0:
        if not result.get("taxes"):
            result["taxes"] = round(gap * (DEFAULT_TAX_RATE / (DEFAULT_TAX_RATE + DEFAULT_UDF_RATE)), 2)
            imputed.append("taxes")
        if not result.get("udf"):
            result["udf"] = round(gap - float(result.get("taxes") or 0), 2)
            imputed.append("udf")

    return result, imputed
