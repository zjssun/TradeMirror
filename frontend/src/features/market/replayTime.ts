import type { Time } from "lightweight-charts";

export type ReplayDisplayTimezone = "utc" | "local" | `offset:${number}`;

export const DEFAULT_REPLAY_DISPLAY_TIMEZONE: ReplayDisplayTimezone = "utc";
export const REPLAY_DISPLAY_TIMEZONE_STORAGE_KEY = "trademirror-replay-display-timezone";
export const REPLAY_DISPLAY_TIMEZONE_OPTIONS: ReplayDisplayTimezone[] = [
  "utc", "local", ...Array.from({ length: 27 }, (_, index) => `offset:${(index - 12) * 60}` as ReplayDisplayTimezone),
];

function isDisplayTimezone(value: string | null): value is ReplayDisplayTimezone {
  return value === "utc" || value === "local" || /^offset:-?\d+$/.test(value ?? "") && REPLAY_DISPLAY_TIMEZONE_OPTIONS.includes(value as ReplayDisplayTimezone);
}

export function readReplayDisplayTimezone(): ReplayDisplayTimezone {
  const value = localStorage.getItem(REPLAY_DISPLAY_TIMEZONE_STORAGE_KEY);
  return isDisplayTimezone(value) ? value : DEFAULT_REPLAY_DISPLAY_TIMEZONE;
}

export function replayTimezoneLabel(value: ReplayDisplayTimezone, localLabel: string): string {
  if (value === "utc") return "UTC";
  if (value === "local") return localLabel;
  const minutes = Number(value.slice("offset:".length));
  const sign = minutes >= 0 ? "+" : "-";
  const absolute = Math.abs(minutes);
  return `UTC${sign}${String(Math.floor(absolute / 60)).padStart(2, "0")}:${String(absolute % 60).padStart(2, "0")}`;
}

function dateFromValue(value: string | Time): Date {
  if (typeof value === "string") {
    const utcValue = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`;
    return new Date(utcValue);
  }
  return new Date(Number(value) * 1000);
}

function displayParts(value: string | Time, timezone: ReplayDisplayTimezone) {
  const date = dateFromValue(value);
  if (timezone === "local") return { year: date.getFullYear(), month: date.getMonth() + 1, day: date.getDate(), hour: date.getHours(), minute: date.getMinutes() };
  const offset = timezone === "utc" ? 0 : Number(timezone.slice("offset:".length));
  const shifted = new Date(date.getTime() + offset * 60_000);
  return { year: shifted.getUTCFullYear(), month: shifted.getUTCMonth() + 1, day: shifted.getUTCDate(), hour: shifted.getUTCHours(), minute: shifted.getUTCMinutes() };
}

export function formatReplayDateTime(value: string | Time, timezone: ReplayDisplayTimezone, localLabel: string): string {
  const parts = displayParts(value, timezone);
  return `${parts.year}-${String(parts.month).padStart(2, "0")}-${String(parts.day).padStart(2, "0")} ${String(parts.hour).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")} ${replayTimezoneLabel(timezone, localLabel)}`;
}

export function formatReplayChartTime(value: Time, timezone: ReplayDisplayTimezone): string {
  const parts = displayParts(value, timezone);
  return `${String(parts.day).padStart(2, "0")} ${String(parts.hour).padStart(2, "0")}:${String(parts.minute).padStart(2, "0")}`;
}
