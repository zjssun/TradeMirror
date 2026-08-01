from __future__ import annotations

from datetime import UTC, datetime

from app.mt5.client import Mt5Client
from app.schemas.mt5 import SymbolListResponse, SymbolResponse


class SymbolService:
    def __init__(self, client: Mt5Client) -> None:
        self._client = client

    def list_symbols(self, query: str | None, visible_only: bool, limit: int) -> SymbolListResponse:
        self._client.initialize()
        normalized_query = (query or "").strip().casefold()
        symbols = []
        for symbol in self._client.symbols():
            if visible_only and not symbol.visible:
                continue
            searchable = f"{symbol.name} {symbol.description} {symbol.path}".casefold()
            if normalized_query and normalized_query not in searchable:
                continue
            symbols.append(
                SymbolResponse(
                    name=symbol.name,
                    description=symbol.description or symbol.name,
                    path=symbol.path or "",
                    digits=int(symbol.digits),
                    point=float(symbol.point),
                    visible=bool(symbol.visible),
                )
            )
        symbols.sort(key=lambda item: (not item.visible, item.name))
        return SymbolListResponse(
            items=symbols[:limit], total=len(symbols), fetched_at=datetime.now(UTC)
        )
