from datetime import timedelta

from app.schemas.market import CandleTimeframe


def select_timeframe(open_time, close_time) -> CandleTimeframe:
    duration = close_time - open_time
    if duration <= timedelta(hours=4): return CandleTimeframe.M5
    if duration <= timedelta(days=2): return CandleTimeframe.M15
    if duration <= timedelta(days=14): return CandleTimeframe.H1
    return CandleTimeframe.H4
