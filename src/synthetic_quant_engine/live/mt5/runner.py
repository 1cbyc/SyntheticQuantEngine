"""High-level polling loop that bridges SMA signals to MT5 execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import MetaTrader5 as mt5
import pandas as pd

from synthetic_quant_engine.live.mt5.executors import PaperExecutor, send_order_real
from synthetic_quant_engine.live.mt5.session import (
    MT5Session,
    get_account_info,
    get_positions,
    get_rates,
    get_symbol_tick,
)
from synthetic_quant_engine.live.mt5.settings import MT5RiskSettings, MT5Settings
from synthetic_quant_engine.live.mt5.signals import compute_sma_signal


LOGGER = logging.getLogger(__name__)

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
}


@dataclass(slots=True)
class SymbolState:
    consecutive_losses: int = 0
    last_signal_time: datetime | None = None
    pnl: float = 0.0


class LoopMode(str):
    PAPER = "paper"
    LIVE = "live"


@dataclass
class LiveTradingLoop:
    """Co-ordinate MT5 session, signals, and execution."""

    settings: MT5Settings
    equity_start: float | None = None
    paper_executor: PaperExecutor | None = field(init=False)
    symbol_state: Dict[str, SymbolState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        risk = self.settings.risk
        account_info = get_account_info()
        starting_equity = account_info.equity if account_info else 10_000.0
        self.equity_start = starting_equity
        if self.settings.paper_mode:
            self.paper_executor = PaperExecutor(
                starting_equity=starting_equity,
                risk_settings=risk,
            )
        for symbol in self.settings.strategy.symbol_whitelist:
            self.symbol_state[symbol] = SymbolState()

    def run(self) -> None:
        with MT5Session(self.settings.account):
            LOGGER.info("Connected to MT5 as %s", self.settings.account.login)
            while True:
                start = time.time()
                try:
                    self._process_cycle()
                except Exception as exc:
                    LOGGER.exception("Live loop encountered error: %s", exc)
                elapsed = time.time() - start
                sleep_time = max(
                    1, self.settings.strategy.polling_seconds - int(elapsed)
                )
                time.sleep(sleep_time)

    def _process_cycle(self) -> None:
        account_info = get_account_info()
        if not account_info:
            LOGGER.error("Account info unavailable; skipping cycle.")
            return

        for symbol in self.settings.strategy.symbol_whitelist:
            try:
                self._process_symbol(symbol, account_info)
            except Exception as exc:
                LOGGER.exception("Failed processing symbol %s: %s", symbol, exc)

    def _process_symbol(self, symbol: str, account_info: mt5.AccountInfo) -> None:
        timeframe = TIMEFRAME_MAP.get(
            self.settings.strategy.timeframe, mt5.TIMEFRAME_M5
        )
        rates = get_rates(symbol, timeframe, 500)
        if not rates:
            LOGGER.warning("No rates for %s", symbol)
            return
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)

        signal = compute_sma_signal(
            df,
            fast_window=self.settings.strategy.fast_window,
            slow_window=self.settings.strategy.slow_window,
        )
        LOGGER.info("Signal for %s: %s (confidence %.3f)", symbol, signal.signal, signal.confidence)

        if signal.signal == "HOLD" or signal.confidence < self.settings.strategy.min_confidence:
            return

        if not self._risk_checks(symbol, account_info):
            LOGGER.info("Risk checks blocked new trade on %s", symbol)
            return

        tick = get_symbol_tick(symbol)
        if tick is None:
            LOGGER.warning("No tick data for %s", symbol)
            return

        side = signal.signal
        volume = self._position_size(symbol, account_info.balance, tick.ask)

        if self.settings.paper_mode:
            assert self.paper_executor is not None
            self.paper_executor.execute(
                symbol=symbol,
                side=side,
                volume=volume,
                price=tick.ask,
            )
            LOGGER.info("Paper trade executed: %s %s vol=%.3f price=%s", symbol, side, volume, tick.ask)
        else:
            result = send_order_real(symbol, side, volume, price=tick.ask)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                LOGGER.error("Order failed %s: %s", symbol, result.comment)
                return
            LOGGER.info("Live order placed: %s %s volume=%s", symbol, side, volume)

    def _risk_checks(self, symbol: str, account_info: mt5.AccountInfo) -> bool:
        risk = self.settings.risk
        daily_pnl = account_info.profit
        if daily_pnl <= -risk.max_daily_loss:
            LOGGER.warning("Daily loss limit reached: %.2f <= -%.2f", daily_pnl, risk.max_daily_loss)
            return False
        if daily_pnl >= risk.max_daily_profit:
            LOGGER.info("Daily profit target reached: %.2f >= %.2f", daily_pnl, risk.max_daily_profit)
            return False
        positions = get_positions()
        if len(positions) >= risk.max_positions:
            LOGGER.info("Max open positions reached (%s >= %s)", len(positions), risk.max_positions)
            return False
        state = self.symbol_state[symbol]
        if state.consecutive_losses >= risk.max_consecutive_losses:
            LOGGER.info("Symbol %s paused due to consecutive losses (%s)", symbol, state.consecutive_losses)
            return False
        return True

    def _position_size(self, symbol: str, balance: float, price: float) -> float:
        risk_pct = self.settings.risk.risk_per_trade_percent / 100.0
        risk_amount = balance * risk_pct
        stop_pips = self.settings.risk.stop_loss_pips

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            pip_size = symbol_info.point
            pip_value = pip_size * 10
        else:
            pip_value = 0.01

        volume = risk_amount / (stop_pips * pip_value)
        min_volume = getattr(symbol_info, "volume_min", 0.01) if symbol_info else 0.01
        step = getattr(symbol_info, "volume_step", 0.01) if symbol_info else 0.01
        volume = max(min_volume, round(volume / step) * step)
        return volume

