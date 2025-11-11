"""Helpers for managing MT5 sessions via MetaTrader5 package."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator, Optional

import MetaTrader5 as mt5

from synthetic_quant_engine.live.mt5.settings import MT5AccountSettings


@dataclass(slots=True)
class MT5Session:
    """Context manager style MT5 session."""

    account: MT5AccountSettings

    def __enter__(self) -> "MT5Session":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    def connect(self) -> None:
        """Initialise terminal and login."""
        terminal_path = (
            str(self.account.terminal_path)
            if self.account.terminal_path is not None
            else None
        )

        if terminal_path:
            if not mt5.initialize(path=terminal_path):
                raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
        else:
            if not mt5.initialize():
                raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

        password = self.account.password.get_secret_value()
        if not mt5.login(
            login=self.account.login,
            password=password,
            server=self.account.server,
        ):
            last_error = mt5.last_error()
            mt5.shutdown()
            raise RuntimeError(f"MT5 login failed: {last_error}")

    def disconnect(self) -> None:
        with contextlib.suppress(Exception):
            mt5.shutdown()


def get_account_info() -> Optional[mt5.AccountInfo]:
    """Return account info if connected."""
    try:
        return mt5.account_info()
    except Exception:
        return None


def get_symbol_tick(symbol: str) -> Optional[mt5.Tick]:
    """Fetch latest tick for symbol."""
    try:
        return mt5.symbol_info_tick(symbol)
    except Exception:
        return None


def get_positions() -> list[mt5.TradePosition]:
    """Get open positions (empty list if none)."""
    positions = mt5.positions_get()
    return list(positions) if positions else []


def get_rates(
    symbol: str,
    timeframe: int,
    count: int,
) -> Optional[list]:
    """Retrieve historical rates using the MT5 API."""
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        return list(rates) if rates else None
    except Exception:
        return None

