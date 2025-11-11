"""Command-line runner for the MT5 live/paper loop."""

from __future__ import annotations

import argparse
import logging

from synthetic_quant_engine.live.mt5 import LiveTradingLoop, load_mt5_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MT5 live/paper trading loop.")
    parser.add_argument(
        "--paper",
        action="store_true",
        help="Force paper mode regardless of environment variable.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Force live mode (disables paper mode). Use with caution.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings = load_mt5_settings()
    if args.paper and args.live:
        raise SystemExit("Specify only one of --paper or --live.")
    if args.paper:
        settings.paper_mode = True
    if args.live:
        settings.paper_mode = False

    loop = LiveTradingLoop(settings=settings)
    loop.run()


if __name__ == "__main__":
    main()

