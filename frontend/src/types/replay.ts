import type { MarketCandle, CandleTimeframe } from "./market";

export interface ReplaySymbolOption {
  symbol: string;
  available_from: string;
  available_to: string;
  trade_count: number;
}

export interface ReplayTradeEvent {
  trade_id: number;
  source: string;
  ticket: string;
  symbol: string;
  direction: string;
  open_time: string;
  close_time: string;
  open_price: number;
  close_price: number;
  volume: number;
  profit: number;
  commission: number;
  swap: number;
  net_profit: number;
  stop_loss: number | null;
  take_profit: number | null;
  close_reason: string | null;
}

export interface ReplayResponse {
  symbol: string;
  timeframe: CandleTimeframe;
  from: string;
  to: string;
  candle_from: string;
  candle_to: string;
  candles: MarketCandle[];
  events: ReplayTradeEvent[];
  cached_count: number;
  fetched_count: number;
  pre_roll_candles: number;
  post_roll_candles: number;
  selected_trade_count: number;
  selected_net_profit: number;
  initial_cursor: number;
  available_pre_roll_candles: number;
}
