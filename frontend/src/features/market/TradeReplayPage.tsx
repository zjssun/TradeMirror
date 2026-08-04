import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { useMutation, useQuery } from "@tanstack/react-query";
import dayjs, { type Dayjs } from "dayjs";
import { Alert, Button, Card, DatePicker, Descriptions, Drawer, Empty, InputNumber, Modal, Select, Segmented, Slider, Space, Spin, Statistic, Switch, Typography } from "antd";

import { calculateIndicators, createTmfExport, getIndicatorDefinitions, getIndicatorPreferences, getReplaySymbols, getTradeReplay, saveIndicatorPreferences } from "../../api/engineClient";
import { useI18n } from "../../app/i18n";
import type { ReplayResponse, ReplayTradeEvent } from "../../types/replay";
import type { IndicatorPreferenceItem, IndicatorSeries } from "../../types/indicators";
import { ReplayChart, candleIndexAtOrBefore } from "./ReplayChart";
import { indicatorKey, IndicatorPanel, defaultIndicatorPreferences } from "./IndicatorPanel";
import { formatReplayDateTime, readReplayDisplayTimezone, replayTimezoneLabel, REPLAY_DISPLAY_TIMEZONE_OPTIONS, REPLAY_DISPLAY_TIMEZONE_STORAGE_KEY, type ReplayDisplayTimezone } from "./replayTime";

const { RangePicker } = DatePicker;

function formatDisplayValue(value: string, timezone: ReplayDisplayTimezone, localLabel: string): string {
  return formatReplayDateTime(value, timezone, localLabel);
}

