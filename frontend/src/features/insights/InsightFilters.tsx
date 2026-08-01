import type { Dayjs } from "dayjs";
import { Alert, Button, DatePicker, Form, Input, Select, Space } from "antd";

import { useI18n } from "../../app/i18n";
import type { TradingNarrativeFilters } from "../../types/narrative";
import { useTradeDateRange } from "../trades/useTradeDateRange";

export function InsightFilters({ onChange }: { onChange: (filters: TradingNarrativeFilters) => void }) {
  const { t } = useI18n(); const [form] = Form.useForm(); const range = useTradeDateRange(); const disabledDate = (date: Dayjs) => !range.hasTrades || date.isBefore(range.from, "day") || date.isAfter(range.to, "day");
  return <Form form={form} layout="inline" onFinish={(values) => onChange({ symbol: values.symbol || undefined, direction: values.direction, source: values.source, from_time: values.range[0].startOf("day").toISOString(), to_time: values.range[1].endOf("day").toISOString() })}><Space wrap align="start"><Form.Item name="symbol"><Input placeholder={t("filters.symbol")} /></Form.Item><Form.Item name="direction"><Select allowClear placeholder={t("trades.direction")} style={{ width: 110 }} options={[{ value: "BUY", label: "BUY" }, { value: "SELL", label: "SELL" }]} /></Form.Item><Form.Item name="source"><Select allowClear placeholder={t("trades.source")} style={{ width: 110 }} options={[{ value: "MT5", label: "MT5" }, { value: "CSV", label: "CSV" }]} /></Form.Item><Form.Item name="range" rules={[{ required: true, message: t("filters.selectRange") }]} extra={range.hasTrades ? t("filters.availableRange", { from: range.from?.format("YYYY-MM-DD") ?? "", to: range.to?.format("YYYY-MM-DD") ?? "" }) : t("filters.noTrades")}><DatePicker.RangePicker disabled={range.isPending || !range.hasTrades} disabledDate={disabledDate} /></Form.Item><Form.Item><Button type="primary" htmlType="submit">{t("filters.generate")}</Button></Form.Item></Space>{range.isError && <Alert type="warning" message={t("filters.rangeError")} />}</Form>;
}
