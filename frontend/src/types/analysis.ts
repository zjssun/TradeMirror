import type { CandleTimeframe, MarketCandle } from "./market";

export type TradeContextStatus = "completed" | "insufficient_data" | "not_analyzed";

export type BatchAnalyzeStatus = "completed" | "insufficient_data" | "failed";

export interface BatchAnalyzeItem {
  trade_id: number;
  status: BatchAnalyzeStatus;
  error_message: string | null;
}

export interface BatchAnalyzeResponse {
  requested_count: number;
  completed_count: number;
  insufficient_data_count: number;
  failed_count: number;
  items: BatchAnalyzeItem[];
}

export interface TradeContext {
  trade_id: number;
  status: TradeContextStatus;
  timeframe: CandleTimeframe | null;
  data_quality: Record<string, unknown>;
  market_context: Record<string, unknown>;
  execution: Record<string, unknown>;
  candles: MarketCandle[];
  error_message: string | null;
  analyzed_at: string | null;
}
