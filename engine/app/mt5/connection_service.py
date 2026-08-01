from __future__ import annotations

from datetime import UTC, datetime

from app.mt5.client import Mt5Client, Mt5ClientError
from app.schemas.mt5 import (
    AccountSummary,
    Mt5ConnectionState,
    Mt5Diagnostic,
    Mt5StatusResponse,
    TerminalSummary,
)


class Mt5ConnectionService:
    def __init__(self, client: Mt5Client) -> None:
        self._client = client

    def connect(self) -> Mt5StatusResponse:
        try:
            self._client.initialize()
            terminal = self._client.terminal_info()
            account = self._client.account_info()
            if terminal is None or account is None:
                return self._disconnected()
            return Mt5StatusResponse(
                state=Mt5ConnectionState.CONNECTED,
                terminal=TerminalSummary(
                    path=getattr(terminal, "path", None),
                    version=str(getattr(terminal, "build", "未知")),
                    connected=bool(getattr(terminal, "connected", False)),
                ),
                account=AccountSummary(
                    login=int(account.login),
                    server=str(account.server),
                    company=getattr(account, "company", None),
                    currency=str(account.currency),
                    balance=float(account.balance),
                    equity=float(account.equity),
                ),
            )
        except Mt5ClientError as error:
            return Mt5StatusResponse(
                state=Mt5ConnectionState.UNAVAILABLE,
                diagnostic=Mt5Diagnostic(
                    code=error.code,
                    message=str(error),
                    remediation=error.remediation,
                ),
            )

    def status(self) -> Mt5StatusResponse:
        return self.connect()

    @staticmethod
    def _disconnected() -> Mt5StatusResponse:
        return Mt5StatusResponse(
            state=Mt5ConnectionState.DISCONNECTED,
            diagnostic=Mt5Diagnostic(
                code="mt5_not_logged_in",
                message="MetaTrader 5 已启动，但尚未连接有效交易账户。",
                remediation="请在 MetaTrader 5 中登录交易账户并确认终端连接正常后重新连接。",
            ),
        )
