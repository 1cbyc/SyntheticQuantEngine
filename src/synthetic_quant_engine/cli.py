"""Command line interface for SyntheticQuantEngine."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from synthetic_quant_engine.data.fetch_volatility25 import (
    FetchConfiguration,
    fetch_volatility25_candles,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SyntheticQuantEngine command line interface."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser(
        "fetch-data",
        help="Fetch Volatility 25 historical candles and persist a curated CSV.",
    )
    fetch_parser.add_argument(
        "--count",
        type=int,
        default=1000,
        help="Number of candles to fetch (default: 1000).",
    )
    fetch_parser.add_argument(
        "--granularity",
        type=int,
        default=3600,
        help="Candle granularity in seconds (default: 3600 -> 1 hour).",
    )
    fetch_parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/vol25_1h.csv"),
        help="Destination CSV path.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "fetch-data":
        config = FetchConfiguration(
            count=args.count,
            granularity=args.granularity,
            output_path=args.output,
        )
        LOGGER.info(
            "Fetching %s candles with granularity %ss -> %s",
            config.count,
            config.granularity,
            config.output_path,
        )

        asyncio.run(fetch_volatility25_candles(config))
        LOGGER.info("Finished fetching data.")


if __name__ == "__main__":
    main()


