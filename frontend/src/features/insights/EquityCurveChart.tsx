import { Card, Empty } from "antd";

import { useI18n } from "../../app/i18n";

export function EquityCurveChart({ points }: { points: { equity: number }[] }) {
  const { t } = useI18n();
  if (!points.length) return <Card title={t("chart.equity")}><Empty description={t("chart.noTrades")} /></Card>;
  const values = points.map((point) => point.equity);
  const low = Math.min(...values), high = Math.max(...values), span = high - low || 1;
  const coordinates = points.map((point, index) => `${index / Math.max(1, points.length - 1) * 100},${100 - (point.equity - low) / span * 90 - 5}`).join(" ");
  return <Card title={t("chart.equity")}><svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: 220 }}><polyline points={coordinates} fill="none" stroke="#1677ff" strokeWidth="1.5" vectorEffect="non-scaling-stroke" /></svg></Card>;
}
