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
