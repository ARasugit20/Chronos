import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models.theme_mapping import ThemeMapping

THEME_MAPPINGS_PATH = Path(__file__).resolve().parent / "theme_mappings.json"


async def seed_theme_mappings() -> int:
    with THEME_MAPPINGS_PATH.open(encoding="utf-8") as handle:
        rows = json.load(handle)

    created = 0
    async with SessionLocal() as session:
        for row in rows:
            existing = (
                await session.execute(
                    select(ThemeMapping).where(ThemeMapping.event_pattern == row["event_pattern"])
                )
            ).scalar_one_or_none()
            if existing:
                continue
            session.add(
                ThemeMapping(
                    event_pattern=row["event_pattern"],
                    tickers=row["tickers"],
                    rationale=row["rationale"],
                    confidence_prior=row["confidence_prior"],
                    approved_by_human=row["approved_by_human"],
                )
            )
            created += 1
        await session.commit()
    return created


async def main() -> None:
    count = await seed_theme_mappings()
    print(f"Seeded {count} theme mappings")


if __name__ == "__main__":
    asyncio.run(main())
