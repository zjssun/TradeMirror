import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, Card, Col, Empty, Row, Statistic, Spin } from "antd";

import { getInsights } from "../../api/engineClient";
import type { InsightFilters as Filters } from "../../types/insights";
import { DistributionChart } from "./DistributionChart";
import { EquityCurveChart } from "./EquityCurveChart";
import { InsightFilters } from "./InsightFilters";

export function TraderProfilePage() {
  const [filters, setFilters] = useState<Filters>({});
  const insights = useQuery({ queryKey: ["insights", filters], queryFn: () => getInsights(filters) });
  if (insights.isPending) return <Spin />;
  if (insights.isError) return <Alert type="error" message={insights.error.message} />;
  const data = insights.data, stats = data.statistics, profile = data.profile;
  return <div><Card title="交易者画像" style={{ marginBottom: 16 }}><InsightFilters onChange={setFilters} /></Card>{Number(stats.trade_count) === 0 ? <Empty description="该筛选范围没有交易记录" /> : <><Row gutter={[16, 16]}><Col xs={24} md={6}><Card><Statistic title="交易风格" value={String(profile.style ?? "UNKNOWN")} /></Card></Col><Col xs={24} md={6}><Card><Statistic title="方向偏好" value={String(profile.direction_preference ?? "UNKNOWN")} /></Card></Col><Col xs={24} md={6}><Card><Statistic title="主要品种" value={String(profile.dominant_symbol ?? "—")} /></Card></Col><Col xs={24} md={6}><Card><Statistic title="品种集中度" value={Number(profile.symbol_concentration ?? 0) * 100} suffix="%" precision={1} /></Card></Col></Row><Card title="风险标签" style={{ marginTop: 16 }}>{Array.isArray(profile.risk_labels) && profile.risk_labels.length ? profile.risk_labels.join(" · ") : "未发现规则定义的风险标签"}</Card><Row gutter={[16, 16]} style={{ marginTop: 16 }}><Col xs={24} lg={12}><EquityCurveChart points={data.equity_curve} /></Col><Col xs={24} lg={12}><DistributionChart values={stats.by_symbol as Record<string, unknown>} /></Col></Row></>}</div>;
}