export function TradeReplayPage() {
  const { t } = useI18n();
  const [displayTimezone, setDisplayTimezone] = useState<ReplayDisplayTimezone>(() => readReplayDisplayTimezone());
  const localTimezoneLabel = t("replay.timezoneLocal");
  const formatDisplayTime = (value: string) => formatDisplayValue(value, displayTimezone, localTimezoneLabel);
  const symbols = useQuery({ queryKey: ["replay-symbols"], queryFn: getReplaySymbols });
  const indicatorDefinitions = useQuery({ queryKey: ["indicator-definitions"], queryFn: getIndicatorDefinitions });
  const indicatorPreferences = useQuery({ queryKey: ["indicator-preferences"], queryFn: getIndicatorPreferences });
  const [symbol, setSymbol] = useState<string>();
  const [range, setRange] = useState<[Dayjs, Dayjs]>();
  const [replay, setReplay] = useState<ReplayResponse | null>(null);
  const [cursor, setCursor] = useState(0);
  const [initialCursor, setInitialCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<1 | 2 | 5>(1);
  const [timeframe, setTimeframe] = useState<"AUTO" | "M1" | "M5" | "M15" | "H1" | "H4">("AUTO");
  const [preRollCandles, setPreRollCandles] = useState(20);
  const [postRollCandles, setPostRollCandles] = useState(20);
  const [selectedTrade, setSelectedTrade] = useState<ReplayTradeEvent | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const [includeCharts, setIncludeCharts] = useState(true);
  const [redactSourceIdentity, setRedactSourceIdentity] = useState(true);
  const [indicatorRequests, setIndicatorRequests] = useState<IndicatorPreferenceItem[]>(defaultIndicatorPreferences());
  const [indicatorModalOpen, setIndicatorModalOpen] = useState(false);
  const indicatorScrollPositionRef = useRef<{ x: number; y: number } | null>(null);
  const [indicatorSeries, setIndicatorSeries] = useState<IndicatorSeries[]>([]);
  const saveIndicators = useMutation({ mutationFn: (indicators: IndicatorPreferenceItem[]) => saveIndicatorPreferences({ indicators }) });
  const selectedSymbol = symbols.data?.find((item) => item.symbol === symbol);
  const loadReplay = useMutation({
    mutationFn: ({ selectedSymbol, selectedRange, selectedTimeframe, preRoll, postRoll }: { selectedSymbol: string; selectedRange: [Dayjs, Dayjs]; selectedTimeframe: "AUTO" | "M1" | "M5" | "M15" | "H1" | "H4"; preRoll: number; postRoll: number }) => getTradeReplay(selectedSymbol, selectedRange[0].startOf("day").toISOString(), selectedRange[1].endOf("day").toISOString(), { timeframe: selectedTimeframe === "AUTO" ? undefined : selectedTimeframe, preRollCandles: preRoll, postRollCandles: postRoll }),
    onSuccess: (data) => { const start = data.initial_cursor; setReplay(data); setInitialCursor(start); setCursor(start); setPlaying(false); setSelectedTrade(null); },
  });
  const exportReplay = useMutation({
    mutationFn: async () => {
      if (!replay) throw new Error(t("replay.exportUnavailable"));
      setPlaying(false);
      const exportCursor = cursor;
      const result = await createTmfExport({
        trade_ids: replay.events.map((event) => event.trade_id),
        include_charts: includeCharts,
        redact_source_identity: redactSourceIdentity,
        replay: { symbol: replay.symbol, timeframe: replay.timeframe, from: replay.from, to: replay.to, candle_from: replay.candle_from, candle_to: replay.candle_to, candles: replay.candles, pre_roll_candles: replay.pre_roll_candles, post_roll_candles: replay.post_roll_candles, available_pre_roll_candles: replay.available_pre_roll_candles, initial_cursor: replay.initial_cursor, cursor: exportCursor },
      });
      await invoke("save_tmf_export", { exportId: result.export_id });
      return result;
    },
    onSuccess: () => setExportOpen(false),
  });

  useEffect(() => {
    if (indicatorPreferences.data) setIndicatorRequests(indicatorPreferences.data.indicators);
  }, [indicatorPreferences.data]);

  useEffect(() => { localStorage.setItem(REPLAY_DISPLAY_TIMEZONE_STORAGE_KEY, displayTimezone); }, [displayTimezone]);

  useEffect(() => {
    const activeIndicators = indicatorRequests.filter((item) => item.visible);
    if (!replay || !activeIndicators.length) { setIndicatorSeries([]); return; }
    let active = true;
    calculateIndicators({ symbol: replay.symbol, timeframe: replay.timeframe, candles: replay.candles, indicators: activeIndicators })
      .then((result) => { if (active) setIndicatorSeries(result.indicators); })
      .catch(() => { if (active) setIndicatorSeries([]); });
    return () => { active = false; };
  }, [replay, indicatorRequests]);

  useEffect(() => {
    if (!playing || !replay) return;
    const timer = window.setInterval(() => setCursor((current) => {
      if (current >= replay.candles.length - 1) { setPlaying(false); return current; }
      return current + 1;
    }), 900 / speed);
    return () => window.clearInterval(timer);
  }, [playing, replay, speed]);

  const toggleIndicator = (item: IndicatorPreferenceItem) => {
    indicatorScrollPositionRef.current = { x: window.scrollX, y: window.scrollY };
    setIndicatorRequests((current) => {
      const key = indicatorKey(item);
      const next = current.map((candidate) => indicatorKey(candidate) === key ? { ...candidate, visible: !candidate.visible } : candidate);
      saveIndicators.mutate(next);
      return next;
    });
  };

  const restoreIndicatorScroll = useCallback(() => {
    const position = indicatorScrollPositionRef.current;
    if (!position) return;
    window.scrollTo({ left: position.x, top: position.y, behavior: "instant" });
    window.requestAnimationFrame(() => window.scrollTo({ left: position.x, top: position.y, behavior: "instant" }));
    window.setTimeout(() => { window.scrollTo({ left: position.x, top: position.y, behavior: "instant" }); indicatorScrollPositionRef.current = null; }, 80);
  }, []);

  useLayoutEffect(() => {
    restoreIndicatorScroll();
  }, [indicatorRequests, restoreIndicatorScroll]);

  const selectSymbol = (value: string) => {
    const option = symbols.data?.find((item) => item.symbol === value);
    setSymbol(value);
    setRange(option ? [dayjs(option.available_from), dayjs(option.available_to)] : undefined);
    setReplay(null); setCursor(0); setInitialCursor(0); setPlaying(false); setSelectedTrade(null);
  };
  const load = () => { if (symbol && range) loadReplay.mutate({ selectedSymbol: symbol, selectedRange: range, selectedTimeframe: timeframe, preRoll: preRollCandles, postRoll: postRollCandles }); };
  const last = Math.max(0, (replay?.candles.length ?? 1) - 1);
  const hasCandles = Boolean(replay?.candles.length);
  const currentCandle = replay?.candles[cursor];
  const closedEvents = replay?.events.filter((event) => {
    const exitIndex = candleIndexAtOrBefore(replay.candles, event.close_time);
    return exitIndex >= 0 && exitIndex <= cursor;
  }) ?? [];
  const realizedNetProfit = closedEvents.reduce((total, event) => total + event.net_profit, 0);
  const duration = selectedTrade ? dayjs(selectedTrade.close_time).diff(dayjs(selectedTrade.open_time), "minute") : 0;

  return <Space direction="vertical" size="large" style={{ width: "100%" }}>
    <Card title={t("replay.title")}>
      {symbols.isPending ? <Spin /> : !symbols.data?.length ? <Empty description={t("replay.noTrades")} /> : <Space direction="vertical" size="small" style={{ width: "100%" }}>
        <Space align="center" size="middle" style={{ whiteSpace: "nowrap" }}>
          <Space size={8}><Typography.Text>{t("replay.symbol")}</Typography.Text><Select value={symbol} onChange={selectSymbol} placeholder={t("replay.selectSymbol")} style={{ width: 190 }} options={symbols.data.map((item) => ({ value: item.symbol, label: `${item.symbol} (${item.trade_count})` }))} /></Space>
          <Space size={8}><Typography.Text>{t("replay.range")}</Typography.Text><RangePicker value={range} onChange={(value) => value?.[0] && value[1] && setRange([value[0], value[1]])} disabled={!selectedSymbol} disabledDate={(date) => !selectedSymbol || date.isBefore(dayjs(selectedSymbol.available_from), "day") || date.isAfter(dayjs(selectedSymbol.available_to), "day")} style={{ width: 360 }} /></Space>
          <Button type="primary" onClick={load} disabled={!symbol || !range} loading={loadReplay.isPending}>{t("replay.load")}</Button>
        </Space>
        <Space align="center" size="middle" style={{ whiteSpace: "nowrap" }}>
          <Space size={8}><Typography.Text>{t("replay.timeframe")}</Typography.Text><Select value={timeframe} onChange={setTimeframe} style={{ width: 100 }} options={[{ value: "AUTO", label: t("replay.auto") }, ...["M1", "M5", "M15", "H1", "H4"].map((value) => ({ value, label: value }))]} /></Space>
          <Space size={8}><Typography.Text>{t("replay.displayTimezone")}</Typography.Text><Select value={displayTimezone} onChange={setDisplayTimezone} style={{ width: 130 }} options={REPLAY_DISPLAY_TIMEZONE_OPTIONS.map((value) => ({ value, label: replayTimezoneLabel(value, localTimezoneLabel) }))} /></Space>
          <Space size={8}><Typography.Text>{t("replay.preRoll")}</Typography.Text><InputNumber min={0} max={500} value={preRollCandles} onChange={(value) => setPreRollCandles(value ?? 20)} style={{ width: 72 }} /></Space>
          <Space size={8}><Typography.Text>{t("replay.postRoll")}</Typography.Text><InputNumber min={0} max={500} value={postRollCandles} onChange={(value) => setPostRollCandles(value ?? 20)} style={{ width: 72 }} /></Space>
        </Space>
      </Space>}
      {selectedSymbol && <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>{t("replay.available", { from: formatDisplayTime(selectedSymbol.available_from), to: formatDisplayTime(selectedSymbol.available_to) })}</Typography.Paragraph>}
      {loadReplay.error && <Alert type="error" showIcon message={(loadReplay.error as Error).message} />}
    </Card>
    {replay && <Card title={`${replay.symbol} · ${replay.timeframe}`} extra={<Space size="large"><Button onClick={() => setIndicatorModalOpen(true)}>{t("indicator.open")}</Button><Button onClick={() => setExportOpen(true)} disabled={!hasCandles}>{t("replay.export")}</Button><Statistic title={t("replay.realizedProfit")} value={realizedNetProfit} precision={2} valueStyle={{ color: realizedNetProfit >= 0 ? "#16a34a" : "#dc2626" }} prefix={realizedNetProfit >= 0 ? "+" : ""} /><Typography.Text type="secondary">{t("replay.closedCount", { closed: closedEvents.length, total: replay.selected_trade_count })} · {t("replay.preRollShown", { actual: replay.available_pre_roll_candles, requested: replay.pre_roll_candles })} · {t("replay.expanded", { from: formatDisplayTime(replay.candle_from), to: formatDisplayTime(replay.candle_to) })}</Typography.Text></Space>}>
      <ReplayChart candles={replay.candles} events={replay.events} cursor={cursor} animationDuration={Math.max(80, Math.min(500, 720 / speed))} displayTimezone={displayTimezone} indicators={indicatorSeries} indicatorPreferences={indicatorRequests} onIndicatorToggle={toggleIndicator} onChartRendered={restoreIndicatorScroll} onTradeSelect={setSelectedTrade} />
      {hasCandles && <><Space wrap align="center" style={{ width: "100%", justifyContent: "space-between", marginTop: 18 }}>
        <Space><Button onClick={() => { setPlaying(false); setCursor((value) => Math.max(initialCursor, value - 1)); }} disabled={cursor <= initialCursor}>{t("replay.back")}</Button><Button type="primary" onClick={() => setPlaying((value) => !value)} disabled={cursor >= last}>{playing ? t("replay.pause") : t("replay.play")}</Button><Button onClick={() => { setPlaying(false); setCursor((value) => Math.min(last, value + 1)); }} disabled={cursor >= last}>{t("replay.forward")}</Button><Segmented<1 | 2 | 5> value={speed} onChange={setSpeed} options={[{ value: 1, label: "1x" }, { value: 2, label: "2x" }, { value: 5, label: "5x" }]} /></Space>
        <Space><Statistic title={t("replay.progress")} value={`${cursor + 1} / ${replay.candles.length}`} /><Typography.Text>{currentCandle ? formatDisplayTime(currentCandle.time) : ""}</Typography.Text></Space>
      </Space>
      <div style={{ marginTop: 10 }}>
        <Slider aria-label={t("replay.seek")} min={initialCursor} max={last} step={1} value={cursor} disabled={initialCursor >= last} tooltip={{ formatter: (value) => value === undefined || !replay.candles[value] ? "" : `${formatDisplayTime(replay.candles[value].time)} · ${value + 1} / ${replay.candles.length}` }} onChange={(value) => { setPlaying(false); setCursor(value); }} />
        <Space style={{ width: "100%", justifyContent: "space-between" }}><Typography.Text type="secondary">{t("replay.seekStart")} · {formatDisplayTime(replay.candles[initialCursor].time)}</Typography.Text><Typography.Text type="secondary">{t("replay.seekEnd")} · {formatDisplayTime(replay.candles[last].time)}</Typography.Text></Space>
      </div></>}
    </Card>}
    <IndicatorPanel definitions={indicatorDefinitions.data?.indicators ?? []} open={indicatorModalOpen} value={indicatorRequests} onCancel={() => setIndicatorModalOpen(false)} onChange={(next) => { setIndicatorRequests(next); saveIndicators.mutate(next); }} />
    <Modal title={t("replay.exportTitle")} open={exportOpen} onCancel={() => setExportOpen(false)} onOk={() => exportReplay.mutate()} okText={t("replay.exportGenerate")} confirmLoading={exportReplay.isPending} okButtonProps={{ disabled: !hasCandles }}>
      {replay && <Space direction="vertical" style={{ width: "100%" }}><Typography.Paragraph>{t("replay.exportDescription")}</Typography.Paragraph><Descriptions size="small" column={1} items={[{ key: "range", label: t("replay.range"), children: `${formatDisplayTime(replay.from)} — ${formatDisplayTime(replay.to)}` }, { key: "cursor", label: t("replay.exportCursor"), children: currentCandle ? `${formatDisplayTime(currentCandle.time)} · ${cursor + 1} / ${replay.candles.length}` : "—" }, { key: "trades", label: t("replay.tradeCount", { count: replay.selected_trade_count }), children: t("replay.exportLifecycle") }]} /><Space><Typography.Text>{t("export.charts")}</Typography.Text><Switch checked={includeCharts} onChange={setIncludeCharts} /></Space><Typography.Text type="secondary">{t("export.chartsHint")}</Typography.Text><Space><Typography.Text>{t("export.redact")}</Typography.Text><Switch checked={redactSourceIdentity} onChange={setRedactSourceIdentity} /></Space>{exportReplay.error && <Alert type="error" showIcon message={(exportReplay.error as Error).message} />}</Space>}
    </Modal>
    <Drawer open={Boolean(selectedTrade)} onClose={() => setSelectedTrade(null)} title={selectedTrade ? `${selectedTrade.symbol} · ${selectedTrade.ticket}` : ""} width={520}>
      {selectedTrade && <Descriptions bordered size="small" column={1} items={[
        { key: "id", label: t("replay.tradeId"), children: selectedTrade.trade_id }, { key: "source", label: t("trades.source"), children: selectedTrade.source }, { key: "direction", label: t("trades.direction"), children: selectedTrade.direction }, { key: "open", label: t("trades.open"), children: `${formatDisplayTime(selectedTrade.open_time)} · ${selectedTrade.open_price}` }, { key: "close", label: t("trades.close"), children: `${formatDisplayTime(selectedTrade.close_time)} · ${selectedTrade.close_price}` }, { key: "volume", label: t("trades.volume"), children: selectedTrade.volume }, { key: "net", label: t("trades.netProfit"), children: selectedTrade.net_profit }, { key: "profit", label: t("replay.profit"), children: selectedTrade.profit }, { key: "cost", label: t("replay.costs"), children: `${selectedTrade.commission} / ${selectedTrade.swap}` }, { key: "holding", label: t("replay.holding"), children: `${duration} min` }, { key: "sl", label: t("market.stopLoss"), children: selectedTrade.stop_loss ?? "—" }, { key: "tp", label: t("market.takeProfit"), children: selectedTrade.take_profit ?? "—" }, { key: "reason", label: t("replay.closeReason"), children: selectedTrade.close_reason ?? "—" },
      ]} />}
    </Drawer>
  </Space>;
}
