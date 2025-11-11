"""Simple CSV trade logger for MT5 runs."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

from synthetic_quant_engine.live.mt5.executors import PaperExecutionLog


@dataclass(slots=True)
class TradeRecord:
    timestamp: str
    mode: str
    symbol: str
    side: str
    volume: float
    price: float
    pnl: float
    equity_after: float


class TradeLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_header()

    def _ensure_header(self) -> None:
        if not self.path.exists():
            with self.path.open("w", newline="") as fp:
                writer = csv.writer(fp)
                writer.writerow(
                    [
                        "timestamp",
                        "mode",
                        "symbol",
                        "side",
                        "volume",
                        "price",
                        "pnl",
                        "equity_after",
                    ]
                )

    def log(self, record: TradeRecord) -> None:
        with self.path.open("a", newline="") as fp:
            writer = csv.writer(fp)
            writer.writerow(
                [
                    record.timestamp,
                    record.mode,
                    record.symbol,
                    record.side,
                    record.volume,
                    record.price,
                    record.pnl,
                    record.equity_after,
                ]
            )

    def log_paper_trade(self, log: PaperExecutionLog) -> None:
        record = TradeRecord(
            timestamp=log.timestamp.isoformat(),
            mode="paper",
            symbol=log.symbol,
            side=log.side,
            volume=log.volume,
            price=log.fill_price,
            pnl=log.pnl,
            equity_after=log.equity_after,
        )
        self.log(record)

