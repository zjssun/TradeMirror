export type CandleTimeframe = "M1" | "M5" | "M15" | "M30" | "H1" | "H4" | "D1";

export interface MarketCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  tick_volume: number;
  spread: number;
  real_volume: number;
}

export interface CandleResponse {
  symbol: string;
  timeframe: CandleTimeframe;
  from: string;
  to: string;
  candles: MarketCandle[];
  cached_count: number;
  fetched_count: number;
}
