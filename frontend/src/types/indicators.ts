import type { CandleTimeframe, MarketCandle } from "./market";

export type IndicatorName = "SMA" | "EMA" | "BOLLINGER_BANDS" | "RSI" | "MACD" | "ATR";
export type IndicatorPane = "main" | "separate";

export interface IndicatorRequest {
  name: IndicatorName;
  parameters: Record<string, number>;
}

export interface IndicatorPoint {
  time: string;
  value: number;
  source_index: number;
}

export interface IndicatorSeries {
  id: string;
  name: IndicatorName;
  display_name: string;
  pane: IndicatorPane;
  parameters: Record<string, number>;
  series: IndicatorPoint[] | Record<string, IndicatorPoint[]>;
}

export interface IndicatorCalculationResponse {
  symbol: string;
  timeframe: CandleTimeframe;
  candle_count: number;
  provider: string;
  provider_version: string;
  indicators: IndicatorSeries[];
}

export interface IndicatorDefinition {
  name: IndicatorName;
  display_name: { "zh-CN": string; "en-US": string };
  pane: IndicatorPane;
  defaults: Record<string, number>;
  parameter_ranges: Record<string, { min: number; max: number }>;
  series_fields: string[];
}

export interface IndicatorDefinitionsResponse {
  provider: string;
  provider_version: string;
  indicators: IndicatorDefinition[];
}

export interface IndicatorCalculationRequest {
  symbol: string;
  timeframe: CandleTimeframe;
  candles: MarketCandle[];
  indicators: IndicatorRequest[];
}

export interface IndicatorPreferenceItem extends IndicatorRequest {
  visible: boolean;
}

export interface IndicatorPreferences {
  indicators: IndicatorPreferenceItem[];
}
