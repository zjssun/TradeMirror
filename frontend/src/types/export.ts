export interface TmfExportRequest {
  trade_ids?: number[];
  symbol?: string;
  direction?: "BUY" | "SELL";
  source?: "MT5" | "CSV";
  from_time?: string;
  to_time?: string;
  include_charts: boolean;
  redact_source_identity: boolean;
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
