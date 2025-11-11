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
```

## Repo Directory Layout

- `src/` – package source code.
- `data/` – data artifacts (ignored by default; keep curated exports under version control if needed).
- `docs/` – documentation, journals, and process notes.
- `docs/backtesting.md` – overview of the event-driven backtesting engine.
- `notebooks/` – exploratory research notebooks.
- `tests/` – unit and integration tests.
- `scripts/` – automation helpers (setup, linting, data pulls).
- `auto.sh` – helper script to commit file changes one file at a time.

## Journaling

I would write all updates, decisions, and what I'm learnings in `docs/journal.md` so future me (or maybe possible collaborators) can replay the rationale behind each change I made.


