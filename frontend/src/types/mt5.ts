export type Mt5ConnectionState = "connected" | "disconnected" | "unavailable";

export interface Mt5Diagnostic {
  code: string;
  message: string;
  remediation: string;
}

export interface TerminalSummary {
  path: string | null;
  version: string | null;
  connected: boolean;
}

export interface AccountSummary {
  login: number;
  server: string;
  company: string | null;
  currency: string;
  balance: number;
  equity: number;
}

export interface Mt5StatusResponse {
  state: Mt5ConnectionState;
  terminal: TerminalSummary | null;
  account: AccountSummary | null;
  diagnostic: Mt5Diagnostic | null;
}

export interface SymbolResponse {
  name: string;
  description: string;
  path: string;
  digits: number;
  point: number;
  visible: boolean;
}

export interface SymbolListResponse {
  items: SymbolResponse[];
  total: number;
  fetched_at: string;
}
