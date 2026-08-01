export interface Insights {
  filters: Record<string, unknown>;
  statistics: Record<string, unknown>;
  profile: Record<string, unknown>;
  prompt: string;
  completed_context_count: number;
  insufficient_data_context_count: number;
  equity_curve: { time: string; equity: number; net_profit: number }[];
}

export interface InsightFilters { symbol?: string; direction?: "BUY" | "SELL"; from?: string; to?: string; }
