"""High-level polling loop that bridges SMA signals to MT5 execution."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - optional dependency
    import MetaTrader5 as mt5  # type: ignore
except ImportError:  # pragma: no cover
    mt5 = None  # type: ignore
import pandas as pd

from synthetic_quant_engine.live.mt5.executors import PaperExecutor, send_order_real
from synthetic_quant_engine.live.mt5.logger import TradeLogger, TradeRecord
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
    trade_logger: TradeLogger = field(init=False)
    daily_equity_anchor: float | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        risk = self.settings.risk
        account_info = get_account_info()
        starting_equity = account_info.equity if account_info else 10_000.0
        self.equity_start = starting_equity
        self.daily_equity_anchor = starting_equity
        if self.settings.paper_mode:
            self.paper_executor = PaperExecutor(
                starting_equity=starting_equity,
                risk_settings=risk,
            )
        for symbol in self.settings.strategy.symbol_whitelist:
            self.symbol_state[symbol] = SymbolState()
        self.trade_logger = TradeLogger(Path("logs") / "mt5_trades.csv")

    def run(self) -> None:
        if mt5 is None:  # pragma: no cover
            raise RuntimeError(
                "MetaTrader5 package is not installed. Install extras with `pip install -e \".[mt5]\"`."
            )
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
        if self.daily_equity_anchor is None:
            self.daily_equity_anchor = account_info.equity

        for symbol in self.settings.strategy.symbol_whitelist:
            try:
                self._process_symbol(symbol, account_info)
            except Exception as exc:
                LOGGER.exception("Failed processing symbol %s: %s", symbol, exc)
        self._manage_positions(account_info)

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
            self.trade_logger.log_paper_trade(self.paper_executor.trades[-1])
        else:
            result = send_order_real(symbol, side, volume, price=tick.ask)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                LOGGER.error("Order failed %s: %s", symbol, result.comment)
                return
            LOGGER.info("Live order placed: %s %s volume=%s", symbol, side, volume)
            self.trade_logger.log(
                TradeRecord(
                    timestamp=datetime.utcnow().isoformat(),
                    mode="live",
                    symbol=symbol,
                    side=side,
                    volume=volume,
                    price=result.price or tick.ask,
                    pnl=0.0,
                    equity_after=account_info.equity,
                )
            )

    def _risk_checks(self, symbol: str, account_info: mt5.AccountInfo) -> bool:
        risk = self.settings.risk
        if self.daily_equity_anchor is None:
            self.daily_equity_anchor = account_info.equity
        daily_pnl = account_info.equity - self.daily_equity_anchor
        if self.settings.paper_mode and self.paper_executor is not None:
            daily_pnl = self.paper_executor.equity - (self.daily_equity_anchor or self.equity_start or 0)
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

    def _manage_positions(self, account_info: mt5.AccountInfo) -> None:
        risk = self.settings.risk
        if self.settings.paper_mode and self.paper_executor is not None:
            for symbol, position in list(self.paper_executor.open_positions().items()):
                tick = get_symbol_tick(symbol)
                if tick is None:
                    continue
                pnl = position.unrealised_pnl(tick.bid if position.side == "BUY" else tick.ask)
                pip_value = 0.01
                if pnl <= -risk.stop_loss_pips * pip_value * position.volume:
                    LOGGER.info("Paper stop-loss triggered for %s", symbol)
                    self.paper_executor.close_position(symbol, tick.bid if position.side == "BUY" else tick.ask)
                    self.trade_logger.log_paper_trade(self.paper_executor.trades[-1])
                elif pnl >= risk.take_profit_pips * pip_value * position.volume:
                    LOGGER.info("Paper take-profit triggered for %s", symbol)
                    self.paper_executor.close_position(symbol, tick.bid if position.side == "BUY" else tick.ask)
                    self.trade_logger.log_paper_trade(self.paper_executor.trades[-1])
        else:
            positions = get_positions()
            for position in positions:
                symbol = position.symbol
                tick = get_symbol_tick(symbol)
                if tick is None:
                    continue
                price_open = position.price_open
                price_current = position.price_current
                symbol_info = mt5.symbol_info(symbol)
                pip_value = (symbol_info.point * 10) if symbol_info else 0.01
                direction = 1 if position.type == mt5.POSITION_TYPE_BUY else -1
                pip_move = (price_current - price_open) * direction / pip_value
                if pip_move <= -risk.stop_loss_pips:
                    LOGGER.info("Closing %s for stop-loss at %.2f pips", symbol, pip_move)
                    self._close_position(position)
                elif pip_move >= risk.take_profit_pips:
                    LOGGER.info("Closing %s for take-profit at %.2f pips", symbol, pip_move)
                    self._close_position(position)
                elif pip_move >= risk.trailing_start_pips:
                    self._trail_position(position, pip_move, pip_value)

    def _close_position(self, position: mt5.TradePosition) -> None:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": position.ticket,
            "deviation": 20,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            LOGGER.error("Failed to close position %s: %s", position.ticket, result.comment)
        else:
            LOGGER.info("Closed position %s profit=%.2f", position.ticket, result.profit)

    def _trail_position(self, position: mt5.TradePosition, pip_move: float, pip_value: float) -> None:
        lock_pips = max(self.settings.risk.stop_loss_pips / 2, pip_move * 0.5)
        if position.type == mt5.POSITION_TYPE_BUY:
            new_sl = position.price_open + lock_pips * pip_value
            if new_sl > position.sl:
                self._modify_sl(position.ticket, new_sl)
        else:
            new_sl = position.price_open - lock_pips * pip_value
            if position.sl == 0 or new_sl < position.sl:
                self._modify_sl(position.ticket, new_sl)

    def _modify_sl(self, ticket: int, price: float) -> None:
        request = {"action": mt5.TRADE_ACTION_SLTP, "position": ticket, "sl": price}
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            LOGGER.error("Failed to modify SL for position %s: %s", ticket, result.comment)
        else:
            LOGGER.info("Updated stop-loss for %s to %.5f", ticket, price)

