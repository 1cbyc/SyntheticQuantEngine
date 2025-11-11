from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from synthetic_quant_engine.backtest.event import (
    EventDrivenBacktester,
    SMAParameters,
    generate_sma_signal,
    run_sma_crossover_backtest,
)


def make_price_series(length: int = 100, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = rng.normal(loc=0.0005, scale=0.01, size=length)
    prices = 100 * (1 + returns).cumprod()
    return pd.DataFrame({"close": prices})


def test_backtester_requires_price_column() -> None:
    df = pd.DataFrame({"foo": [1, 2, 3]})
    with pytest.raises(KeyError):
        EventDrivenBacktester(df)


def test_backtester_runs_and_produces_metrics() -> None:
    df = make_price_series(200)
    result = run_sma_crossover_backtest(df, SMAParameters(fast_window=5, slow_window=20))

    assert isinstance(result.total_return, float)
    assert result.equity_curve.iloc[0] == pytest.approx(10_000.0)
    assert len(result.cumulative_returns) == len(df)
    assert result.max_drawdown <= 0


def test_generate_sma_signal_shapes_align() -> None:
    df = make_price_series(60)
    params = SMAParameters(fast_window=3, slow_window=10)
    signal = generate_sma_signal(df, params)

    assert signal.shape[0] == df.shape[0]
    assert signal.dtype == float
    assert signal.isin({0.0, 1.0}).all()


def test_invalid_sma_configuration() -> None:
    with pytest.raises(ValueError):
        SMAParameters(fast_window=10, slow_window=5).validate()

    with pytest.raises(ValueError):
        SMAParameters(fast_window=0, slow_window=5).validate()


def test_backtester_signal_validation() -> None:
    df = make_price_series(50)
    backtester = EventDrivenBacktester(df)

    def bad_signal(_: pd.DataFrame) -> pd.Series:
        return pd.Series([2] * len(df))

    with pytest.raises(ValueError):
        backtester.run(bad_signal)

