from __future__ import annotations

import hashlib
import json
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.engine import Engine

from app.database.repositories.trade_context_repository import TradeContextRepository
from app.database.repositories.trade_repository import TradeRepository
from app.events.trade_event_generator import TradeEventGenerator
from app.exporter.chart_renderer import render_chart, render_replay_chart
from app.exporter.prompt_builder import build_prompt
from app.exporter.statistics import calculate_statistics
from app.exporter.tmf_validator import validate_tmf
from app.exporter.trader_profile import build_profile
from app.mt5.client import Mt5Client
from app.mt5.market_data_service import MarketDataService
from app.narrative.trading_narrative_service import TradingNarrativeService
from app.schemas.export import TmfExportRequest
from app.schemas.narrative import TradingNarrativeRequest


class TmfExportService:
    def __init__(self, database: Engine, tmf_dir: Path) -> None:
        self._database = database
        self._exports_dir = tmf_dir
        self._exports_dir.mkdir(parents=True, exist_ok=True)

    def create(self, request: TmfExportRequest) -> dict:
        repository = TradeRepository(self._database)
        if request.replay:
            expected_ids = [trade.id for trade in repository.list_for_replay(request.replay.symbol, request.replay.from_time, request.replay.to_time)]
            if request.trade_ids != expected_ids:
                raise ValueError("当前回放交易已变化，请重新加载回放后再导出。")
        trades = repository.get_for_export(
            request.trade_ids, request.symbol, request.direction, request.from_time, request.to_time, request.source
        )
        if not trades:
            raise ValueError("没有找到符合条件的交易。")
        trade_data = [self._trade_data(trade, request.redact_source_identity) for trade in trades]
        contexts = TradeContextRepository(self._database).get_many([trade.id for trade in trades])
        context_data = [self._context_data(trade.id, contexts.get(trade.id)) for trade in trades]
        events = [TradeEventGenerator.generate(trade, contexts.get(trade.id)).model_dump(mode="json") for trade in trades]
        narrative = self._narrative(request, trades)
        statistics = calculate_statistics(trade_data)
        profile = build_profile(statistics)
        export_id = uuid.uuid4().hex
        filename = f"trademirror-{datetime.now(UTC):%Y%m%dT%H%M%SZ}-{export_id[:8]}.tmf"
        path = self._exports_dir / f"{export_id}.tmf"
        options = {"include_charts": request.include_charts, "redact_source_identity": request.redact_source_identity}
        files: dict[str, bytes] = {
            "trades.json": self._json(trade_data),
            "contexts.json": self._json(context_data),
            "trade_events.json": self._json(events),
            "trading_narrative.md": narrative.narrative.encode(),
            "trading_timeline.json": self._json({"timeline": narrative.timeline, "markets": narrative.markets, "diagnostics": narrative.diagnostics}),
            "statistics.json": self._json(statistics),
            "profile.json": self._json(profile),
        }
        if request.replay:
            files["replay.json"] = self._json(self._replay_data(request))
        sources = sorted({trade.source for trade in trades})
        account_ids = sorted({trade.source_account_id for trade in trades if trade.source_account_id})
        provisional_manifest = {
            "format_version": "1.1",
            "indicator_engine": self._indicator_provenance(context_data),
            "created_at": datetime.now(UTC).isoformat(),
            "trade_count": len(trades),
            "source": sources[0] if len(sources) == 1 else None,
            "sources": sources,
            "account": None if request.redact_source_identity else account_ids[0] if len(account_ids) == 1 else account_ids,
            "symbols": sorted({trade.symbol for trade in trades}),
            "export_kind": "trade_replay" if request.replay else "trade_collection",
            "options": options,
        }
        files["prompt.md"] = build_prompt(provisional_manifest, profile, statistics).encode()
        if request.include_charts:
            for trade, context in zip(trade_data, context_data):
                files[f"charts/trade-{trade['id']}.png"] = render_chart(trade, context["context"])
            if request.replay:
                files["replay/replay.png"] = render_replay_chart(request.replay, events)
        manifest = {**provisional_manifest, "files": [{"path": name, "sha256": hashlib.sha256(content).hexdigest()} for name, content in sorted(files.items())]}
        files["manifest.json"] = self._json(manifest)
        files["validation.json"] = self._json({"passed": True, "validated_at": datetime.now(UTC).isoformat()})
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        try:
            validation = validate_tmf(path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return {"export_id": export_id, "filename": filename, "trade_count": len(trades), "include_charts": request.include_charts, "redact_source_identity": request.redact_source_identity, "validation_passed": validation["passed"], "statistics": statistics}

    def path_for(self, export_id: str) -> Path | None:
        path = self._exports_dir / f"{export_id}.tmf"
        return path if path.is_file() else None

    def _narrative(self, request: TmfExportRequest, trades: list) -> object:
        from_time = request.replay.from_time if request.replay else request.from_time or min(trade.open_time for trade in trades)
        to_time = request.replay.to_time if request.replay else request.to_time or max(trade.close_time for trade in trades)
        from_time = from_time.replace(tzinfo=UTC) if from_time.tzinfo is None else from_time.astimezone(UTC)
        to_time = to_time.replace(tzinfo=UTC) if to_time.tzinfo is None else to_time.astimezone(UTC)
        payload = TradingNarrativeRequest(
            symbol=request.symbol,
            direction=request.direction,
            source=request.source,
            from_time=from_time,
            to_time=to_time,
        )
        return TradingNarrativeService(
            self._database,
            MarketDataService(Mt5Client(), self._database),
        ).generate(payload, trades)

    @staticmethod
    def _indicator_provenance(contexts: list[dict]) -> dict | None:
        for item in contexts:
            market_context = (item.get("context") or {}).get("market_context") or {}
            provenance = market_context.get("indicator_provenance")
            if provenance:
                return provenance
        return None

    @staticmethod
    def _replay_data(request: TmfExportRequest) -> dict:
        replay = request.replay
        assert replay is not None
        return {
            "schema_version": "1.0",
            "selection_semantics": "trade_lifecycle_overlaps_selected_range",
            "symbol": replay.symbol,
            "timeframe": replay.timeframe,
            "from": replay.from_time,
            "to": replay.to_time,
            "candle_from": replay.candle_from,
            "candle_to": replay.candle_to,
            "candles": [candle.model_dump(mode="json") for candle in replay.candles],
            "trade_ids": request.trade_ids,
            "pre_roll_candles": replay.pre_roll_candles,
            "post_roll_candles": replay.post_roll_candles,
            "available_pre_roll_candles": replay.available_pre_roll_candles,
            "initial_cursor": replay.initial_cursor,
            "cursor": replay.cursor,
            "current_candle_time": replay.candles[replay.cursor].time,
            "visible_candle_count": replay.cursor + 1,
        }

    @staticmethod
    def _json(value) -> bytes:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8")

    @staticmethod
    def _trade_data(trade, redact: bool) -> dict:
        result = {
            "id": trade.id, "ticket": trade.ticket, "import_batch_id": trade.import_batch_id,
            "source": trade.source, "source_trade_id": trade.source_trade_id, "source_position_id": trade.source_position_id,
            "symbol": trade.symbol, "direction": trade.direction, "open_time": trade.open_time,
            "close_time": trade.close_time, "open_price": trade.open_price, "close_price": trade.close_price,
            "volume": trade.volume, "profit": trade.profit, "commission": trade.commission, "swap": trade.swap,
            "net_profit": trade.net_profit, "stop_loss": trade.stop_loss, "take_profit": trade.take_profit,
            "close_reason": trade.close_reason, "holding_duration_seconds": int((trade.close_time - trade.open_time).total_seconds()),
        }
        if redact:
            result.pop("ticket")
            result.pop("import_batch_id")
            result.pop("source_trade_id")
            result.pop("source_position_id")
        return result

    @staticmethod
    def _context_data(trade_id: int, record) -> dict:
        if not record:
            return {"trade_id": trade_id, "status": "not_analyzed", "context": None}
        return {"trade_id": trade_id, "status": record.status, "timeframe": record.timeframe, "analyzed_at": record.analyzed_at, "error_message": record.error_message, "context": record.context}
