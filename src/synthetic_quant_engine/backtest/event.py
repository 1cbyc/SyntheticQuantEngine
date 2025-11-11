"""Simple event-driven backtesting utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd


@dataclass(slots=True)
class BacktestResult:
    """Summary of a backtest run."""

    total_return: float
    cumulative_returns: pd.Series
    equity_curve: pd.Series
    trades: int
    win_rate: float
    max_drawdown: float
    final_cash: float


@dataclass(slots=True)
class SMAParameters:
    """Parameters for the SMA crossover strategy."""

    fast_window: int = 20
    slow_window: int = 50

    def validate(self) -> None:
        if self.fast_window <= 0 or self.slow_window <= 0:
            raise ValueError("SMA windows must be positive integers.")
        if self.fast_window >= self.slow_window:
            raise ValueError("Fast SMA window must be less than slow SMA window.")


class EventDrivenBacktester:
    """Single-asset event-driven backtester with a long/flat posture."""

    def __init__(
        self,
        data: pd.DataFrame,
        price_column: str = "close",
        initial_cash: float = 10_000.0,
        position_size: float = 1.0,
    ) -> None:
        if price_column not in data.columns:
            raise KeyError(f"Price column '{price_column}' not found in dataframe.")

        self.data = data.copy()
        self.price_column = price_column
        self.initial_cash = initial_cash
        self.position_size = position_size
        self._validate_input()

    def _validate_input(self) -> None:
        if self.data.empty:
            raise ValueError("Input data is empty.")
        if not self.data[self.price_column].dtype.kind in {"f", "i"}:
            raise TypeError("Price column must be numeric.")

    def run(self, signal_fn: Callable[[pd.DataFrame], pd.Series]) -> BacktestResult:
        """Run the backtest using the provided signal function.

        The signal function must return a Series with values in {1, 0, -1}, representing
        long, flat, or short positions respectively. For now we only support long/flat,
        but the interface leaves room for future extension.
        """
        signals = signal_fn(self.data).reindex(self.data.index).fillna(0.0)
        if signals.abs().max() > 1:
            raise ValueError("Signals must be in the range [-1, 1].")

        prices = self.data[self.price_column]
        returns = prices.pct_change().fillna(0.0)

        position = signals.shift(1).fillna(0.0)
        strategy_returns = position * returns * self.position_size
        equity_curve = (1 + strategy_returns).cumprod() * self.initial_cash

        trades = (signals.diff().abs() > 0).sum()
        wins = ((strategy_returns > 0) & (position.shift(1) != 0)).sum()
        total_trades = ((position != 0) & (position.shift(1) == 0)).sum()
        win_rate = wins / total_trades if total_trades else 0.0

        drawdown = equity_curve / equity_curve.cummax() - 1.0
        result = BacktestResult(
            total_return=equity_curve.iloc[-1] / self.initial_cash - 1,
            cumulative_returns=strategy_returns.cumsum(),
            equity_curve=equity_curve,
            trades=int(trades),
            win_rate=win_rate,
            max_drawdown=drawdown.min(),
            final_cash=float(equity_curve.iloc[-1]),
        )
        return result


def generate_sma_signal(
    data: pd.DataFrame, params: SMAParameters, price_column: str = "close"
) -> pd.Series:
    params.validate()
    fast = data[price_column].rolling(window=params.fast_window).mean()
    slow = data[price_column].rolling(window=params.slow_window).mean()
    signal = (fast > slow).astype(float)
    return signal


def run_sma_crossover_backtest(
    data: pd.DataFrame,
    params: SMAParameters | None = None,
    initial_cash: float = 10_000.0,
    position_size: float = 1.0,
    price_column: str = "close",
) -> BacktestResult:
    params = params or SMAParameters()
    backtester = EventDrivenBacktester(
        data=data,
        price_column=price_column,
        initial_cash=initial_cash,
        position_size=position_size,
    )
    return backtester.run(lambda df: generate_sma_signal(df, params, price_column=price_column))

