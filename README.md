# SyntheticQuantEngine

SyntheticQuantEngine is a full-stack data and strategy engine focused on synthetic indices. The goal is to build a self-contained research and execution toolkit that covers data ingestion, strategy research, backtesting, and live experimentation.

## Vision

- Treat synthetic indices as a clean sandbox for rapid strategy iteration.
- Combine trader and developer mindsets to stay end-to-end on ideas.
- Build reusable, testable components that scale beyond early experiments.

## Project Roadmap

1. **Bootstrap** – establish repo hygiene, documentation, and automation.
2. **Data Intake v0.1** – fetch Volatility 75 candles, clean them with Pandas, and persist curated datasets.
3. **Strategy Prototyping** – implement baseline indicators and exploratory notebooks.
4. **Backtesting** – build event-driven simulations first, then optimize with vectorized pipelines.
5. **Live Loop** – wire demo trading flows with strong logging, risk checks, and monitoring hooks.

Each stage prioritizes clarity, testing, and auditability so findings are easy to explain and extend.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> Tooling details will solidify once the packaging baseline is finalized.

## Repo Directory Layout

- `src/` – package source code.
- `data/` – data artifacts (ignored by default; keep curated exports under version control if needed).
- `docs/` – documentation, journals, and process notes.
- `tests/` – unit and integration tests.
- `scripts/` – automation helpers (setup, linting, data pulls).
- `auto.sh` – helper script to commit file changes one file at a time.

## Journaling

Updates, decisions, and all my learnings flow into `docs/journal.md` so future me (or maybe possible collaborators) can replay the rationale behind each change I made.


