export type TradeSource = "MT5" | "CSV";

export interface DataSourceStatus {
  source: TradeSource;
  available: boolean;
  recommended: boolean;
  message: string;
  remediation?: string | null;
}

export interface DataSourceSync {
  source: TradeSource;
  account_id: string | null;
  symbol: string | null;
  from_time: string;
  to_time: string;
  status: string;
  trade_count: number;
  diagnostic: string | null;
  completed_at: string | null;
}

export interface Mt5HistorySyncRequest {
  symbol?: string;
  sync_all?: boolean;
  from_time: string;
  to_time: string;
}

export interface Mt5HistorySyncResponse {
  source: "MT5";
  account_id: string;
  imported_count: number;
  updated_count: number;
  skipped_count: number;
  from_time: string;
  to_time: string;
}
