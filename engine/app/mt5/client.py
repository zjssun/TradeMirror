from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class Mt5ClientError(RuntimeError):
    def __init__(self, code: str, message: str, remediation: str) -> None:
        super().__init__(message)
        self.code = code
        self.remediation = remediation


class Mt5Client:
    def __init__(self, module: Any | None = None) -> None:
        self._module = module

    @property
    def module(self) -> Any:
        if self._module is None:
            try:
                import MetaTrader5 as module
            except ImportError as error:
                raise Mt5ClientError(
                    "mt5_package_missing",
                    "未安装 MetaTrader5 Python API。",
                    "请重新安装 TradeMirror 分析引擎组件。",
                ) from error
            self._module = module
        return self._module

    def initialize(self) -> None:
        if not self.module.initialize():
            code, message = self.module.last_error()
            raise Mt5ClientError(
                "mt5_initialize_failed",
                f"无法连接 MetaTrader 5（{code}: {message}）。",
                "请启动并登录 MetaTrader 5，然后在 TradeMirror 中点击“重新连接”。",
            )

    def terminal_info(self) -> Any:
        return self.module.terminal_info()

    def account_info(self) -> Any:
        return self.module.account_info()

    def symbols(self) -> list[Any]:
        return list(self.module.symbols_get() or [])

    def ensure_symbol_selected(self, symbol: str) -> None:
        info = self.module.symbol_info(symbol)
        if info is None:
            raise Mt5ClientError(
                "symbol_not_found",
                f"MT5 中没有找到交易品种 {symbol}。",
                "请从 TradeMirror 显示的品种列表中选择交易品种。",
            )
        if not info.visible and not self.module.symbol_select(symbol, True):
            code, message = self.module.last_error()
            raise Mt5ClientError(
                "symbol_select_failed",
                f"无法启用交易品种 {symbol}（{code}: {message}）。",
                "请在 MT5 市场报价窗口手动显示该交易品种后重试。",
            )

    def rates_range(self, symbol: str, timeframe: Any, from_time: datetime, to_time: datetime) -> list[Any]:
        rates = self.module.copy_rates_range(symbol, timeframe, from_time, to_time)
        if rates is None:
            code, message = self.module.last_error()
            raise Mt5ClientError(
                "candle_fetch_failed",
                f"无法读取 {symbol} 的历史K线（{code}: {message}）。",
                "请确认 MT5 已连接、该品种可见且所选时间范围存在历史数据。",
            )
        return list(rates)

    def history_orders(self, from_time: datetime, to_time: datetime) -> list[Any]:
        orders = self.module.history_orders_get(from_time, to_time)
        if orders is None:
            code, message = self.module.last_error()
            raise Mt5ClientError(
                "history_orders_fetch_failed",
                f"无法读取 MT5 历史订单（{code}: {message}）。",
                "请确认 MT5 已连接且账户允许读取历史订单。",
            )
        return list(orders)

    def history_deals(self, from_time: datetime, to_time: datetime) -> list[Any]:
        deals = self.module.history_deals_get(from_time, to_time)
        if deals is None:
            code, message = self.module.last_error()
            raise Mt5ClientError(
                "history_deals_fetch_failed",
                f"无法读取 MT5 历史成交（{code}: {message}）。",
                "请确认 MT5 已连接且账户允许读取历史成交。",
            )
        return list(deals)

    def rates_from_pos(self, symbol: str, timeframe: Any, start_pos: int, count: int) -> list[Any]:
        rates = self.module.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        if rates is None:
            code, message = self.module.last_error()
            raise Mt5ClientError(
                "candle_fetch_failed",
                f"无法读取 {symbol} 的历史K线（{code}: {message}）。",
                "请确认 MT5 已连接、该品种可见且存在历史数据。",
            )
        return list(rates)

    def timeframe_value(self, timeframe: str) -> Any:
        try:
            return getattr(self.module, f"TIMEFRAME_{timeframe}")
        except AttributeError as error:
            raise Mt5ClientError(
                "timeframe_unsupported",
                f"MT5 不支持周期 {timeframe}。",
                "请选择 TradeMirror 提供的周期。",
            ) from error

    @staticmethod
    def utc_datetime(timestamp: int | float) -> datetime:
        return datetime.fromtimestamp(timestamp, tz=UTC)
