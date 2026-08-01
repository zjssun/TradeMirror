import { Alert, Button, Card, Col, Descriptions, Result, Row, Space, Spin, Statistic, Tag } from "antd";
import { useQuery } from "@tanstack/react-query";

import { getEngineHealth, getInsights } from "../../api/engineClient";
import { useI18n } from "../../app/i18n";
import { DistributionChart } from "../insights/DistributionChart";
import { EquityCurveChart } from "../insights/EquityCurveChart";

export function DashboardPage() {
  const { t } = useI18n();
  const healthQuery = useQuery({ queryKey: ["engine-health"], queryFn: getEngineHealth, retry: false });
  const insights = useQuery({ queryKey: ["insights"], queryFn: () => getInsights() });
  if (healthQuery.isPending) return <Result icon={<Spin size="large" />} title={t("dashboard.connecting")} />;
  if (healthQuery.isError) return <Result status="warning" title={t("dashboard.unavailable")} subTitle={healthQuery.error.message} extra={<Button type="primary" onClick={() => void healthQuery.refetch()}>{t("dashboard.reconnect")}</Button>} />;
  const health = healthQuery.data;
  const stats = insights.data?.statistics ?? {};
  return <Space direction="vertical" size="large" style={{ width: "100%" }}><Alert message={t("dashboard.connected")} description={t("dashboard.description")} type="success" showIcon /><Card title={t("dashboard.overview")}>{insights.isPending ? <Spin /> : <Row gutter={[16, 16]}><Col xs={12} md={4}><Statistic title={t("dashboard.tradeCount")} value={Number(stats.trade_count ?? 0)} /></Col><Col xs={12} md={4}><Statistic title={t("dashboard.netProfit")} value={Number(stats.net_profit ?? 0)} precision={2} valueStyle={{ color: Number(stats.net_profit ?? 0) >= 0 ? "#16a34a" : "#dc2626" }} /></Col><Col xs={12} md={4}><Statistic title={t("dashboard.winRate")} value={Number(stats.win_rate ?? 0) * 100} suffix="%" precision={1} /></Col><Col xs={12} md={4}><Statistic title={t("dashboard.profitFactor")} value={Number(stats.profit_factor ?? 0)} precision={2} /></Col><Col xs={12} md={4}><Statistic title={t("dashboard.lossStreak")} value={Number(stats.longest_loss_streak ?? 0)} /></Col><Col xs={12} md={4}><Statistic title={t("dashboard.completedReviews")} value={insights.data?.completed_context_count ?? 0} /></Col></Row>}</Card>{insights.data && <Row gutter={[16, 16]}><Col xs={24} lg={12}><EquityCurveChart points={insights.data.equity_curve} /></Col><Col xs={24} lg={12}><DistributionChart values={stats.by_symbol as Record<string, unknown>} /></Col></Row>}<Card title={t("dashboard.engineStatus")}><Descriptions column={1} bordered><Descriptions.Item label={t("dashboard.runningStatus")}><Tag color="success">{health.status}</Tag></Descriptions.Item><Descriptions.Item label={t("dashboard.engineVersion")}>{health.engine_version}</Descriptions.Item><Descriptions.Item label={t("dashboard.databaseStatus")}>{health.database}</Descriptions.Item></Descriptions></Card></Space>;
}
