SCALPING_SECONDS = 4 * 60 * 60
DAY_TRADING_SECONDS = 24 * 60 * 60
HIGH_CONCENTRATION = 0.6


def build_profile(statistics: dict) -> dict:
    median_duration = statistics["median_holding_duration_seconds"]
    if median_duration is None:
        style = "UNKNOWN"
    elif median_duration <= SCALPING_SECONDS:
        style = "SCALPING"
    elif median_duration <= DAY_TRADING_SECONDS:
        style = "DAY_TRADING"
    else:
        style = "SWING"
    direction_counts = statistics["by_direction"]
    direction_preference = max(direction_counts, key=lambda key: direction_counts[key]["trade_count"]) if direction_counts else "UNKNOWN"
    total = statistics["trade_count"]
    symbol_counts = statistics["by_symbol"]
    dominant_symbol = max(symbol_counts, key=lambda key: symbol_counts[key]["trade_count"]) if symbol_counts else None
    concentration = symbol_counts[dominant_symbol]["trade_count"] / total if dominant_symbol and total else None
    return {
        "rules_version": "1.0",
        "style": style,
        "direction_preference": direction_preference,
        "dominant_symbol": dominant_symbol,
        "symbol_concentration": concentration,
        "risk_labels": [
            label for label, applies in {
                "HIGH_SYMBOL_CONCENTRATION": bool(concentration and concentration >= HIGH_CONCENTRATION),
                "LOSING_STREAK_RISK": statistics["longest_loss_streak"] >= 3,
                "UNPROFITABLE_HISTORY": bool(statistics["trade_count"] and statistics["net_profit"] < 0),
            }.items() if applies
        ],
        "evidence": {
            "median_holding_duration_seconds": median_duration,
            "trade_count": total,
            "net_profit": statistics["net_profit"],
            "profit_factor": statistics["profit_factor"],
            "longest_loss_streak": statistics["longest_loss_streak"],
        },
    }
