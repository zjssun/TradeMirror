import { useMutation, useQuery } from "@tanstack/react-query";
import { Alert, Card, Descriptions, Result, Space, Spin, Tag } from "antd";

import { connectMt5, getDataSourceStatuses, getLastMt5Sync, getMt5Status } from "../../api/engineClient";
import { useI18n } from "../../app/i18n";
import { Mt5StatusCard } from "../mt5/Mt5StatusCard";
import { Mt5HistorySyncPanel } from "./Mt5HistorySyncPanel";

export function DataSourcePage() {
  const { t } = useI18n();
  const statuses = useQuery({ queryKey: ["datasource-statuses"], queryFn: getDataSourceStatuses, retry: false });
  const mt5 = useQuery({ queryKey: ["mt5-status"], queryFn: getMt5Status, retry: false });
  const lastSync = useQuery({ queryKey: ["mt5-last-sync"], queryFn: getLastMt5Sync, retry: false });
  const reconnect = useMutation({ mutationFn: connectMt5, onSuccess: () => { void mt5.refetch(); void statuses.refetch(); } });
  if (statuses.isPending || mt5.isPending) return <Spin size="large" />;
  if (statuses.isError || mt5.isError || !mt5.data) return <Result status="warning" title={t("datasource.unavailable")} subTitle={statuses.error?.message ?? mt5.error?.message} />;
  const mt5Source = statuses.data?.find((item) => item.source === "MT5");
  return <Space direction="vertical" size="large" style={{ width: "100%" }}><Alert type="info" showIcon message={t("datasource.primary")} description={t("datasource.primaryDescription")} /><Mt5StatusCard status={mt5.data} loading={reconnect.isPending} onReconnect={() => reconnect.mutate()} />{lastSync.data && <Card size="small" title={t("datasource.recentSync")}><Descriptions size="small" column={{ xs: 1, sm: 2 }}><Descriptions.Item label={t("datasource.completedAt")}>{lastSync.data.completed_at ? new Date(lastSync.data.completed_at).toLocaleString() : t("datasource.inProgress")}</Descriptions.Item><Descriptions.Item label={t("datasource.status")}><Tag color={lastSync.data.status === "completed" ? "success" : "error"}>{lastSync.data.status === "completed" ? t("datasource.success") : t("datasource.failed")}</Tag></Descriptions.Item><Descriptions.Item label={t("datasource.symbol")}>{lastSync.data.symbol ?? t("datasource.allSymbols")}</Descriptions.Item><Descriptions.Item label={t("datasource.writtenTrades")}>{lastSync.data.trade_count}</Descriptions.Item>{lastSync.data.diagnostic && <Descriptions.Item label={t("datasource.diagnostic")} span={2}>{lastSync.data.diagnostic}</Descriptions.Item>}</Descriptions></Card>}{mt5.data.state === "connected" ? <Mt5HistorySyncPanel /> : <Card title={t("datasource.csvImport")}><Alert type="warning" showIcon message={t("datasource.mt5Unavailable")} description={mt5Source?.remediation ?? t("datasource.connectOrImport")} /></Card>}</Space>;
}
