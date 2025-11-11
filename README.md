# SyntheticQuantEngine

SyntheticQuantEngine is a full-stack data and strategy engine focused on synthetic indices. The goal is to build a self-contained research and execution toolkit that covers data ingestion, strategy research, backtesting, and live experimentation.

## Vision

- Treat synthetic indices as a clean sandbox for rapid strategy iteration.
- Combine trader and developer mindsets to stay end-to-end on ideas.
- Build reusable, testable components that scale beyond early experiments.

## Project Roadmap

1. **Bootstrap** – establish repo hygiene, documentation, and automation.
2. **Data Intake v0.1** – fetch Volatility 25 candles, clean them with Pandas, and persist curated datasets.
3. **Strategy Prototyping** – implement baseline indicators and exploratory notebooks.
4. **Backtesting** – build event-driven simulations first, then optimize with vectorized pipelines.
5. **Live Loop** – wire demo trading flows with strong logging, risk checks, and monitoring hooks.

Each stage prioritizes clarity, testing, and auditability so findings are easy to explain and extend.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create a `.env` file and supply your Deriv demo credentials:

```
DERIV_APP_ID=your_app_id
# Optional if your account requires it
# DERIV_API_TOKEN=your_api_token
```

### Fetch Volatility 25 candles

Run the project CLI to pull the latest batch of candles, compute a 20-period SMA, and store the dataset (defaults to `data/raw/r_25_1h.csv`). Override the symbol or output path as needed:

```bash
python -m synthetic_quant_engine.cli fetch-data --symbol R_25 --count 1000 --granularity 3600
# e.g. fetch 5-minute Volatility 50 candles
python -m synthetic_quant_engine.cli fetch-data --symbol R_50 --granularity 300
```

### Run the SMA crossover backtester (Python shell or notebook)

```python
import pandas as pd
from synthetic_quant_engine.backtest import run_sma_crossover_backtest, SMAParameters

df = pd.read_csv("data/raw/r_25_1h.csv", parse_dates=["timestamp"])
result = run_sma_crossover_backtest(df, SMAParameters(fast_window=20, slow_window=50))
print(f"Total return: {result.total_return:.2%}, max drawdown: {result.max_drawdown:.2%}")
```

## Makefile shortcuts

```bash
make setup        # to create venv and install project in editable mode
make fetch-data   # to run the CLI to refresh Volatility 25 hourly candles
make lint         # for ruff check
make test         # the main pytest
make notebook     # and to launch Jupyter Lab inside the project venv
make mt5-loop     # start the MT5 paper loop (terminal must be running)
```

## MT5 integration (preview)

The legacy `mt5-trading/` folder contains the earlier MT5 bot. We are porting that logic into the main package:

- `synthetic_quant_engine.live.mt5` exposes settings, MT5 session helpers, and a polling loop that reuses the SMA crossover signals.
- Configure credentials in `.env` (demo account shown below):

```
DERIV_MT5_LOGIN=123456789
DERIV_MT5_PASSWORD=your_demo_password
DERIV_MT5_SERVER=Deriv-Demo
DERIV_MT5_SYMBOLS=Volatility 25 Index,Volatility 50 Index
DERIV_MT5_PAPER_MODE=true
```

- Install extras: `pip install -e ".[dev,mt5]"`.
- Launch a paper loop:

```python
from synthetic_quant_engine.live.mt5 import LiveTradingLoop, load_mt5_settings

settings = load_mt5_settings()
loop = LiveTradingLoop(settings)
loop.run()  # polls MT5, generates SMA signals, and simulates fills
```

Or, use the CLI helper (defaults to paper mode):

```bash
python -m synthetic_quant_engine.live.mt5.cli --paper
# When ready (after thorough testing):
# python -m synthetic_quant_engine.live.mt5.cli --live
```

We’ll extend this loop to place real MT5 orders once the paper run and risk controls are validated.

## Repo Directory Layout

- `src/` – package source code.
- `data/` – data artifacts (ignored by default; keep curated exports under version control if needed).
- `docs/` – documentation, journals, and process notes.
- `docs/backtesting.md` – overview of the event-driven backtesting engine.
- `docs/live_mt5.md` – MT5 integration and live-loop notes.
- `notebooks/` – exploratory research notebooks.
- `tests/` – unit and integration tests.
- `scripts/` – automation helpers (setup, linting, data pulls).

## Journaling

I would write all updates, decisions, and what I'm learnings in `docs/journal.md` so future me (or maybe possible collaborators) can replay the rationale behind each change I made.

# Random

Realized some of my installs failed because MetaQuotes hasn’t published a MetaTrader5 wheel for Python 3.13 (and on macOS the package is Windows-only unless I run MT5 through a Windows layer). That's one constraint I have currently, so I will buy a windows pc this afternoon.

