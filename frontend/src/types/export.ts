import type { MarketCandle } from "./market";

export interface TmfReplaySnapshot {
  symbol: string;
  timeframe: "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1";
  from: string;
  to: string;
  candle_from: string;
  candle_to: string;
  candles: MarketCandle[];
  pre_roll_candles: number;
  post_roll_candles: number;
  available_pre_roll_candles: number;
  initial_cursor: number;
  cursor: number;
}

export interface TmfExportRequest {
  trade_ids?: number[];
  symbol?: string;
  direction?: "BUY" | "SELL";
  source?: "MT5" | "CSV";
  from_time?: string;
  to_time?: string;
  include_charts: boolean;
  redact_source_identity: boolean;
  replay?: TmfReplaySnapshot;
}

export interface TmfExportResponse {
  export_id: string;
  filename: string;
  trade_count: number;
  include_charts: boolean;
  redact_source_identity: boolean;
  validation_passed: boolean;
  statistics: Record<string, unknown>;
}
