<p align="center">
  <img src="md_img/banner.png" alt="TradeMirror banner" width="100%">
</p>

<h1 align="center">TradeMirror</h1>

<p align="center">
  <strong>连接 MT5，重构交易数据，转化为 AI 可理解的交易洞察</strong><br>
  <strong>Connect with MT5, transform trading data, and turn it into AI-powered trading insights.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Tauri-v2-24C8DB?logo=tauri&logoColor=white" alt="Tauri v2">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React 19">
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/MT5-Read--only-1E40AF" alt="MT5 read-only">
  <img src="https://img.shields.io/badge/Privacy-Local--first-16A34A" alt="Local-first privacy">
</p>

<p align="center">
  <a href="#中文">中文</a> · <a href="#english">English</a>
</p>

---

## 下载 / Download

### Windows 免安装绿色版 / Windows Portable Edition

从 [GitHub Releases](https://github.com/zjssun/TradeMirror/releases) 下载最新的 `TradeMirror_Portable_v*.zip`，解压后双击 `TradeMirror.exe` 即可启动。无需安装 Python、Node.js、npm、pip 或独立数据库。  
Download the latest `TradeMirror_Portable_v*.zip` from [GitHub Releases](https://github.com/zjssun/TradeMirror/releases), extract it, and launch `TradeMirror.exe`. Python, Node.js, npm, pip, and a separate database installation are not required.

---

## 更新历史 / Update History

- **2026-08-04 — 整体优化与功能增强 / General Improvements and Feature Enhancements**
  - 复盘图表增加指标功能，目前支持指标有SMA、EMA、BOLL、RSI、MACD、ATR。
    Added indicator functionality to replay charts, currently supporting indicators such as SMA, EMA, BOLL, RSI, MACD, and ATR.
  - 用户可以选择图表时区，以适配不同经纪商的服务器时区。  
    Users can select the chart timezone to accommodate different broker server timezones.
  - 优化复盘图表中的交易标签样式。  
    Improved the styling of trade labels in replay charts.
  - 在“交易记录”中新增“复盘全部”和“删除全部”按钮。  
    Added “Review All” and “Delete All” buttons to Trade Records.
- **2026-08-03 — 交易复盘播放器 / Trade Replay Player**  
  新增按时间顺序播放历史 K 线的复盘页面，支持周期与前后市场窗口设置、播放控制、进度跳转、交易标记及动态已实现净收益。  
  Added chronological historical-candle playback with configurable timeframes and market windows, playback controls, seeking, trade markers, and dynamically realized net profit.

---

## 中文

### TradeMirror 是什么？

TradeMirror 是一款面向交易复盘的本地桌面软件。它将已平仓交易记录与对应时间范围内的 MT5 K 线数据结合起来，帮助你回看每笔交易发生时的市场环境，并整理为适合交给 AI 进一步分析的交易过程材料。

软件专注于**历史数据整理、复盘和分析**，不是交易终端，也不提供行情预测、下单或自动交易功能。

### 核心原则

- **本地优先**：本地 FastAPI 引擎、SQLite 数据库和桌面界面协同运行；应用不会自动将数据上传到第三方服务。
- **MT5 禁止交易执行**：仅读取已平仓历史、行情 K 线及必要的终端/账户摘要；不会下单、检查订单、修改订单或仓位、平仓、模拟成交，也不会收集交易账户密码。为读取有效但不可见品种的行情，应用可能仅将其显示到 MT5“市场报价”中；这不会改变任何订单、仓位或账户交易状态。
- **MT5 优先，兼容 CSV**：优先从 Windows MetaTrader 5 终端同步历史记录；也支持 CSV 导入，用于历史迁移或导入其他经纪商、平台导出的数据。
- **控制权属于用户**：TMF 导出文件在本地生成；是否将其提交给任意 AI 服务完全由你自行决定。

### 功能

| 功能 | 说明 |
| --- | --- |
| MT5 已平仓交易同步 | 从已登录的 MT5 终端以只读方式同步已平仓交易；支持指定日期范围或全部可用历史，并保留数据来源与同步状态。 |
| CSV 导入与字段映射 | 预览 CSV 的编码、分隔符和样例数据；映射字段并确认后导入，适用于历史迁移及其他平台导出的交易数据。 |
| 交易记录与数据管理 | 按品种、方向、来源和日期筛选交易；支持查看详情、删除单笔或选中记录，以及“复盘全部”和“删除全部”。 |
| 交易概览与洞察 | 在本地汇总交易数量、净利润、胜率、盈亏比、连续亏损和品种表现，并按筛选条件生成统计洞察。 |
| 单笔交易复盘 | 在 K 线图上标注开仓、平仓、止损、止盈、价格和手数；展示入场市场环境、执行表现、数据质量及 MFE/MAE 等区间近似指标。 |
| 批量交易复盘 | 对选中的交易或筛选结果批量生成市场上下文和执行分析；开仓指标仅使用开仓前已完整收盘的 K 线，避免前视偏差。 |
| 交易复盘播放器 | 按单一品种和日期范围逐根播放历史 K 线；支持周期、交易前后窗口、图表时区、播放速度、单步前进/回退和进度跳转，交易标记与已实现净收益会随播放位置同步更新。 |
| 技术指标系统 | 本地 Python Indicator Engine 统一计算 SMA、EMA、布林带、RSI、MACD 和 ATR；支持参数调整和本地偏好保存，主图叠加线与 RSI/MACD/ATR 副图均严格裁剪到复盘游标，不提前显示未来值。 |
| 交易过程叙事 | 将指定时间范围内的交易序列、时间线和市场 K 线阶段组织成连续、可复制的交易过程文本。 |
| TMF 导出 | 在本地生成可供 AI 复盘的 `.tmf` 归档，包含交易、上下文、事件、叙事、时间线、统计和校验信息；支持图表、回放快照、来源脱敏，并记录指标计算来源与版本信息。 |

### 界面预览

#### 交易概览

![交易概览页面](md_img/overview.png)

在本地汇总交易数量、净利润、胜率、盈亏比、最长连亏和已完成复盘，并展示净利润曲线与品种分布。

#### 交易记录

![交易记录页面](md_img/TradeRecords.png)

在交易记录中筛选、选择或清理本地交易；打开单笔复盘后，可查看标注开平仓位置、价格和手数的行情图，并检查入场市场环境、执行指标与数据质量。

#### 交易复盘播放器

![交易复盘播放器](md_img/TradeReplay.png)

选择单一品种与日期范围后，可设置 K 线周期以及交易前后市场窗口；历史 K 线会按时间顺序播放，也可通过进度条直接跳转。交易开平仓标记、连接线与已实现净收益会随播放位置同步更新。

#### 交易过程叙事

![交易过程叙事页面](md_img/narrative.png)

在所选时间范围内，将交易与同一时期的 K 线市场阶段组合为连续、可复制的交易过程描述。

#### TMF 导出

![TMF 导出页面](md_img/trade.png)

导出的 TMF 文件可以上传给 AI 进行交易分析。你可以按品种、来源、方向和日期筛选交易，并选择是否导出图表，以及是否对订单和来源标识进行脱敏。

### 日常使用

1. **准备 MT5（可选但推荐）**：在 Windows 上安装并登录 MetaTrader 5 终端；启动 TradeMirror 后，在“数据源”中检查连接状态。
2. **导入交易历史**：在“数据源”中同步 MT5 已平仓交易，并选择日期范围或全部历史。重复同步会自动去重。无法使用 MT5 时，可上传 CSV，在确认字段映射和数据预览后导入。
3. **浏览与清理交易**：在“交易记录”中按品种、方向、来源和日期筛选；可删除单笔、选中批次或全部交易。
4. **复盘单笔交易**：从交易记录打开单笔复盘，点击“生成分析”或“重新分析”。系统读取所需历史 K 线并生成 UTC+0 行情回放；开仓和平仓箭头会落在对应 K 线或此前最近的一根 K 线上。
5. **播放交易过程**：打开“交易复盘播放器”，选择品种和日期范围，并按需设置 K 线周期及交易前后市场窗口。加载后可先观察入场前行情，再播放、单步前进或拖动进度条定位；已实现净收益会在平仓 K 线出现时动态更新。
6. **生成时间范围叙事**：在“交易过程叙事”中选择包含交易数据的日期范围和筛选条件，生成由交易时间线与市场阶段组成的连续文本，并复制到你选择的 AI 工具中。
7. **导出 TMF 材料**：在“TMF 导出”中设置筛选条件、图表和数据脱敏选项，生成后保存到本地。整个导出过程均在本机完成。

### 运行与开发

#### 前置条件

- Windows 10/11
- Python 3.12 或 3.13
- Node.js（建议使用当前 LTS 版本）
- Rust stable 工具链（用于 Tauri 桌面端）
- MetaTrader 5 Windows 桌面终端（仅 MT5 同步与行情回放需要）

#### 安装依赖

以下示例使用 Git Bash；在 PowerShell 中请根据环境调整虚拟环境命令。

```bash
# 后端引擎
cd engine
python -m venv .venv
./.venv/Scripts/pip install -e ".[dev]"

# 前端
cd ../frontend
npm install
```

#### 启动前端开发服务器

```bash
cd frontend
npm run dev
```

默认开发地址为 `http://localhost:1420`。

#### 启动桌面应用

```bash
cd desktop/tauri
cargo tauri dev
```

#### 构建 Windows 免安装绿色版

在安装了 64 位 Python 3.12+、Node.js、Rust、Cargo 和 Tauri CLI 的 Windows x64 发布环境中运行：

```bat
scripts\package_portable.bat
```

构建链路如下：

1. `build_engine.bat` 创建发布虚拟环境、安装 `engine[dev,package]`、运行完整 pytest，并通过 PyInstaller 构建单文件无控制台的 `TradeMirrorEngine.exe`。
2. `build_desktop.bat` 运行 `npm ci`、`npm run build`（TypeScript 类型检查与 Vite 构建），再执行 `cargo tauri build --no-bundle -- --locked`，生成 `TradeMirror.exe`。
3. `package_portable.bat` 组装便携目录、生成 `dist\TradeMirror_Portable_v1.0.zip` 与 `dist\TradeMirror_Portable_v1.0.zip.sha256`，并检查 ZIP 中的桌面程序、Engine、配置及 data/log/resources 文档等 7 个必需路径。

最终用户只需解压 ZIP 并运行 `TradeMirror.exe`，无需安装 Python、Node.js、npm、pip 或独立数据库。Tauri 依赖 WebView2，而 Windows 10/11 通常已预装该组件。

运行时数据会保存到解压目录之外：

```text
%APPDATA%\TradeMirror\
├── database\trademirror.db
├── tmf\
├── cache\
├── import-previews\
└── logs\engine\engine.log
```

#### 验证测试、构建与发布前检查

```bash
# 后端测试
cd engine
./.venv/Scripts/python.exe -m pytest

# 前端生产构建与类型检查
cd frontend
npm run build
```

使用 PowerShell 核验便携包 SHA-256：

```powershell
Get-FileHash .\dist\TradeMirror_Portable_v1.0.zip -Algorithm SHA256
Get-Content .\dist\TradeMirror_Portable_v1.0.zip.sha256
```

两处的哈希值应一致。打包脚本会执行 Engine pytest、前端构建、PyInstaller/Tauri 构建、ZIP 必需路径检查和 checksum 文件生成；**它不会**启动解压后的 `TradeMirror.exe` 或冻结的 `TradeMirrorEngine.exe`，也不会调用 health endpoint 或执行端到端 smoke test。发布前应在干净 Windows 环境手工解压并启动应用，确认本地 Engine、`%APPDATA%\TradeMirror` 数据/日志目录、可选 MT5 同步和无订单/仓位变动。

### 数据与安全说明

- 引擎仅绑定本机回环地址 `127.0.0.1`。
- 桌面端与本地引擎之间使用启动令牌进行通信保护。
- TradeMirror 不会执行任何 MT5 交易操作，也不会读取或保存 MT5 登录凭据；为请求历史行情，可能将有效但不可见品种显示在 MT5“市场报价”中，该操作不会改变订单、仓位或账户交易状态。
- 界面语言切换仅影响软件自身的固定 UI 文案；后端生成的叙事、诊断内容和导入的原始业务数据会保留原始语言与语义。
- 在将交易数据、叙事或 TMF 文件发送至外部 AI 服务前，请自行确认该服务的数据处理政策以及你的合规要求。

---

## English

### What is TradeMirror?

TradeMirror is a local desktop application for reviewing trading history. It combines closed-trade records with MT5 candlestick data from the relevant time windows, helping you revisit the market context of each trade and prepare structured trading-process material for further AI-assisted analysis.

The application focuses on **historical-data organization, review, and analysis**. It is not a trading terminal and does not provide market forecasting, order placement, or automated execution.

### Core principles

- **Local-first**: the FastAPI engine, SQLite database, and desktop UI run locally. The application does not automatically upload your data to third-party services.
- **MT5 execution is prohibited**: it reads closed-trade history, market candles, and necessary terminal/account summaries only. It never places/checks orders, modifies orders or positions, closes trades, simulates execution, or collects trading-account passwords. To fetch candles for a valid but hidden symbol, it may only make that symbol visible in MT5 Market Watch; this does not change any order, position, or account trading state.
- **MT5 first, CSV compatible**: synchronize history from the Windows MetaTrader 5 terminal when available, with CSV import as a fallback for migration or data exported from other brokers and platforms.
- **You control sharing**: TMF export files are generated locally. Whether you provide them to any AI service is entirely your decision.

### Features

| Feature | Description |
| --- | --- |
| MT5 closed-trade sync | Read-only synchronization of closed trades from a signed-in MT5 terminal, for a selected date range or all available history, while retaining source and sync status. |
| CSV import and field mapping | Inspect CSV encoding, delimiter, and sample rows; map fields before importing data from migrations or other platforms. |
| Trade records and data management | Filter trades by symbol, direction, source, and date; inspect details, delete individual or selected records, and use **Review All** or **Delete All**. |
| Trading overview and insights | Locally summarize trade count, net profit, win rate, profit factor, losing streaks, and symbol performance, with filterable statistical insights. |
| Per-trade review | Mark entry, exit, stop loss, take profit, price, and volume on candle charts; inspect entry context, execution quality, data quality, and OHLC-based MFE/MAE approximations. |
| Batch trade review | Generate market-context and execution analysis for selected or filtered trades. Entry indicators use only fully closed candles before entry to avoid look-ahead bias. |
| Trade Replay Player | Play historical candles one by one for a symbol and date range. Configure timeframe, pre/post-trade windows, chart timezone, speed, stepping, and seeking; markers and realized net profit update with the playback position. |
| Technical indicators | The local Python Indicator Engine calculates SMA, EMA, Bollinger Bands, RSI, MACD, and ATR. It supports parameter editing and local preference persistence; overlays and RSI/MACD/ATR panes are strictly clipped to the replay cursor so future values never appear. |
| Trading narrative | Combine a selected period's trades, timeline, and candle-market phases into a continuous, copyable account of the trading process. |
| TMF export | Generate a local `.tmf` archive for AI-assisted review, including trades, contexts, events, narrative, timeline, statistics, and validation. Supports charts, replay snapshots, source redaction, and indicator provider/version provenance. |

### Screenshots

#### Trading Overview

![Trading Overview page](md_img/overview.png)

Summarizes local trading performance, including trade count, net profit, win rate, profit factor, longest losing streak, and completed reviews, while also displaying the net-profit curve and symbol distribution.

#### Trade Records

![Trade Records page](md_img/TradeRecords.png)

Filter, select, or clean up local trades in Trade Records. Open an individual review to inspect a market chart labeled with entry and exit positions, prices, and volume, alongside entry context, execution metrics, and data quality.

#### Trade Replay Player

![Trade Replay Player](md_img/TradeReplay.png)

Select one symbol and a date range, configure the candle timeframe and pre/post-trade market windows, then play candles chronologically or seek directly with the progress bar. Entry and exit markers, trade paths, and realized net profit update with the replay position.

#### Trading Narrative

![Trading Narrative page](md_img/narrative.png)

Combines trades and candle-market phases from the selected time range into a chronological, copyable account of the trading process.

#### TMF Export

![TMF Export page](md_img/trade.png)

Exported TMF files can be uploaded to AI services for trading analysis. You can filter trades by symbol, source, direction, and date, then choose whether to include charts and anonymize order and source identifiers.

### Typical workflow

1. **Prepare MT5 (optional, recommended)**: install and sign in to the MetaTrader 5 terminal on Windows. Start TradeMirror, open **Data Sources**, and check the MT5 connection.
2. **Bring in trade history**: use **Sync MT5 Closed Trades**, selecting a date range or all history. Repeated synchronization is automatically deduplicated. If MT5 is unavailable, import a CSV after reviewing field mappings and sample data.
3. **Inspect and curate trades**: open **Trade Records** and filter by symbol, direction, source, or date; remove individual trades, selected batches, or all trades.
4. **Review an individual trade**: open a trade review, then select **Generate Analysis** or **Reanalyze**. The application retrieves the required historical candles and creates a UTC+0 market replay. Entry and exit arrows are placed on the matching candle or the nearest preceding candle.
5. **Replay a trading period**: open **Trade Replay Player**, select a symbol and date range, and optionally configure the timeframe and pre/post-trade market windows. Inspect the pre-entry market, play or step through candles, or seek with the progress bar; realized net profit updates when exit candles appear.
6. **Generate a period narrative**: in **Trading Narrative**, select a date range containing trade data and apply optional filters. The result combines a trade timeline with market phases and can be copied into an AI tool of your choice.
7. **Export TMF material**: in **TMF Export**, configure filters, chart inclusion, and data-anonymization options. Generate the export and save it locally; the entire export process remains on your device.

### Run and develop

#### Prerequisites

- Windows 10/11
- Python 3.12 or 3.13
- Node.js (the current LTS release is recommended)
- Rust stable toolchain (for the Tauri desktop host)
- MetaTrader 5 for Windows (required only for MT5 synchronization and market replay)

#### Install dependencies

The examples below use Git Bash. Adjust the virtual-environment commands for PowerShell if needed.

```bash
# Engine
cd engine
python -m venv .venv
./.venv/Scripts/pip install -e ".[dev]"

# Frontend
cd ../frontend
npm install
```

#### Start the frontend development server

```bash
cd frontend
npm run dev
```

The default development URL is `http://localhost:1420`.

#### Start the desktop application

```bash
cd desktop/tauri
cargo tauri dev
```

#### Build the Windows portable edition

On a Windows x64 release machine with 64-bit Python 3.12+, Node.js, Rust, Cargo, and the Tauri CLI installed, run:

```bat
scripts\package_portable.bat
```

The build pipeline:

1. `build_engine.bat` creates the release virtual environment, installs `engine[dev,package]`, runs the full pytest suite, and uses PyInstaller to build a one-file windowless `TradeMirrorEngine.exe`.
2. `build_desktop.bat` runs `npm ci` and `npm run build` (TypeScript type checking plus the Vite build), then runs `cargo tauri build --no-bundle -- --locked` to create `TradeMirror.exe`.
3. `package_portable.bat` stages the portable directory, creates `dist\TradeMirror_Portable_v1.0.zip` and `dist\TradeMirror_Portable_v1.0.zip.sha256`, then checks seven required ZIP paths for the desktop application, Engine, configuration, and data/log/resources documentation.

End users only need to extract the ZIP and run `TradeMirror.exe`; Python, Node.js, npm, pip, and a separate database installation are not required. Tauri depends on WebView2, which is normally available on Windows 10/11.

Runtime data is stored outside the extracted application directory:

```text
%APPDATA%\TradeMirror\
├── database\trademirror.db
├── tmf\
├── cache\
├── import-previews\
└── logs\engine\engine.log
```

#### Verify tests, builds, and release artifacts

```bash
# Engine tests
cd engine
./.venv/Scripts/python.exe -m pytest

# Frontend production build and type checking
cd frontend
npm run build
```

Use PowerShell to compare the portable ZIP checksum:

```powershell
Get-FileHash .\dist\TradeMirror_Portable_v1.0.zip -Algorithm SHA256
Get-Content .\dist\TradeMirror_Portable_v1.0.zip.sha256
```

The hashes must match. The packaging script runs Engine pytest, the frontend build, PyInstaller/Tauri builds, required ZIP-path checks, and checksum-file generation; **it does not** start the extracted `TradeMirror.exe` or frozen `TradeMirrorEngine.exe`, call a health endpoint, or run an end-to-end smoke test. Before release, manually extract and launch the application on a clean Windows environment, verify the local Engine and `%APPDATA%\TradeMirror` data/log directories, optionally synchronize MT5, and confirm that no order or position changes occur.

### Data and security notes

- The engine binds only to the local loopback address, `127.0.0.1`.
- A launch token protects communication between the desktop application and the local engine.
- TradeMirror never performs MT5 trading actions or reads/stores MT5 login credentials. When historical candles require it, it may make a valid hidden symbol visible in MT5 Market Watch; this does not change any order, position, or account trading state.
- UI language switching affects only the application's static interface copy. Backend-generated narratives, diagnostics, and imported business data retain their original language and meaning.
- Before sending trade data, narratives, or TMF files to an external AI service, review that service's data-handling policy and your own compliance obligations.
