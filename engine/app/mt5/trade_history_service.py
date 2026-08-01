from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from app.database.repositories.trade_repository import TradeRepository
from app.mt5.client import Mt5Client
from app.schemas.datasource import Mt5HistorySyncRequest, Mt5HistorySyncResponse


class TradeHistoryService:
    def __init__(self, client: Mt5Client, database) -> None:
        self._client = client
        self._repository = TradeRepository(database)

    def sync(self, request: Mt5HistorySyncRequest) -> Mt5HistorySyncResponse:
        from_time, to_time = self._range(request)
        self._client.initialize()
        account_id = str(self._client.account_info().login)
        orders = self._client.history_orders(from_time, to_time)
        deals = self._client.history_deals(from_time, to_time)
        normalized = self._normalize_deals(deals, orders, account_id, request.symbol)
        imported, updated = self._repository.upsert_source_trades("MT5", normalized)
        self._repository.record_sync("MT5", account_id, request.symbol, from_time, to_time, "completed", len(normalized))
        return Mt5HistorySyncResponse(
            account_id=account_id,
            imported_count=imported,
            updated_count=updated,
            skipped_count=len(deals) - len(normalized),
            from_time=from_time,
            to_time=to_time,
        )

    def record_failure(self, request: Mt5HistorySyncRequest, diagnostic: str) -> None:
        from_time, to_time = self._range(request)
        self._repository.record_sync(
            "MT5", None, request.symbol, from_time, to_time, "failed", 0, diagnostic
        )

    @staticmethod
    def _range(request: Mt5HistorySyncRequest) -> tuple[datetime, datetime]:
        if request.sync_all:
            return datetime(1970, 1, 1, tzinfo=UTC), datetime.now(UTC)
        return request.from_time.astimezone(UTC), request.to_time.astimezone(UTC)

    def _normalize_deals(self, deals: list[Any], orders: list[Any], account_id: str, symbol: str | None) -> list[dict[str, Any]]:
        entry_in = getattr(self._client.module, "DEAL_ENTRY_IN", 0)
        entry_out = getattr(self._client.module, "DEAL_ENTRY_OUT", 1)
        entry_out_by = getattr(self._client.module, "DEAL_ENTRY_OUT_BY", 3)
        buy = getattr(self._client.module, "DEAL_TYPE_BUY", 0)
        openings: dict[str, list[dict[str, Any]]] = {}
        for deal in sorted(deals, key=self._time):
            if self._value(deal, "entry") == entry_in:
                openings.setdefault(str(self._value(deal, "position_id", "0")), []).append(
                    {"deal": deal, "remaining": float(self._value(deal, "volume", 0))}
                )
        orders_by_ticket = {str(self._value(order, "ticket")): order for order in orders}
        trades = []
        for deal in sorted(deals, key=self._time):
            if self._value(deal, "entry") not in {entry_out, entry_out_by}:
                continue
            deal_symbol = str(self._value(deal, "symbol", ""))
            if not deal_symbol or (symbol and deal_symbol != symbol):
                continue
            volume = float(self._value(deal, "volume", 0))
            deal_ticket = str(self._value(deal, "ticket"))
            if volume <= 0 or not deal_ticket:
                continue
            position_id = str(self._value(deal, "position_id", "0"))
            allocations = self._allocate(openings.get(position_id, []), volume, self._time(deal))
            if not allocations:
                continue
            allocated_volume = sum(item[1] for item in allocations)
            opening = allocations[0][0]["deal"]
            open_price = sum(float(self._value(item[0]["deal"], "price", 0)) * item[1] for item in allocations) / allocated_volume
            open_commission = sum(float(self._value(item[0]["deal"], "commission", 0)) * item[1] / float(self._value(item[0]["deal"], "volume", 1)) for item in allocations)
            open_swap = sum(float(self._value(item[0]["deal"], "swap", 0)) * item[1] / float(self._value(item[0]["deal"], "volume", 1)) for item in allocations)
            profit = float(self._value(deal, "profit", 0))
            commission = open_commission + float(self._value(deal, "commission", 0))
            swap = open_swap + float(self._value(deal, "swap", 0))
            order = orders_by_ticket.get(str(self._value(deal, "order")))
            direction = "BUY" if self._value(opening, "type") == buy else "SELL"
            fingerprint = hashlib.sha256(f"MT5|{account_id}|{deal_ticket}".encode()).hexdigest()
            trades.append(
                {
                    "ticket": deal_ticket,
                    "symbol": deal_symbol,
                    "direction": direction,
                    "open_time": self._time(opening),
                    "close_time": self._time(deal),
                    "open_price": open_price,
                    "close_price": float(self._value(deal, "price", 0)),
                    "volume": allocated_volume,
                    "profit": profit,
                    "commission": commission,
                    "swap": swap,
                    "net_profit": profit + commission + swap,
                    "stop_loss": self._float_or_none(order, "sl"),
                    "take_profit": self._float_or_none(order, "tp"),
                    "close_reason": str(self._value(order, "reason")) if order and self._value(order, "reason") is not None else "MT5_HISTORY",
                    "source_trade_id": deal_ticket,
                    "source_position_id": position_id,
                    "source_account_id": account_id,
                    "source_metadata": {"order": self._value(deal, "order"), "deal_entry": self._value(deal, "entry"), "allocated_open_deals": [self._value(item[0]["deal"], "ticket") for item in allocations]},
                    "synced_at": datetime.now(UTC),
                    "source_fingerprint": fingerprint,
                }
            )
        return trades

    def _allocate(self, openings: list[dict[str, Any]], close_volume: float, close_time: datetime) -> list[tuple[dict[str, Any], float]]:
        remaining = close_volume
        allocations = []
        for opening in openings:
            if self._time(opening["deal"]) >= close_time or remaining <= 0:
                continue
            used = min(opening["remaining"], remaining)
            if used > 0:
                opening["remaining"] -= used
                remaining -= used
                allocations.append((opening, used))
        return allocations

    @staticmethod
    def _value(record: Any, field: str, default: Any = None) -> Any:
        return getattr(record, field, default) if not isinstance(record, dict) else record.get(field, default)

    def _time(self, deal: Any) -> datetime:
        return self._client.utc_datetime(int(self._value(deal, "time")))

    def _float_or_none(self, record: Any, field: str) -> float | None:
        value = self._value(record, field) if record else None
        return float(value) if value not in {None, 0} else None
