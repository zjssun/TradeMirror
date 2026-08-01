import { Modal, Result, Space, Tag } from "antd";

import { useI18n } from "../../app/i18n";
import type { BatchAnalyzeResponse } from "../../types/analysis";

interface Props { result: BatchAnalyzeResponse | null; onClose: () => void; }

export function BatchReviewResult({ result, onClose }: Props) {
  const { t } = useI18n();
  return <Modal title={t("review.batchTitle")} open={Boolean(result)} footer={null} onCancel={onClose}>{result && <><Result status={result.failed_count ? "warning" : "success"} title={t("review.processed", { count: result.requested_count })} subTitle={<Space wrap><Tag color="green">{t("review.completed", { count: result.completed_count })}</Tag><Tag color="gold">{t("review.insufficient", { count: result.insufficient_data_count })}</Tag><Tag color="red">{t("review.failed", { count: result.failed_count })}</Tag></Space>} />{result.items.filter((item) => item.status !== "completed").map((item) => <div key={item.trade_id} style={{ marginBottom: 8 }}><Tag color={item.status === "failed" ? "red" : "gold"}>{item.status === "failed" ? t("datasource.failed") : t("review.insufficient", { count: "" }).trim()}</Tag>{t("review.trade", { id: item.trade_id })}{item.error_message ?? t("review.noDiagnostic")}</div>)}</>}</Modal>;
}
