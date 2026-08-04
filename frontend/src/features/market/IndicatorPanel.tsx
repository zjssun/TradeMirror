import { Button, InputNumber, Modal, Space, Tag, Typography } from "antd";

import { useI18n } from "../../app/i18n";
import type { IndicatorDefinition, IndicatorName, IndicatorPreferenceItem, IndicatorRequest } from "../../types/indicators";

interface Props {
  definitions: IndicatorDefinition[];
  open: boolean;
  value: IndicatorPreferenceItem[];
  onCancel: () => void;
  onChange: (value: IndicatorPreferenceItem[]) => void;
}

const DEFAULTS: IndicatorPreferenceItem[] = [
  { name: "SMA", parameters: { period: 20 }, visible: true },
  { name: "EMA", parameters: { period: 20 }, visible: true },
  { name: "EMA", parameters: { period: 50 }, visible: true },
  { name: "EMA", parameters: { period: 200 }, visible: true },
  { name: "BOLLINGER_BANDS", parameters: { period: 20, std_dev: 2 }, visible: true },
  { name: "RSI", parameters: { period: 14 }, visible: true },
  { name: "MACD", parameters: { fast: 12, slow: 26, signal: 9 }, visible: true },
  { name: "ATR", parameters: { period: 14 }, visible: true },
];

const ABBREVIATIONS: Record<IndicatorName, string> = {
  SMA: "SMA", EMA: "EMA", BOLLINGER_BANDS: "BOLL", RSI: "RSI", MACD: "MACD", ATR: "ATR",
};

export function indicatorKey(item: IndicatorRequest): string {
  return `${item.name}:${Object.entries(item.parameters).sort(([left], [right]) => left.localeCompare(right)).map(([name, value]) => `${name}=${value}`).join(",")}`;
}

export function indicatorLabel(item: IndicatorRequest): string {
  const values = Object.values(item.parameters).join(", ");
  return `${ABBREVIATIONS[item.name]} ${values}`;
}

export function defaultIndicatorPreferences(): IndicatorPreferenceItem[] {
  return DEFAULTS.map((item) => ({ ...item, parameters: { ...item.parameters } }));
}

export function IndicatorPanel({ definitions, open, value, onCancel, onChange }: Props) {
  const { t } = useI18n();
  const definitionFor = (name: IndicatorName) => definitions.find((item) => item.name === name);
  const add = (definition: IndicatorDefinition) => {
    const parameters = { ...definition.defaults };
    if (definition.name === "SMA" || definition.name === "EMA") {
      const periods = value.filter((item) => item.name === definition.name).map((item) => item.parameters.period);
      parameters.period = [20, 50, 100, 200].find((period) => !periods.includes(period)) ?? Math.max(...periods, 1) + 1;
    }
    const candidate: IndicatorPreferenceItem = { name: definition.name, parameters, visible: true };
    if (value.some((item) => indicatorKey(item) === indicatorKey(candidate))) return;
    onChange([...value, candidate]);
  };
  const toggle = (current: IndicatorPreferenceItem) => onChange(value.map((item) => indicatorKey(item) === indicatorKey(current) ? { ...item, visible: !item.visible } : item));
  const update = (current: IndicatorPreferenceItem, parameter: string, next: number | null) => {
    if (next === null) return;
    const updated = { ...current, parameters: { ...current.parameters, [parameter]: next } };
    if (value.some((item) => indicatorKey(item) !== indicatorKey(current) && indicatorKey(item) === indicatorKey(updated))) return;
    onChange(value.map((item) => indicatorKey(item) === indicatorKey(current) ? updated : item));
  };
  const remove = (current: IndicatorPreferenceItem) => onChange(value.filter((item) => indicatorKey(item) !== indicatorKey(current)));

  return <Modal title={t("indicator.settings")} open={open} onCancel={onCancel} footer={<Button onClick={onCancel}>{t("indicator.done")}</Button>} width={720}>
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Space wrap>
        {definitions.map((definition) => <Button key={definition.name} size="small" onClick={() => add(definition)} disabled={definition.name !== "SMA" && definition.name !== "EMA" && value.some((item) => item.name === definition.name)}>{definition.name === "SMA" ? t("indicator.addSma") : definition.name === "EMA" ? t("indicator.addEma") : `${t("indicator.add")} ${ABBREVIATIONS[definition.name]}`}</Button>)}
        <Button size="small" onClick={() => onChange(defaultIndicatorPreferences())}>{t("indicator.restoreDefaults")}</Button>
      </Space>
      {value.length === 0 ? <Typography.Text type="secondary">{t("indicator.empty")}</Typography.Text> : value.map((item) => {
        const definition = definitionFor(item.name);
        if (!definition) return null;
        return <div key={indicatorKey(item)} style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
          <Tag role="button" tabIndex={0} onClick={() => toggle(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") toggle(item); }} style={{ cursor: "pointer", marginInlineEnd: 0, color: item.visible ? "#1677ff" : "#595959", background: item.visible ? "#e6f4ff" : "#262626", borderColor: item.visible ? "#91caff" : "#434343" }}>{indicatorLabel(item)}</Tag>
          {Object.entries(definition.parameter_ranges).map(([parameter, range]) => <Space key={parameter} size={4}><Typography.Text type="secondary">{t(`indicator.parameter.${parameter}`)}</Typography.Text><InputNumber size="small" min={range.min} max={range.max} step={parameter === "std_dev" ? 0.1 : 1} value={item.parameters[parameter]} onChange={(next) => update(item, parameter, next)} style={{ width: 76 }} /></Space>)}
          <Button size="small" danger onClick={() => remove(item)}>{t("indicator.remove")}</Button>
        </div>;
      })}
    </Space>
  </Modal>;
}
