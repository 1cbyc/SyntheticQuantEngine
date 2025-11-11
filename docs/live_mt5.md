# MT5 Live Loop (Preview)

The original `mt5-trading/` folder contains a sprawling MT5 automation stack (multi-strategy bot, dashboards, risk controls). We’re carving out the reusable core and integrating it into `synthetic_quant_engine` so research, backtests, and live execution share the same code path.

## Components

- `synthetic_quant_engine.live.mt5.settings`: Pydantic models that read MT5 credentials, strategy, and risk settings from environment variables.
- `synthetic_quant_engine.live.mt5.session`: Context manager for MT5 terminal lifecycle (initialize, login, shutdown).
- `synthetic_quant_engine.live.mt5.signals`: Reuses the SMA crossover logic from the backtester to generate live signals.
- `synthetic_quant_engine.live.mt5.executors`: Paper-trade simulator plus helper to send real MT5 orders.
- `synthetic_quant_engine.live.mt5.runner`: Polling loop that fetches candles from MT5, computes signals, runs risk checks, and either simulates or places trades.

This “preview” version runs in paper mode by default; adding live execution later is a matter of switching the mode once risk controls are validated.

## Environment Variables

```
DERIV_MT5_LOGIN=123456789
DERIV_MT5_PASSWORD=your_demo_password
DERIV_MT5_SERVER=Deriv-Demo
# Optional comma-separated list of symbols; defaults to Volatility 25 Index
DERIV_MT5_SYMBOLS=Volatility 25 Index,Volatility 50 Index
# Optional path to terminal64.exe (only needed when MT5 terminal is not already running)
# DERIV_MT5_TERMINAL_PATH=/Applications/DerivMT5.app/drive_c/Program\ Files/MetaTrader\ 5/terminal64.exe
# Set to false to send real orders (once you are ready)
DERIV_MT5_PAPER_MODE=true
```

## Install Dependencies

```
pip install -e ".[dev,mt5]"
```

## Quickstart (Paper Trading)

```python
from synthetic_quant_engine.live.mt5 import LiveTradingLoop, load_mt5_settings

settings = load_mt5_settings()
loop = LiveTradingLoop(settings=settings)
loop.run()  # loops forever; Ctrl+C to exit
```

The loop:

1. Connects to MT5 (the desktop terminal must be running and logged into the same account).
2. Polls MT5 candles for each configured symbol.
3. Computes SMA crossover signals.
4. Runs basic risk checks (daily loss/profit, max positions, consecutive losses).
5. Simulates fills (paper mode) or routes orders to MT5 (live mode).

## Roadmap

- Port additional risk controls from the legacy bot (advanced trailing stops, correlation checks).
- Stream logs/metrics to disk or dashboards for easier monitoring.
- Add orchestration scripts (`python -m synthetic_quant_engine.live.mt5.loop`).
- Integrate advanced strategies (RSI, breakout, etc.) once they’ve been vetted by the backtester.
- Only after exhaustively testing paper mode, toggle to live trading by setting `DERIV_MT5_PAPER_MODE=false`.

