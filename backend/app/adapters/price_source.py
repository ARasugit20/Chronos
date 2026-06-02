import random
from decimal import Decimal
from typing import Protocol


class PriceSource(Protocol):
    async def get_price(self, ticker: str, metadata: dict | None = None) -> Decimal:
        ...


class MockPriceSource:
    async def get_price(self, ticker: str, metadata: dict | None = None) -> Decimal:
        _ = ticker
        if metadata and "price" in metadata:
            return Decimal(str(metadata["price"]))
        return Decimal(str(round(random.uniform(50, 500), 4)))


def get_price_source(name: str) -> PriceSource:
    if name in {"polygon", "yahoo"}:
        return MockPriceSource()
    return MockPriceSource()
