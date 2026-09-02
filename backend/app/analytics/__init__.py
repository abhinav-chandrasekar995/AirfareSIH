"""Pure statistical analytics.

ARCHITECTURE RULE (ADR-001 / build prompt Sec.35): this package must never import
from app.db, app.api, app.collection, app.services or app.tasks. Every function here
takes plain data structures (lists, dicts, DataFrames) and returns deterministic
output, which is what makes the published statistics reproducible and auditable.
Enforced in CI by import-linter (see pyproject.toml).
"""
