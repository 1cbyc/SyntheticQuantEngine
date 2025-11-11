"""Order execution adapters (paper vs real)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

import MetaTrader5 as mt5
import pandas as pd

from synthetic_quant_engine.live.mt5.settings import MT5RiskSettings


@dataclass(slots=True)
class PaperExecutionLog:
    """In-memory log of simulated orders."""

    timestamp: datetime
    symbol: str
    side: str
    volume: float
    fill_price: float
    equity_after: float


@dataclass(slots=True)
class PaperExecutor:
    """Simple paper trade engine tracking cash + positions."""

    starting_equity: float
    risk_settings: MT5RiskSettings
    equity: float = field(init=False)
    positions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    trades: list[PaperExecutionLog] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.equity = self.starting_equity

    def execute(
        self,
        symbol: str,
        side: str,
        volume: float,
        price: float,
    ) -> None:
        """Simulate a fill and update equity/positions."""
        if side not in {"BUY", "SELL"}:
            raise ValueError("Side must be BUY or SELL")

        position = self.positions.setdefault(symbol, {"volume": 0.0, "avg_price": 0.0})
        signed_volume = volume if side == "BUY" else -volume

        new_volume = position["volume"] + signed_volume
        if new_volume == 0:
            realised = (price - position["avg_price"]) * position["volume"]
            self.equity += realised
            position["volume"] = 0.0
            position["avg_price"] = 0.0
        else:
            avg_price = (
                (position["avg_price"] * position["volume"]) + price * signed_volume
            ) / new_volume
            position["volume"] = new_volume
            position["avg_price"] = avg_price

        self.trades.append(
            PaperExecutionLog(
                timestamp=datetime.utcnow(),
                symbol=symbol,
                side=side,
                volume=volume,
                fill_price=price,
                equity_after=self.equity,
            )
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([trade.__dict__ for trade in self.trades])


def send_order_real(
    symbol: str,
    side: str,
    volume: float,
    price: Optional[float] = None,
    deviation: int = 20,
    comment: str = "synthetic-quant-engine",
) -> mt5.TradeResult:
    """Send a real market order via MT5."""
    if side not in {"BUY", "SELL"}:
        raise ValueError("Side must be BUY or SELL")

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL,
        "deviation": deviation,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    if price is not None:
        request["price"] = price

    result = mt5.order_send(request)
    return result

