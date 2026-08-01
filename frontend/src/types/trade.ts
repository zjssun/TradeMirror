export type TradeSource = "MT5" | "CSV";

export interface Trade {
  id: number;
  import_batch_id: number | null;
  source: TradeSource;
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

export interface TradeDateRange {
  from_time: string | null;
  to_time: string | null;
}

export interface TradeListResponse {
  items: Trade[];
  total: number;
  page: number;
  page_size: number;
}
