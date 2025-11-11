"""Backtesting utilities for SyntheticQuantEngine."""

from __future__ import annotations

from .event import BacktestResult, EventDrivenBacktester, SMAParameters, run_sma_crossover_backtest

__all__ = [
    "BacktestResult",
    "EventDrivenBacktester",
    "SMAParameters",
    "run_sma_crossover_backtest",
]

