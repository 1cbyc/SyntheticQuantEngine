"""Order execution adapters (paper vs real)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional

# instead of importing metatrader as mt5 doing this:
try:  # pragma: no cover - optional dependency
    import MetaTrader5 as mt5  # type: ignore
except ImportError:  # pragma: no cover
    mt5 = None  # type: ignore
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
    pnl: float
    equity_after: float


@dataclass(slots=True)
class PaperPosition:
    symbol: str
    side: str  # BUY or SELL
    volume: float
    entry_price: float
    open_time: datetime

    def market_value(self, price: float) -> float:
        signed = self.volume if self.side == "BUY" else -self.volume
        return signed * price

    def unrealised_pnl(self, price: float) -> float:
        direction = 1 if self.side == "BUY" else -1
        return (price - self.entry_price) * direction * self.volume


@dataclass(slots=True)
class PaperExecutor:
    """Simple paper trade engine tracking cash + positions."""

    starting_equity: float
    risk_settings: MT5RiskSettings
    equity: float = field(init=False)
    positions: Dict[str, PaperPosition] = field(default_factory=dict)
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

        existing = self.positions.get(symbol)
        pnl = 0.0

        if existing is None:
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                side=side,
                volume=volume,
                entry_price=price,
                open_time=datetime.utcnow(),
            )
        else:
            if existing.side == side:
                # scale in
                total_volume = existing.volume + volume
                weighted_price = (
                    existing.entry_price * existing.volume + price * volume
                ) / total_volume
                existing.volume = total_volume
                existing.entry_price = weighted_price
            else:
                # closing/flip
                closing_volume = min(existing.volume, volume)
                direction = 1 if existing.side == "BUY" else -1
                pnl = (price - existing.entry_price) * direction * closing_volume
                self.equity += pnl
                remaining = existing.volume - closing_volume
                if remaining <= 1e-9:
                    del self.positions[symbol]
                    if volume > closing_volume:
                        # open new position opposite side with leftover volume
                        leftover = volume - closing_volume
                        self.positions[symbol] = PaperPosition(
                            symbol=symbol,
                            side=side,
                            volume=leftover,
                            entry_price=price,
                            open_time=datetime.utcnow(),
                        )
                else:
                    existing.volume = remaining
                    if volume > closing_volume:
                        weighted_price = (
                            price * (volume - closing_volume) + existing.entry_price * remaining
                        ) / (remaining + volume - closing_volume)
                        existing.side = side
                        existing.volume = remaining + (volume - closing_volume)
                        existing.entry_price = weighted_price
                        existing.open_time = datetime.utcnow()

        self.trades.append(
            PaperExecutionLog(
                timestamp=datetime.utcnow(),
                symbol=symbol,
                side=side,
                volume=volume,
                fill_price=price,
                pnl=pnl,
                equity_after=self.equity,
            )
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([trade.__dict__ for trade in self.trades])

    def open_positions(self) -> Dict[str, PaperPosition]:
        return self.positions

    def close_position(self, symbol: str, price: float) -> float:
        position = self.positions.get(symbol)
        if position is None:
            return 0.0
        pnl = position.unrealised_pnl(price)
        self.equity += pnl
        del self.positions[symbol]
        self.trades.append(
            PaperExecutionLog(
                timestamp=datetime.utcnow(),
                symbol=symbol,
                side="CLOSE",
                volume=position.volume,
                fill_price=price,
                pnl=pnl,
                equity_after=self.equity,
            )
        )
        return pnl


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

