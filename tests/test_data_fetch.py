from __future__ import annotations

from pathlib import Path
import pytest

from synthetic_quant_engine.data.fetch_volatility25 import (
    Candle,
    FetchConfiguration,
    HistoryResponse,
    _granularity_slug,
    _to_dataframe,
)


def test_candle_parses_numeric_fields_and_defaults_volume() -> None:
    payload = {
        "epoch": 1,
        "open": "100.5",
        "high": "101.0",
        "low": "99.9",
        "close": "100.2",
        # Volume intentionally omitted
    }

    candle = Candle.model_validate(payload)

    assert candle.volume == 0
    assert isinstance(candle.open, float)
    assert candle.close == pytest.approx(100.2)


@pytest.mark.parametrize(
    ("granularity", "expected_slug"),
    [
        (3600, "1h"),
        (60, "1m"),
        (900, "15m"),
        (45, "45s"),
    ],
)
def test_granularity_slug(granularity: int, expected_slug: str) -> None:
    assert _granularity_slug(granularity) == expected_slug


def test_fetch_configuration_derives_default_output_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    config = FetchConfiguration(symbol="R_50", granularity=900, output_path=None)

    derived = config.derived_output_path()
    assert derived == Path("data/raw/r_50_15m.csv")

    # ensure_output_dir should create directories and return resolved path
    resolved = config.ensure_output_dir()
    assert resolved == tmp_path / derived
    assert resolved.exists() is False  # file shouldn't exist yet
    assert resolved.parent.is_dir()


def test_to_dataframe_orders_and_computes_sma() -> None:
    history = HistoryResponse(
        candles=[
            Candle(
                epoch=2,
                open=101,
                high=102,
                low=99,
                close=100,
                volume=5,
            ),
            Candle(
                epoch=1,
                open=50,
                high=55,
                low=45,
                close=50,
                volume=0,
            ),
        ]
    )

    df = _to_dataframe(history)

    assert list(df.columns) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "sma_20",
    ]
    assert len(df) == 2
    assert df.loc[0, "timestamp"] < df.loc[1, "timestamp"]
    assert df.loc[0, "sma_20"] == pytest.approx(50.0)
    assert df.loc[1, "sma_20"] == pytest.approx((50 + 100) / 2)

