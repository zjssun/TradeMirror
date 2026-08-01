from app.schemas.market import MarketCandle


def trend(indicators: dict[str, float | None], candles: list[MarketCandle]) -> str:
    ema20, ema50 = indicators["ema20"], indicators["ema50"]
    if ema20 is None or ema50 is None or len(candles) < 5: return "UNKNOWN"
    slope = candles[-1].close - candles[-5].close
    if ema20 > ema50 and slope > 0: return "UP"
    if ema20 < ema50 and slope < 0: return "DOWN"
    return "RANGE"
