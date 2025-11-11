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




