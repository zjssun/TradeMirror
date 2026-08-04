import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Card, Checkbox, DatePicker, Form, Result, Select, Space, Spin } from "antd";
import dayjs, { type Dayjs } from "dayjs";

import { getMt5Symbols, syncMt5History } from "../../api/engineClient";
import { useI18n } from "../../app/i18n";

export function Mt5HistorySyncPanel() {
  const { t } = useI18n();
  const [symbolQuery, setSymbolQuery] = useState("");
  const [symbol, setSymbol] = useState<string>();
  const [range, setRange] = useState<[Dayjs, Dayjs]>([dayjs().subtract(30, "day"), dayjs()]);
  const [syncAll, setSyncAll] = useState(false);
  const queryClient = useQueryClient();
  const symbols = useQuery({ queryKey: ["mt5-symbols", symbolQuery], queryFn: () => getMt5Symbols(symbolQuery) });
  const sync = useMutation({ mutationFn: () => syncMt5History({ symbol, sync_all: syncAll, from_time: range[0].startOf("day").toISOString(), to_time: range[1].endOf("day").toISOString() }), onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ["trades"] }); void queryClient.invalidateQueries({ queryKey: ["trade-date-range"] }); void queryClient.invalidateQueries({ queryKey: ["replay-symbols"] }); void queryClient.invalidateQueries({ queryKey: ["mt5-last-sync"] }); } });
  if (symbols.isPending) return <Spin />;
  return <Card title={t("sync.title")}><Form layout="vertical" onFinish={() => sync.mutate()}><Space wrap align="end"><Form.Item label={t("sync.symbol")}><Select allowClear showSearch filterOption={false} value={symbol} onSearch={setSymbolQuery} onChange={setSymbol} style={{ width: 280 }} placeholder={t("sync.allSymbols")} options={symbols.data?.items.map((item) => ({ value: item.name, label: `${item.name} — ${item.description}` }))} /></Form.Item><Form.Item label={t("sync.closeRange")}><DatePicker.RangePicker disabled={syncAll} value={range} allowClear={false} onChange={(value) => value?.[0] && value[1] && setRange(value as [Dayjs, Dayjs])} /></Form.Item><Form.Item label={<span>&nbsp;</span>}><Checkbox checked={syncAll} onChange={(event) => setSyncAll(event.target.checked)}>{t("sync.allHistory")}</Checkbox></Form.Item><Form.Item label={<span>&nbsp;</span>}><Button htmlType="submit" type="primary" loading={sync.isPending}>{t("sync.submit")}</Button></Form.Item></Space></Form>{sync.isError && <Alert style={{ marginTop: 16 }} type="error" showIcon message={sync.error.message} />}{sync.data && <Result style={{ paddingBottom: 0 }} status="success" title={t("sync.complete")} subTitle={t("sync.summary", { imported: sync.data.imported_count, updated: sync.data.updated_count, skipped: sync.data.skipped_count })} />}</Card>;
}
