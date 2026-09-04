"""Ingests the real MoSPI e-Sankhyiki item-level Airfare CPI into `cpi_reference`.

Source: data/cpi_1703.xlsx, downloaded from the MoSPI e-Sankhyiki portal - item
"Passenger transport by air, domestic" (COICOP 07.3.3.1.2.01), All-India, Combined
sector, base year 2024. This is genuine government data, not seeded/synthetic - it is
kept in its own series_vintage ("mospi-airfare-2024base") so it is never confused with
the two illustrative CpiReference rows seeds/load_seed.py already writes under different
vintages ("cpi-2024-base", "cpi-2012-base"). See IMPLEMENTATION_LOG.md for the backtest
feature this feeds.

Idempotent: upserts on the (series_vintage, period_month) unique constraint, so re-running
after a fresh MoSPI download (new months appended to the sheet) is safe.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import openpyxl
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from app.db.models import CpiReference
from app.db.session import SessionLocal, dispose_engine

SOURCE_FILE = Path(__file__).resolve().parents[2] / "data" / "cpi_1703.xlsx"
SERIES_VINTAGE = "mospi-airfare-2024"  # String(20) column - keep at or under 20 chars
WEIGHT_SOURCE = "HCES 2023-24"  # the real household consumption survey backing the 2024-base CPI series

MONTH_NUMBER = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


def read_rows() -> list[dict]:
    wb = openpyxl.load_workbook(SOURCE_FILE, data_only=True)
    ws = wb["CPI Data"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    col = {name: i for i, name in enumerate(header)}

    out = []
    for r in rows[1:]:
        if r[col["item"]] != "Airfare":
            continue  # this sheet only ever has one item, but don't assume it stays that way
        out.append(
            {
                "period_month": date(int(r[col["year"]]), MONTH_NUMBER[r[col["month"]]], 1),
                "base_year": r[col["base_year"]],
                "airfare_sub_index": float(r[col["index"]]),
                "item_code": r[col["code"]],
            }
        )
    return out


async def main() -> None:
    rows = read_rows()
    print(f"Read {len(rows)} real MoSPI airfare CPI rows from {SOURCE_FILE.name}")
    for r in sorted(rows, key=lambda x: x["period_month"]):
        print(f"  {r['period_month']}: index={r['airfare_sub_index']}")

    async with SessionLocal() as session:
        await session.execute(text("SELECT set_config('app.role', 'ADMIN', false)"))

        for r in rows:
            stmt = insert(CpiReference).values(
                series_vintage=SERIES_VINTAGE,
                base_year=r["base_year"],
                weight_source=WEIGHT_SOURCE,
                coicop_version=r["item_code"],
                period_month=r["period_month"],
                airfare_sub_index=r["airfare_sub_index"],
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["series_vintage", "period_month"],
                set_={"airfare_sub_index": stmt.excluded.airfare_sub_index, "base_year": stmt.excluded.base_year},
            )
            await session.execute(stmt)

        await session.commit()
        print(f"\nUpserted {len(rows)} rows into cpi_reference (series_vintage={SERIES_VINTAGE})")

    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
