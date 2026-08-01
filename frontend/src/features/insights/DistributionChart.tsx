import { Card, Empty, Progress, Space, Typography } from "antd";

import { useI18n } from "../../app/i18n";

export function DistributionChart({ values }: { values: Record<string, unknown> }) {
  const { t } = useI18n();
  const rows = Object.entries(values) as [string, { trade_count?: number; net_profit?: number }][];
  const maximum = Math.max(1, ...rows.map(([, value]) => value.trade_count ?? 0));
  if (!rows.length) return <Card title={t("chart.distribution")}><Empty description={t("chart.noTrades")} /></Card>;
  return <Card title={t("chart.distribution")}><Space direction="vertical" style={{ width: "100%" }}>{rows.map(([name, value]) => <div key={name}><Typography.Text>{name} · {t("chart.netProfit")} {value.net_profit?.toFixed(2) ?? t("common.none")}</Typography.Text><Progress percent={(value.trade_count ?? 0) / maximum * 100} showInfo={false} /></div>)}</Space></Card>;
}
