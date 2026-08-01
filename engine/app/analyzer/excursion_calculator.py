from app.schemas.market import MarketCandle


def excursions(direction: str, entry: float, candles: list[MarketCandle]) -> dict[str, float | None]:
    if not candles: return {"mfe_price": None, "mae_price": None, "max_drawdown_price": None}
    favorable = [(c.high - entry) if direction == "BUY" else (entry - c.low) for c in candles]
    adverse = [(entry - c.low) if direction == "BUY" else (c.high - entry) for c in candles]
    running_peak = 0.0
    drawdown = 0.0
    for value in favorable:
        running_peak = max(running_peak, value)
        drawdown = max(drawdown, running_peak - value)
    return {"mfe_price": max(favorable), "mae_price": max(adverse), "max_drawdown_price": drawdown}
