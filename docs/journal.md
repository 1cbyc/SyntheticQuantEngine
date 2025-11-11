# Build Journal

## 2025-11-11 – Bootstrap

- Created `.gitignore` to keep secrets, data artifacts, and virtual environments out of version control.
- Drafted `README.md` to capture vision, roadmap, and initial setup notes.
- Established `docs/` directory and this journal for ongoing decision tracking.

## 2025-11-11 – Data intake scaffolding

- Added `pyproject.toml` and minimal package layout under `src/synthetic_quant_engine`.
- Implemented async Volatility 25 fetcher using Deriv WebSocket API with Pydantic validation and SMA enrichment.
- Introduced CLI (`python -m synthetic_quant_engine.cli fetch-data`) plus documentation for the data pipeline.
- Ensured `data/` is tracked via `.gitkeep` while keeping raw exports ignored by default.
- `tail data/raw/vol25_1h.csv` when I got the data

## 2025-11-11 – First live pull

- Created Deriv demo application + token and populated `.env`.
- Reworked WebSocket client to use native protocol (with SSL fix + certifi) and tolerate missing synthetic volumes.
- Successfully fetched 1,000 × 1-hour Volatility 25 candles to `data/raw/vol25_1h.csv`; inspected head/tail stats with pandas.

## 2025-11-11 – Fetch generalisation + tests

- Generalised the fetch pipeline to accept arbitrary symbols/granularities with automatic output naming.
- Added helper slug logic and Pydantic model tests to guard schema changes.
- Extended the CLI interface (`--symbol`, smart defaults) and refreshed docs/README around the broader data workflow.

## 2025-11-11 – Exploratory analytics starter

- Created `notebooks/vol25_exploration.ipynb` to review recent Volatility 25 hourly candles.
- Computed basic stats/returns, rolling volatility, and plotted price vs SMA20 for quick sanity checks.
- Captured next research questions in the notebook to guide upcoming strategy prototypes.

## 2025-11-11 – Event-driven backtester v0.1

- Implemented `EventDrivenBacktester` with SMA crossover helper + result metrics.
- Added pytest coverage for signal generation, configuration validation, and risk stats.
- Documented usage in `docs/backtesting.md` and surfaced quick-start snippet in the README.

## 2025-11-11 – Repo automation helpers

- I added `Makefile` with shortcuts for setup, lint, test, data fetch, and notebooks.
- Updated README to surface common commands for local development.

## 2025-11-11 – MT5 integration scaffold

- Began porting the legacy MT5 bot into the package (`synthetic_quant_engine.live.mt5`).
- Added Pydantic settings, MT5 session helpers, signal bridge, paper/live executors, and polling loop skeleton.
- Documented environment variables and workflow in `docs/live_mt5.md` and noted the preview flow in the README.

## 2025-11-11 – MT5 risk + CLI pass

- Brought across core risk management: daily loss/profit limits, max positions, consecutive-loss pauses, and trailing stop / TP enforcement.
- Added CSV trade logger plus paper executor improvements so fills/PnL are auditable.
- Created `python -m synthetic_quant_engine.live.mt5.cli` and Makefile target `make mt5-loop` for quick paper runs.




