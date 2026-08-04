from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.market import MarketCandle


class IndicatorProvider(ABC):
    name: str
    version: str

    @abstractmethod
    def calculate(self, name: str, candles: list[MarketCandle], parameters: dict[str, float | int]) -> dict[str, list[float | None]]:
        raise NotImplementedError
