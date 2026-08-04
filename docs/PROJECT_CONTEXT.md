# TradeMirror 项目背景

## 产品定位

TradeMirror 是面向 Windows 的本地历史交易复盘桌面应用。它将 MT5 已平仓交易、对应历史 K 线与本地分析结果关联，帮助用户进行单笔/批量复盘、时间序列回放、交易过程叙事、技术指标观察和 TMF 材料导出。

应用关注历史数据整理、复盘和分析，不提供市场预测、交易建议、下单或自动交易。所有交易数据、缓存、SQLite 数据库、日志和 TMF 归档先在本机处理；是否将导出的材料提交给外部 AI 服务完全由用户决定。

## 核心流程

```text
MT5 已平仓历史 / CSV
        ↓
本地 SQLite 交易记录与行情缓存
        ↓
市场关联、交易复盘、指标和叙事
        ↓
本地生成 TMF
        ↓
用户自主选择是否交给 AI 分析
```

## 数据源与本地架构

- **主数据源：** 已登录 Windows MT5 终端的已平仓订单/成交历史和历史 K 线。
- **兼容数据源：** CSV，用于 MT5 不可用、历史迁移或其他平台导出的交易数据。
- **桌面宿主：** Tauri/Rust 负责启动桌面程序、本地 Engine 和原生文件保存。
- **界面：** React 单页 UI 通过启动令牌访问本机 FastAPI Engine。
- **数据：** SQLite 保存交易、行情缓存、复盘上下文和应用偏好；运行时数据默认位于 `%APPDATA%\TradeMirror\`，不写入解压后的便携包目录。

## 前端与桌面库

| 类别 | 库/工具 | 作用 |
| --- | --- | --- |
| UI | React 19、React DOM | 组件界面与状态渲染。 |
| 类型与构建 | TypeScript 5.7、Vite 6、`@vitejs/plugin-react` | 类型检查、开发服务器和前端生产构建。 |
| UI 组件 | Ant Design 5 | 表单、表格、弹窗、日期选择和本地化组件。 |
| 请求状态 | TanStack React Query 5 | 本地 Engine 请求、缓存和失效刷新。 |
| 图表 | TradingView Lightweight Charts 5 | K 线、交易标注、复盘播放器和技术指标 Pane 绘制；不在前端计算指标公式。 |
| 桌面 | Tauri 2、Tauri Dialog Plugin、Rust | 桌面窗口、原生保存对话框和本地进程协调。 |

## Python Engine 库

| 类别 | 库/工具 | 作用 |
| --- | --- | --- |
| Web API | FastAPI、Uvicorn、Pydantic | 本机 API、启动令牌保护、请求/响应校验。 |
| 数据 | SQLAlchemy、SQLite | 本地交易、行情缓存、分析结果和偏好保存。 |
| MT5 | MetaTrader5 | 读取终端/账户摘要、品种、已平仓历史和历史 K 线。 |
| 数据处理 | NumPy、pandas、`ta` | K 线处理和 SMA、EMA、BOLL、RSI、MACD、ATR 指标计算。 |
| 导出 | Pillow | 生成 TMF 可选图表。 |
| 测试与打包 | pytest、httpx、PyInstaller、Hatchling | API 测试、冻结 Engine 和 Python 包构建。 |

Python 运行时要求为 64 位 Python 3.12+。

## 应用内语言切换

- 支持 **简体中文（`zh-CN`）** 与 **English（`en-US`）**。
- 顶部语言选择器切换应用语言；选项通过 `localStorage["trademirror-language"]` 保存，重启后恢复。未保存或非 `en-US` 值默认使用中文。
- 前端使用项目内的 React `I18nProvider` 和内置字典，不依赖 i18next/react-intl；`ConfigProvider` 同步切换 Ant Design 的 `zh_CN` / `en_US` locale。
- 切换范围仅限固定 UI 文案、按钮、表单和 Ant Design 组件。导入的原始交易数据、后端诊断和生成的交易叙事保留原始语言与语义，不自动翻译。

## 安全与 MT5 执行边界

**禁止交易执行是项目的硬性约束。** Engine 不调用下单、订单检查、订单修改、仓位修改、平仓或模拟成交 API；不会修改订单、仓位或账户交易状态，也不收集/保存 MT5 登录凭据。

正常 MT5 访问仅用于读取终端/账户摘要、品种信息、已平仓订单/成交历史和历史 K 线。为了请求某个有效但在 MT5 Market Watch 中不可见的品种行情，客户端可能调用 `symbol_select(symbol, True)` 使该品种显示在 Market Watch；这不是交易执行，也不会创建、关闭或修改交易。

`engine/tests/test_mt5_read_only.py` 对 Engine 源码扫描 `order_send`、`order_check`、`positions_modify` 和 `order_modify` 等禁止调用，作为防回归保护；它是代码层保障，不是 MT5 权限沙箱。应用自身仍会在本地 SQLite、缓存、TMF 和日志目录中写入数据。

## 当前发布形态

当前发布形态为 Windows 免安装绿色版。便携包包含桌面 EXE、本地 Engine EXE、配置和占位目录；最终用户不需要安装 Python、Node.js、npm、pip 或独立数据库。Tauri 依赖 Windows WebView2。
