from __future__ import annotations

from app.schemas.events import TradeEvent


class TradeEventGenerator:
    @staticmethod
    def generate(trade, context_record=None) -> TradeEvent:
        return TradeEvent(
            trade_id=trade.id,
            source=trade.source,
            ticket=trade.ticket,
            symbol=trade.symbol,
            direction=trade.direction,
            open_time=trade.open_time,
            close_time=trade.close_time,
            open_price=trade.open_price,
            close_price=trade.close_price,
            volume=trade.volume,
            result={
                "profit": trade.profit,
                "commission": trade.commission,
                "swap": trade.swap,
                "net_profit": trade.net_profit,
            },
            context_status=context_record.status if context_record else "not_analyzed",
            context=context_record.context if context_record else None,
        )
