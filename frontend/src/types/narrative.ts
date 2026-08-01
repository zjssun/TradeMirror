export interface TradingNarrativeFilters {
  symbol?: string;
  direction?: "BUY" | "SELL";
  source?: "MT5" | "CSV";
  from_time: string;
  to_time: string;
}

export interface NarrativeTimelineEvent {
  type: "open" | "close";
  trade_id: number;
  time: string;
  symbol: string;
  direction: "BUY" | "SELL";
  action: string;
  price: number;
  volume: number;
  net_profit?: number;
  source: "MT5" | "CSV";
  outside_selected_range: boolean;
}

export interface NarrativeMarket {
  symbol: string;
  timeframe: string;
  from_time: string;
  to_time: string;
  candle_count: number;
  phases: Array<Record<string, unknown>>;
  diagnostics: string[];
}

export interface TradingNarrative {
  filters: Record<string, unknown>;
  trade_count: number;
  narrative: string;
  timeline: NarrativeTimelineEvent[];
  markets: NarrativeMarket[];
  diagnostics: string[];
}
