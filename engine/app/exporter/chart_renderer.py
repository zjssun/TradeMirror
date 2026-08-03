from datetime import UTC, datetime
from io import BytesIO

from PIL import Image, ImageDraw


def render_chart(trade: dict, context: dict | None) -> bytes:
    image = Image.new("RGB", (1000, 500), "white")
    draw = ImageDraw.Draw(image)
    candles = (context or {}).get("candles", [])
    draw.text((24, 18), f"{trade['symbol']} · {trade['direction']} · trade {trade['id']}", fill="#1e293b")
    if not candles:
        draw.text((24, 70), "No stored historical candles available for this trade.", fill="#64748b")
    else:
        highs, lows = [c["high"] for c in candles], [c["low"] for c in candles]
        high, low = max(highs), min(lows)
        scale = lambda value: 450 - (value - low) / (high - low or 1) * 360
        width = max(2, 900 // len(candles))
        for index, candle in enumerate(candles):
            x = 50 + index * 900 / len(candles)
            color = "#16a34a" if candle["close"] >= candle["open"] else "#dc2626"
            draw.line((x, scale(candle["high"]), x, scale(candle["low"])), fill=color)
            draw.rectangle((x - width / 3, scale(max(candle["open"], candle["close"])), x + width / 3, scale(min(candle["open"], candle["close"]))), fill=color)
        for key, color in (("open_price", "#2563eb"), ("close_price", "#7c3aed"), ("stop_loss", "#dc2626"), ("take_profit", "#16a34a")):
            if trade.get(key) is not None:
                y = scale(trade[key])
                draw.line((50, y, 950, y), fill=color, width=2)
                draw.text((955, y - 8), key, fill=color)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def render_replay_chart(replay, events: list[dict]) -> bytes:
    candles = replay.candles[:replay.cursor + 1]
    image = Image.new("RGB", (1200, 600), "white")
    draw = ImageDraw.Draw(image)
    draw.text((24, 18), f"{replay.symbol} · {replay.timeframe} · {candles[-1].time.isoformat()}", fill="#1e293b")
    highs, lows = [candle.high for candle in candles], [candle.low for candle in candles]
    high, low = max(highs), min(lows)
    scale = lambda value: 550 - (value - low) / (high - low or 1) * 460
    width = max(2, 1080 // len(candles))
    for index, candle in enumerate(candles):
        x = 60 + index * 1080 / len(candles)
        color = "#16a34a" if candle.close >= candle.open else "#dc2626"
        draw.line((x, scale(candle.high), x, scale(candle.low)), fill=color)
        draw.rectangle((x - width / 3, scale(max(candle.open, candle.close)), x + width / 3, scale(min(candle.open, candle.close))), fill=color)
    for event in events:
        open_time = datetime.fromisoformat(event["open_time"].replace("Z", "+00:00")).replace(tzinfo=UTC) if datetime.fromisoformat(event["open_time"].replace("Z", "+00:00")).tzinfo is None else datetime.fromisoformat(event["open_time"].replace("Z", "+00:00")).astimezone(UTC)
        close_time = datetime.fromisoformat(event["close_time"].replace("Z", "+00:00")).replace(tzinfo=UTC) if datetime.fromisoformat(event["close_time"].replace("Z", "+00:00")).tzinfo is None else datetime.fromisoformat(event["close_time"].replace("Z", "+00:00")).astimezone(UTC)
        entry_index = max((index for index, candle in enumerate(candles) if (candle.time.replace(tzinfo=UTC) if candle.time.tzinfo is None else candle.time.astimezone(UTC)) <= open_time), default=-1)
        exit_index = max((index for index, candle in enumerate(candles) if (candle.time.replace(tzinfo=UTC) if candle.time.tzinfo is None else candle.time.astimezone(UTC)) <= close_time), default=-1)
        color = "#2563eb" if event["direction"] == "BUY" else "#dc2626"
        if entry_index >= 0:
            entry_x = 60 + entry_index * 1080 / len(candles)
            draw.ellipse((entry_x - 4, scale(event["open_price"]) - 4, entry_x + 4, scale(event["open_price"]) + 4), fill=color)
        if entry_index >= 0 and exit_index >= 0:
            exit_x = 60 + exit_index * 1080 / len(candles)
            draw.line((entry_x, scale(event["open_price"]), exit_x, scale(event["close_price"])), fill=color, width=2)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
