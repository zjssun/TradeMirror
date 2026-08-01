import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Alert, Button, Card, Descriptions, Select, Space, Steps, Table, Upload } from "antd";
import type { UploadProps } from "antd";

import { commitTradeImport, previewTradeCsv } from "../../api/engineClient";
import { useI18n } from "../../app/i18n";
import type { ImportPreview, ImportResult } from "../../types/importer";

export function TradeImportPage() {
  const { t } = useI18n();
  const [preview, setPreview] = useState<ImportPreview>(); const [mapping, setMapping] = useState<Record<string, string>>({}); const [result, setResult] = useState<ImportResult>();
  const upload = useMutation({ mutationFn: previewTradeCsv, onSuccess: (data) => { setPreview(data); setMapping(Object.fromEntries(data.mappings.filter((item) => item.source).map((item) => [item.target, item.source!] ))); setResult(undefined); } });
  const commit = useMutation({ mutationFn: () => commitTradeImport(preview!.preview_id, preview!.filename, mapping), onSuccess: setResult });
  const props: UploadProps = { accept: ".csv", maxCount: 1, beforeUpload: (file) => { upload.mutate(file); return false; }, showUploadList: false };
  return <Space direction="vertical" size="large" style={{ width: "100%" }}><Card title={t("import.title")}><Alert type="info" showIcon message={t("datasource.primary")} description={t("import.description")} style={{ marginBottom: 20 }} /><Steps current={result ? 2 : preview ? 1 : 0} items={[{ title: t("import.select") }, { title: t("import.map") }, { title: t("import.complete") }]} /><Space direction="vertical" size="middle" style={{ width: "100%", marginTop: 24 }}><Upload {...props}><Button loading={upload.isPending}>{t("import.chooseFile")}</Button></Upload>{upload.isError && <Alert type="error" message={upload.error.message} showIcon />}{preview && <><Descriptions size="small" bordered column={3}><Descriptions.Item label={t("import.file")}>{preview.filename}</Descriptions.Item><Descriptions.Item label={t("import.encoding")}>{preview.encoding}</Descriptions.Item><Descriptions.Item label={t("import.delimiter")}>{preview.delimiter === "\t" ? "Tab" : preview.delimiter}</Descriptions.Item></Descriptions><Card size="small" title={t("import.mapping")}><Space wrap>{preview.mappings.map((item) => <Space key={item.target}><span>{t(`field.${item.target}`)}</span><Select value={mapping[item.target]} onChange={(value) => setMapping((current) => ({ ...current, [item.target]: value }))} allowClear options={preview.columns.map((column) => ({ value: column, label: column }))} style={{ width: 180 }} /></Space>)}</Space></Card><Table size="small" scroll={{ x: true }} dataSource={preview.sample_rows} rowKey={(_, index) => String(index)} pagination={false} columns={preview.columns.map((column) => ({ title: column, dataIndex: column, key: column }))} /><Button type="primary" loading={commit.isPending} onClick={() => commit.mutate()}>{t("import.confirm")}</Button>{commit.isError && <Alert type="error" message={commit.error.message} showIcon />}</>}{result && <Alert type="success" showIcon message={t("import.result", { imported: result.imported_rows, duplicates: result.duplicate_rows, errors: result.error_rows })} description={result.issues.slice(0, 5).map((issue) => `#${issue.row_number}: ${issue.message}`).join("；")} />}</Space></Card></Space>;
}
