import { useState } from "react";
import { EyeInvisibleOutlined, EyeOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Descriptions, Space, Tag, Tooltip } from "antd";

import { useI18n } from "../../app/i18n";
import type { Mt5StatusResponse } from "../../types/mt5";

interface Props { status: Mt5StatusResponse; loading: boolean; onReconnect: () => void; }

export function Mt5StatusCard({ status, loading, onReconnect }: Props) {
  const { t } = useI18n();
  const [accountVisible, setAccountVisible] = useState(false);
  const connected = status.state === "connected";
  const privateValue = { filter: accountVisible ? "none" : "blur(6px)", userSelect: accountVisible ? "text" as const : "none" as const, transition: "filter 0.15s" };
  const accountLabel = accountVisible ? t("mt5.hideAccount") : t("mt5.showAccount");
  return <Card title={t("mt5.title")} extra={<Button loading={loading} onClick={onReconnect}>{connected ? t("mt5.reconnect") : t("mt5.connect")}</Button>}><Space direction="vertical" size="middle" style={{ width: "100%" }}><Tag color={connected ? "success" : "warning"} style={{ width: "fit-content" }}>{connected ? t("mt5.connected") : t("mt5.disconnected")}</Tag>{status.diagnostic && <Alert type="warning" message={status.diagnostic.message} description={status.diagnostic.remediation} showIcon />}{status.terminal && <Descriptions column={1} size="small" bordered><Descriptions.Item label={t("mt5.terminalVersion")}>{status.terminal.version ?? t("mt5.unknown")}</Descriptions.Item><Descriptions.Item label={t("mt5.terminalPath")}>{status.terminal.path ?? t("mt5.unknown")}</Descriptions.Item></Descriptions>}{status.account && <Descriptions column={2} size="small" bordered title={t("mt5.accountInfo")} extra={<Tooltip title={accountLabel}><Button type="text" aria-label={accountLabel} icon={accountVisible ? <EyeOutlined /> : <EyeInvisibleOutlined />} onClick={() => setAccountVisible((visible) => !visible)} /></Tooltip>}><Descriptions.Item label={t("mt5.account")}><span style={privateValue}>{status.account.login}</span></Descriptions.Item><Descriptions.Item label={t("mt5.server")}><span style={privateValue}>{status.account.server}</span></Descriptions.Item><Descriptions.Item label={t("mt5.balance")}><span style={privateValue}>{status.account.balance.toFixed(2)} {status.account.currency}</span></Descriptions.Item><Descriptions.Item label={t("mt5.equity")}><span style={privateValue}>{status.account.equity.toFixed(2)} {status.account.currency}</span></Descriptions.Item></Descriptions>}</Space></Card>;
}
