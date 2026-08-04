# 技术指标系统（Indicator Engine）

## 选型

第一阶段使用 [`ta`](https://github.com/bukosabino/ta) 作为唯一的指标计算库，版本由 `engine/pyproject.toml` 固定在 `>=0.11,<0.12`。

- **未采用 TA-Lib：** TA-Lib 依赖原生库和 DLL，会增加 Windows 便携版及 PyInstaller one-file 打包的收集与兼容性风险。
- **未采用 pandas-ta：** 虽然可用，但需要额外确认 Python 3.12 发行包兼容性；本项目已有 pandas/numpy，纯 Python 的 `ta` 可满足第一阶段指标且打包风险更低。
- **不在前端计算：** React 只绘制 Engine 返回的序列，所有公式均在 Python Provider 中执行。

## 已支持指标与默认参数

| 位置 | 指标 | 默认参数 |
| --- | --- | --- |
| 主图 | SMA | 20 |
| 主图 | EMA | 20、50、200 |
| 主图 | Bollinger Bands | period=20，std_dev=2 |
| 副图 | RSI | 14 |
| 副图 | MACD | fast=12，slow=26，signal=9 |
| 副图 | ATR | 14 |

## 数据和无未来函数规则

计算请求接收标准 OHLCV 数据。Engine 会统一 UTC 时间、按时间排序、按时间戳去重，并拒绝不合法 OHLC、负成交量/点差或非有限数值。

- 每个点仅由同一根及之前的 K 线生成；
- 预热期及无效数值不会输出；不会出现 `NaN` 或 `Infinity`；
- 响应点包含原始 UTC 时间和 `source_index`；
- 回放前端只绘制 `source_index <= cursor` 的点，因此回退、拖动和播放均不会泄露后续指标；
- 交易开仓快照仅使用开仓前已完整收盘的 K 线；离场快照只使用离场时刻及之前已完整收盘的 K 线。

OHLC 数据只能表达区间，MFE、MAE 及部分风险分析均是区间近似，不应解释为逐笔成交路径。

## API

所有接口使用本地 Engine Token 鉴权。

### `GET /indicators/definitions`

返回 Provider 名称和版本，以及每种指标的中英文名称、默认参数、参数范围、主图/副图位置与展示字段。

### `POST /indicators/calculate`

请求：

```json
{
  "symbol": "XAUUSD",
  "timeframe": "M15",
  "candles": [{"time":"2025-01-01T00:00:00Z","open":1,"high":2,"low":0.5,"close":1.5,"tick_volume":1,"spread":0,"real_volume":0}],
  "indicators": [{"name":"EMA","parameters":{"period":20}}]
}
```

响应中简单指标返回 `series: [{time,value,source_index}]`；布林带和 MACD 返回按上/中/下轨或 macd/signal/histogram 分组的序列。

## TMF

TMF 的交易上下文会包含开仓/离场指标快照，并在 manifest 的 `indicator_engine` 中记录 Provider、版本、schema 以及对应的已收盘 K 线时间边界策略。默认不导出完整指标序列，避免归档过大。

## 打包验证

`ta` 为纯 Python 库，理论上不需要 TA-Lib DLL。发布前仍必须运行 `scripts/build_engine.bat`，并在无 Python 的干净 Windows 环境启动冻结后的 `TradeMirrorEngine.exe`，调用 definitions 和 calculate 接口验证所有六种指标。
