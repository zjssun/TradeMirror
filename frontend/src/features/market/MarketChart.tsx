import { useEffect, useRef } from "react";
import { Empty } from "antd";
import { CandlestickSeries, ColorType, createChart, createSeriesMarkers, LineSeries, type IChartApi, type SeriesMarker, type Time, type UTCTimestamp } from "lightweight-charts";

import { useI18n } from "../../app/i18n";
import type { MarketCandle } from "../../types/market";
import { TradeAnnotationPrimitive, formatTradeVolume, type TradeAnnotation } from "./TradeAnnotationPrimitive";

interface Props { candles: MarketCandle[]; direction?: string; entryPrice?: number; exitPrice?: number; volume?: number; stopLoss?: number | null; takeProfit?: number | null; entryTime?: string; exitTime?: string; }
function formatUtcTime(value: Time): string { const date = new Date(Number(value) * 1000); return `${String(date.getUTCDate()).padStart(2, "0")} ${String(date.getUTCHours()).padStart(2, "0")}:${String(date.getUTCMinutes()).padStart(2, "0")}`; }
function timestamp(value: string): UTCTimestamp { const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`; return Math.floor(new Date(utcValue).getTime() / 1000) as UTCTimestamp; }
function candleTimeAtOrBefore(candles: MarketCandle[], value: string): UTCTimestamp | undefined { const target = timestamp(value); let matched: UTCTimestamp | undefined; for (const candle of candles) { const current = timestamp(candle.time); if (current > target) break; matched = current; } return matched; }
function formatPrice(value: number): string { return value.toFixed(2); }

export function MarketChart({ candles, direction, entryPrice, exitPrice, volume, stopLoss, takeProfit, entryTime, exitTime }: Props) {
  const { t } = useI18n(); const containerRef = useRef<HTMLDivElement>(null); const chartRef = useRef<IChartApi | null>(null);
  useEffect(() => {
    if (!containerRef.current || candles.length === 0) return;
    const chart: IChartApi = createChart(containerRef.current, { autoSize: true, height: 520, layout: { background: { type: ColorType.Solid, color: "#ffffff" }, textColor: "#334155" }, grid: { vertLines: { color: "#f1f5f9" }, horzLines: { color: "#f1f5f9" } }, timeScale: { timeVisible: true, secondsVisible: false, tickMarkFormatter: formatUtcTime }, localization: { timeFormatter: formatUtcTime } });
    chartRef.current = chart;
    const series = chart.addSeries(CandlestickSeries, { upColor: "#16a34a", downColor: "#dc2626", borderVisible: false, wickUpColor: "#16a34a", wickDownColor: "#dc2626" });
    series.setData(candles.map((candle) => ({ time: timestamp(candle.time), open: candle.open, high: candle.high, low: candle.low, close: candle.close })));
    const annotations = new TradeAnnotationPrimitive(); series.attachPrimitive(annotations);
    [[stopLoss, t("market.stopLoss"), "#dc2626"], [takeProfit, t("market.takeProfit"), "#16a34a"]].forEach(([price, title, color]) => { if (typeof price === "number") series.createPriceLine({ price, title: String(title), color: String(color), lineWidth: 1, lineStyle: 2, axisLabelVisible: true }); });
    const entryMarkerTime = entryTime && candleTimeAtOrBefore(candles, entryTime); const exitMarkerTime = exitTime && candleTimeAtOrBefore(candles, exitTime); const isBuy = direction === "BUY"; const markers: SeriesMarker<UTCTimestamp>[] = []; const labels: TradeAnnotation[] = []; const lots = typeof volume === "number" ? formatTradeVolume(volume, t("market.lots")) : "—";
    if (entryMarkerTime && typeof entryPrice === "number") { markers.push({ time: entryMarkerTime, position: isBuy ? "atPriceBottom" : "atPriceTop", price: entryPrice, color: "#2563eb", shape: isBuy ? "arrowUp" : "arrowDown", size: 2 }); labels.push({ id: "entry", time: entryMarkerTime, price: entryPrice, anchor: isBuy ? "below" : "above", color: "#2563eb", lines: [isBuy ? t("market.openBuy") : t("market.openSell"), `${formatPrice(entryPrice)} · ${lots}`] }); }
    if (exitMarkerTime && typeof exitPrice === "number") { markers.push({ time: exitMarkerTime, position: isBuy ? "atPriceTop" : "atPriceBottom", price: exitPrice, color: "#7c3aed", shape: isBuy ? "arrowDown" : "arrowUp", size: 2 }); labels.push({ id: "exit", time: exitMarkerTime, price: exitPrice, anchor: isBuy ? "above" : "below", color: "#7c3aed", lines: [isBuy ? t("market.closeBuy") : t("market.closeSell"), `${formatPrice(exitPrice)} · ${lots}`] }); }
    createSeriesMarkers(series, markers); annotations.setAnnotations(labels);
    if (entryMarkerTime && exitMarkerTime && entryMarkerTime !== exitMarkerTime && typeof entryPrice === "number" && typeof exitPrice === "number") { const tradeLine = chart.addSeries(LineSeries, { color: exitPrice >= entryPrice ? "#16a34a" : "#dc2626", lineWidth: 2, crosshairMarkerVisible: false, lastValueVisible: false, priceLineVisible: false }); tradeLine.setData([{ time: entryMarkerTime, value: entryPrice }, { time: exitMarkerTime, value: exitPrice }]); }
    chart.timeScale().fitContent(); return () => { series.detachPrimitive(annotations); chartRef.current = null; chart.remove(); };
  }, [candles, direction, entryPrice, exitPrice, volume, stopLoss, takeProfit, entryTime, exitTime, t]);
  if (!candles.length) return <Empty description={t("market.noCandles")} />;
  return <div ref={containerRef} style={{ width: "100%" }} />;
}
