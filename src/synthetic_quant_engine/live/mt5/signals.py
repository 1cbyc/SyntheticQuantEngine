"""Bridge live MT5 data into SMA-based signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from synthetic_quant_engine.backtest.event import SMAParameters, generate_sma_signal


@dataclass(slots=True)
class LiveSignalResult:
    signal: str
    confidence: float


def compute_sma_signal(
    dataframe: pd.DataFrame,
    fast_window: int,
    slow_window: int,
    price_column: str = "close",
) -> LiveSignalResult:
    """Return BUY/SELL/HOLD plus confidence based on SMA crossovers."""
    params = SMAParameters(fast_window=fast_window, slow_window=slow_window)
    signal_series = generate_sma_signal(dataframe, params, price_column=price_column)
    signal_value = signal_series.iloc[-1]
    prev_value = signal_series.iloc[-2] if len(signal_series) > 1 else signal_value

    if signal_value > prev_value:
        signal = "BUY"
    elif signal_value < prev_value:
        signal = "SELL"
    else:
        signal = "HOLD"

    fast = dataframe[price_column].rolling(window=fast_window).mean()
    slow = dataframe[price_column].rolling(window=slow_window).mean()
    spread = fast.iloc[-1] - slow.iloc[-1]
    confidence = float(abs(spread) / dataframe[price_column].iloc[-1])

    return LiveSignalResult(signal=signal, confidence=confidence)

