from app.schemas.market import MarketCandle


def levels(candles: list[MarketCandle], entry: float) -> tuple[list[float], list[float]]:
    lows, highs = [], []
    for index in range(2, len(candles) - 2):
        window = candles[index - 2:index + 3]
        if candles[index].low == min(c.low for c in window): lows.append(candles[index].low)
        if candles[index].high == max(c.high for c in window): highs.append(candles[index].high)
    supports = sorted({round(value, 8) for value in lows if value <= entry}, key=lambda value: entry - value)[:3]
    resistances = sorted({round(value, 8) for value in highs if value >= entry}, key=lambda value: value - entry)[:3]
    return supports, resistances
