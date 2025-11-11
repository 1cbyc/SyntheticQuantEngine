# Event-Driven Backtester (v0.1)

## Purpose

- Provide a minimal, auditable engine to simulate long/flat strategies on synthetic index candles.
- Serve as the backbone for future vectorised and portfolio-level extensions.

## Components

- `EventDrivenBacktester`: Encapsulates the run loop, equity tracking, drawdown calculation, and trade statistics.
- `generate_sma_signal`: Produces binary long/flat signals using configurable fast/slow SMAs.
- `run_sma_crossover_backtest`: Convenience helper that wires the backtester with SMA parameters and returns a `BacktestResult`.
- `BacktestResult`: Stores headline metrics (`total_return`, `max_drawdown`, `win_rate`, `equity_curve`, etc.) for downstream analysis or reporting.

## Usage

```python
import pandas as pd
from synthetic_quant_engine.backtest import run_sma_crossover_backtest, SMAParameters

df = pd.read_csv("data/raw/r_25_1h.csv", parse_dates=["timestamp"])
params = SMAParameters(fast_window=20, slow_window=50)
result = run_sma_crossover_backtest(df, params)

print(f"Total return: {result.total_return:.2%}")
print(f"Max drawdown: {result.max_drawdown:.2%}")
result.equity_curve.plot(title="Equity Curve")
```

## Testing

- Unit tests live in `tests/test_backtester.py`.
- Coverage includes SMA configuration validation, signal generation, aggregate metrics, and failure modes.

## Next Steps

- Introduce transaction costs and slippage.
- Support short positioning and position sizing beyond binary exposure.
- Integrate with vectorised backtesting pipeline for faster parameter sweeps.

