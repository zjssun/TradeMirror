from __future__ import annotations

from collections import Counter
from statistics import median


def calculate_statistics(trades: list[dict]) -> dict:
    profits = [trade["net_profit"] for trade in trades]
    winners = [profit for profit in profits if profit > 0]
    losers = [profit for profit in profits if profit < 0]
    durations = [trade["holding_duration_seconds"] for trade in trades]
    count = len(trades)
    by_symbol = {symbol: _summary([trade for trade in trades if trade["symbol"] == symbol]) for symbol in sorted({trade["symbol"] for trade in trades})}
    by_direction = {direction: _summary([trade for trade in trades if trade["direction"] == direction]) for direction in ("BUY", "SELL") if any(trade["direction"] == direction for trade in trades)}
    return {
        **_summary(trades),
        "median_net_profit": median(profits) if profits else None,
        "average_holding_duration_seconds": sum(durations) / count if count else None,
        "median_holding_duration_seconds": median(durations) if durations else None,
        "longest_win_streak": _streak(profits, lambda value: value > 0),
        "longest_loss_streak": _streak(profits, lambda value: value < 0),
        "by_symbol": by_symbol,
        "by_direction": by_direction,
    }


def _summary(trades: list[dict]) -> dict:
    profits = [trade["net_profit"] for trade in trades]
    winners = [profit for profit in profits if profit > 0]
    losers = [profit for profit in profits if profit < 0]
    count = len(trades)
    gross_profit, gross_loss = sum(winners), abs(sum(losers))
    return {
        "trade_count": count,
        "winning_count": len(winners),
        "losing_count": len(losers),
        "breakeven_count": count - len(winners) - len(losers),
        "win_rate": len(winners) / count if count else None,
        "net_profit": sum(profits),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "average_net_profit": sum(profits) / count if count else None,
    }


def _streak(values: list[float], predicate) -> int:
    longest = current = 0
    for value in values:
        current = current + 1 if predicate(value) else 0
        longest = max(longest, current)
    return longest
