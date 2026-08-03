import { useEffect, useRef } from "react";
import { Empty } from "antd";
import { CandlestickSeries, ColorType, createChart, createSeriesMarkers, LineSeries, LineStyle, type IChartApi, type SeriesMarker, type Time, type UTCTimestamp } from "lightweight-charts";

import { useI18n } from "../../app/i18n";
import type { MarketCandle } from "../../types/market";
import type { ReplayTradeEvent } from "../../types/replay";

interface Props {
  candles: MarketCandle[];
  events: ReplayTradeEvent[];
  cursor: number;
  animationDuration: number;
  onTradeSelect: (event: ReplayTradeEvent) => void;
}

const BUY_COLORS = ["#16a34a", "#65a30d", "#0f766e", "#0891b2"];
const SELL_COLORS = ["#dc2626", "#ea580c", "#c2410c", "#be123c"];
type CandleData = { time: UTCTimestamp; open: number; high: number; low: number; close: number };
type TradePath = { setData: (data: Array<{ time: UTCTimestamp; value: number }>) => void };

function timestamp(value: string): UTCTimestamp {
  const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`;
  return Math.floor(new Date(utcValue).getTime() / 1000) as UTCTimestamp;
}

function candleData(candle: MarketCandle): CandleData {
  return { time: timestamp(candle.time), open: candle.open, high: candle.high, low: candle.low, close: candle.close };
}

function formatUtcTime(value: Time): string {
  const date = new Date(Number(value) * 1000);
  return `${String(date.getUTCDate()).padStart(2, "0")} ${String(date.getUTCHours()).padStart(2, "0")}:${String(date.getUTCMinutes()).padStart(2, "0")}`;
}

export function formatPrice(value: number): string {
  return value.toFixed(2);
}

export function candleIndexAtOrBefore(candles: MarketCandle[], value: string): number {
  const target = timestamp(value);
  let matched = -1;
  for (let index = 0; index < candles.length; index += 1) {
    if (timestamp(candles[index].time) > target) break;
    matched = index;
  }
  return matched;
}

function colorAssignments(candles: MarketCandle[], events: ReplayTradeEvent[]): Map<number, string> {
  const result = new Map<number, string>();
  for (const direction of ["BUY", "SELL"]) {
    const palette = direction === "BUY" ? BUY_COLORS : SELL_COLORS;
    const ordered = events.filter((event) => event.direction === direction).sort((left, right) => candleIndexAtOrBefore(candles, left.open_time) - candleIndexAtOrBefore(candles, right.open_time) || left.open_time.localeCompare(right.open_time) || left.trade_id - right.trade_id);
    const assigned: Array<{ index: number; color: string }> = [];
    for (const event of ordered) {
      const index = candleIndexAtOrBefore(candles, event.open_time);
      const unavailable = new Set(assigned.filter((item) => index - item.index <= 3).map((item) => item.color));
      const color = palette.find((candidate) => !unavailable.has(candidate)) ?? palette[event.trade_id % palette.length];
      result.set(event.trade_id, color);
      assigned.push({ index, color });
    }
  }
  return result;
}

export function ReplayChart({ candles, events, cursor, animationDuration, onTradeSelect }: Props) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const updateRef = useRef<((nextCursor: number, animate: boolean) => void) | null>(null);
  const cursorRef = useRef(cursor);
  const renderedCursorRef = useRef(-1);
  const animationFrameRef = useRef<number | null>(null);
  const animationDurationRef = useRef(animationDuration);
  animationDurationRef.current = animationDuration;
  cursorRef.current = cursor;

  useEffect(() => {
    if (!containerRef.current || !candles.length) return;
    const chart = createChart(containerRef.current, { autoSize: true, height: 560, layout: { background: { type: ColorType.Solid, color: "#ffffff" }, textColor: "#334155" }, grid: { vertLines: { color: "#f1f5f9" }, horzLines: { color: "#f1f5f9" } }, timeScale: { timeVisible: true, secondsVisible: false, tickMarkFormatter: formatUtcTime }, localization: { timeFormatter: formatUtcTime } });
    chartRef.current = chart;
    const series = chart.addSeries(CandlestickSeries, { upColor: "#16a34a", downColor: "#dc2626", borderVisible: false, wickUpColor: "#16a34a", wickDownColor: "#dc2626" });
    const colors = colorAssignments(candles, events);
    const paths = new Map<number, TradePath>();
    const positions = new Map<number, { entryIndex: number; exitIndex: number; color: string; isBuy: boolean }>();
    for (const event of events) {
      const color = colors.get(event.trade_id) ?? (event.direction === "BUY" ? BUY_COLORS[0] : SELL_COLORS[0]);
      positions.set(event.trade_id, { entryIndex: candleIndexAtOrBefore(candles, event.open_time), exitIndex: candleIndexAtOrBefore(candles, event.close_time), color, isBuy: event.direction === "BUY" });
      paths.set(event.trade_id, chart.addSeries(LineSeries, { color, lineWidth: 2, lineStyle: LineStyle.Dashed, crosshairMarkerVisible: false, lastValueVisible: false, priceLineVisible: false }));
    }
    let clickable: Array<{ event: ReplayTradeEvent; time: UTCTimestamp; price: number }> = [];
    const markersApi = createSeriesMarkers(series, []);
    const updateDecorations = (nextCursor: number) => {
      const markers: SeriesMarker<UTCTimestamp>[] = [];
      clickable = [];
      for (const event of events) {
        const position = positions.get(event.trade_id);
        if (!position) continue;
        if (position.entryIndex >= 0 && position.entryIndex <= nextCursor) {
          const time = timestamp(candles[position.entryIndex].time);
          markers.push({ time, position: position.isBuy ? "atPriceBottom" : "atPriceTop", price: event.open_price, color: position.color, shape: position.isBuy ? "arrowUp" : "arrowDown", text: `${position.isBuy ? "↑ BUY" : "↓ SELL"} ${formatPrice(event.open_price)}`, size: 2 });
          clickable.push({ event, time, price: event.open_price });
        }
        if (position.exitIndex >= 0 && position.exitIndex <= nextCursor) {
          const time = timestamp(candles[position.exitIndex].time);
          const profit = event.net_profit >= 0 ? `+${event.net_profit}` : String(event.net_profit);
          markers.push({ time, position: position.isBuy ? "atPriceTop" : "atPriceBottom", price: event.close_price, color: position.color, shape: position.isBuy ? "arrowDown" : "arrowUp", text: `${t("replay.close")} ${formatPrice(event.close_price)} (${profit})`, size: 2 });
          clickable.push({ event, time, price: event.close_price });
        }
        paths.get(event.trade_id)?.setData(position.entryIndex >= 0 && position.exitIndex > position.entryIndex && position.exitIndex <= nextCursor ? [{ time: timestamp(candles[position.entryIndex].time), value: event.open_price }, { time: timestamp(candles[position.exitIndex].time), value: event.close_price }] : []);
      }
      markersApi.setMarkers(markers);
    };
    const cancelAnimation = () => {
      if (animationFrameRef.current !== null) window.cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    };
    const sync = (nextCursor: number, animate: boolean) => {
      cancelAnimation();
      const previousCursor = renderedCursorRef.current;
      if (!animate || nextCursor !== previousCursor + 1) {
        series.setData(candles.slice(0, nextCursor + 1).map(candleData));
        renderedCursorRef.current = nextCursor;
        updateDecorations(nextCursor);
        return;
      }
      const target = candleData(candles[nextCursor]);
      series.update({ time: target.time, open: target.open, high: target.open, low: target.open, close: target.open });
      const startedAt = performance.now();
      const animateFrame = (now: number) => {
        const progress = Math.min(1, (now - startedAt) / animationDurationRef.current);
        const eased = 1 - (1 - progress) ** 3;
        series.update({ time: target.time, open: target.open, high: target.open + (target.high - target.open) * eased, low: target.open + (target.low - target.open) * eased, close: target.open + (target.close - target.open) * eased });
        if (progress < 1) animationFrameRef.current = window.requestAnimationFrame(animateFrame);
        else { animationFrameRef.current = null; renderedCursorRef.current = nextCursor; updateDecorations(nextCursor); }
      };
      animationFrameRef.current = window.requestAnimationFrame(animateFrame);
    };
    chart.subscribeClick((parameter) => {
      if (!parameter.point || !parameter.time) return;
      const candidates = clickable.filter((item) => item.time === parameter.time).map((item) => ({ ...item, distance: Math.abs((series.priceToCoordinate(item.price) ?? Number.POSITIVE_INFINITY) - parameter.point!.y) }));
      const match = candidates.filter((item) => item.distance <= 16).sort((left, right) => left.distance - right.distance || left.event.trade_id - right.event.trade_id)[0];
      if (match) onTradeSelect(match.event);
    });
    renderedCursorRef.current = -1;
    updateRef.current = sync;
    sync(cursorRef.current, false);
    chart.timeScale().fitContent();
    return () => { cancelAnimation(); updateRef.current = null; chartRef.current = null; chart.remove(); };
  }, [candles, events, onTradeSelect, t]);

  useEffect(() => { updateRef.current?.(cursor, true); }, [cursor]);

  if (!candles.length) return <Empty description={t("market.noCandles")} />;
  return <div ref={containerRef} style={{ width: "100%" }} />;
}
