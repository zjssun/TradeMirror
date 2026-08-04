import { invoke } from "@tauri-apps/api/core";

import type { BatchAnalyzeResponse, TradeContext } from "../types/analysis";
import type { Insights, InsightFilters } from "../types/insights";
import type { TmfExportRequest, TmfExportResponse } from "../types/export";
import type { EngineRuntime, HealthResponse } from "../types/engine";
import type { CandleResponse, CandleTimeframe } from "../types/market";
import type { Mt5StatusResponse, SymbolListResponse } from "../types/mt5";
import type { ImportPreview, ImportResult } from "../types/importer";
import type { TradeDateRange, TradeListResponse, TradeSource } from "../types/trade";
import type { ReplayResponse, ReplaySymbolOption } from "../types/replay";
import type { DataSourceStatus, DataSourceSync, Mt5HistorySyncRequest, Mt5HistorySyncResponse } from "../types/datasource";
import type { TradingNarrative, TradingNarrativeFilters } from "../types/narrative";

let runtime: EngineRuntime | null = null;

export async function getEngineRuntime(): Promise<EngineRuntime> {
  if (!runtime) {
    runtime = await invoke<EngineRuntime>("get_engine_runtime");
  }
  return runtime;
}

async function engineFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const connection = await getEngineRuntime();
  const response = await fetch(`${connection.baseUrl}${path}`, {
    ...options,
    headers: {
      "X-TradeMirror-Token": connection.token,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: { message?: string } | string } | null;
    const detail = typeof body?.detail === "object" ? body.detail.message : body?.detail;
    throw new Error(detail ?? `本地分析引擎请求失败（HTTP ${response.status}）`);
  }

  return response.json() as Promise<T>;
}

export function getEngineHealth(): Promise<HealthResponse> {
  return engineFetch<HealthResponse>("/health");
}

export function getMt5Status(): Promise<Mt5StatusResponse> {
  return engineFetch<Mt5StatusResponse>("/mt5/status");
}

export function connectMt5(): Promise<Mt5StatusResponse> {
  return engineFetch<Mt5StatusResponse>("/mt5/connect", { method: "POST" });
}

export function getMt5Symbols(query: string): Promise<SymbolListResponse> {
  const params = new URLSearchParams({ visible_only: "true", limit: "300" });
  if (query.trim()) params.set("query", query.trim());
  return engineFetch<SymbolListResponse>(`/mt5/symbols?${params}`);
}

export function getReplaySymbols(): Promise<ReplaySymbolOption[]> {
  return engineFetch<ReplaySymbolOption[]>("/market/replay/symbols");
}

export function getTradeReplay(symbol: string, from: string, to: string, options: { timeframe?: CandleTimeframe; preRollCandles: number; postRollCandles: number }): Promise<ReplayResponse> {
  const params = new URLSearchParams({ symbol, from, to, pre_roll_candles: String(options.preRollCandles), post_roll_candles: String(options.postRollCandles) });
  if (options.timeframe) params.set("timeframe", options.timeframe);
  return engineFetch<ReplayResponse>(`/market/replay?${params}`);
}

export function getMarketCandles(
  symbol: string,
  timeframe: CandleTimeframe,
  from: string,
  to: string,
): Promise<CandleResponse> {
  const params = new URLSearchParams({ symbol, timeframe, from, to });
  return engineFetch<CandleResponse>(`/market/candles?${params}`);
}

export async function previewTradeCsv(file: File): Promise<ImportPreview> {
  const connection = await getEngineRuntime();
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${connection.baseUrl}/trades/import/preview`, {
    method: "POST",
    headers: { "X-TradeMirror-Token": connection.token },
    body: form,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? "无法解析 CSV 文件。");
  }
  return response.json() as Promise<ImportPreview>;
}

export function commitTradeImport(previewId: string, filename: string, mapping: Record<string, string>): Promise<ImportResult> {
  return engineFetch<ImportResult>("/trades/import/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preview_id: previewId, filename, mapping }),
  });
}

export function getTradeDateRange(): Promise<TradeDateRange> {
  return engineFetch<TradeDateRange>("/trades/date-range");
}

export function getDataSourceStatuses(): Promise<DataSourceStatus[]> {
  return engineFetch<DataSourceStatus[]>("/datasources");
}

export function getLastMt5Sync(): Promise<DataSourceSync | null> {
  return engineFetch<DataSourceSync | null>("/datasources/mt5/last-sync");
}

export function syncMt5History(request: Mt5HistorySyncRequest): Promise<Mt5HistorySyncResponse> {
  return engineFetch<Mt5HistorySyncResponse>("/datasources/mt5/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export function getTrades(page: number, pageSize: number, symbol?: string, direction?: string, source?: TradeSource): Promise<TradeListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (symbol) params.set("symbol", symbol);
  if (direction) params.set("direction", direction);
  if (source) params.set("source", source);
  return engineFetch<TradeListResponse>(`/trades?${params}`);
}

export function deleteTrade(tradeId: number): Promise<{ deleted_count: number }> {
  return engineFetch<{ deleted_count: number }>(`/trades/${tradeId}`, { method: "DELETE" });
}

export function deleteTrades(tradeIds: number[]): Promise<{ deleted_count: number }> {
  return engineFetch<{ deleted_count: number }>("/trades/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trade_ids: tradeIds }),
  });
}

export function getTradeContext(tradeId: number): Promise<TradeContext> {
  return engineFetch<TradeContext>(`/trades/${tradeId}/context`);
}

export function analyzeTrade(tradeId: number): Promise<TradeContext> {
  return engineFetch<TradeContext>(`/trades/${tradeId}/analyze`, { method: "POST" });
}

export function analyzeAllTrades(): Promise<BatchAnalyzeResponse> {
  return engineFetch<BatchAnalyzeResponse>("/analysis/trades", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ all: true }),
  });
}

export function deleteAllTrades(): Promise<{ deleted_count: number }> {
  return engineFetch<{ deleted_count: number }>("/trades/all", { method: "DELETE" });
}

export function analyzeTrades(tradeIds: number[]): Promise<BatchAnalyzeResponse> {
  return engineFetch<BatchAnalyzeResponse>("/analysis/trades", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ trade_ids: tradeIds }),
  });
}

export function createTmfExport(request: TmfExportRequest): Promise<TmfExportResponse> {
  return engineFetch<TmfExportResponse>("/exports/tmf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
}

export function getTradingNarrative(filters: TradingNarrativeFilters): Promise<TradingNarrative> {
  return engineFetch<TradingNarrative>("/narratives/trading-process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(filters),
  });
}

export function getInsights(filters: InsightFilters = {}): Promise<Insights> {
  const params = new URLSearchParams();
  if (filters.symbol) params.set("symbol", filters.symbol);
  if (filters.direction) params.set("direction", filters.direction);
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  return engineFetch<Insights>(`/insights?${params}`);
}
