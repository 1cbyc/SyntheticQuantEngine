"""Pydantic-based configuration for MT5 live trading."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, SecretStr

from synthetic_quant_engine.settings import load_env_file


class MT5AccountSettings(BaseModel):
    """Credentials and connection details for the MT5 terminal."""

    login: int = Field(..., description="MT5 account login number.")
    password: SecretStr = Field(..., description="Password for the MT5 account.")
    server: str = Field(..., description="Broker server name, e.g. 'Deriv-Demo'.")
    terminal_path: Optional[Path] = Field(
        default=None,
        description="Optional path to terminal64.exe (if running headless).",
    )


class MT5StrategySettings(BaseModel):
    """Strategy-level configuration."""

    symbol_whitelist: List[str] = Field(
        default_factory=lambda: ["Volatility 25 Index"],
        description="Symbols to monitor/trade via MT5.",
    )
    timeframe: str = Field(
        default="M5",
        description="Primary timeframe string (MT5 format e.g. M1, M5, H1).",
    )
    fast_window: int = Field(default=20, description="Fast SMA period for live signals.")
    slow_window: int = Field(default=50, description="Slow SMA period for live signals.")
    min_confidence: float = Field(
        default=0.65,
        description="Confidence threshold before executing a trade.",
    )
    polling_seconds: int = Field(
        default=60,
        description="Seconds between each polling cycle for new candles.",
    )


class MT5RiskSettings(BaseModel):
    """Risk management guards for the live loop."""

    max_daily_loss: float = Field(default=100.0, description="Daily loss stop in account currency.")
    max_daily_profit: float = Field(default=250.0, description="Daily take-profit lock.")
    max_positions: int = Field(default=5, description="Maximum concurrent open positions.")
    risk_per_trade_percent: float = Field(
        default=1.0,
        description="Percentage of equity risked per trade.",
    )
    stop_loss_pips: float = Field(
        default=20.0,
        description="Baseline stop-loss distance in pips for sizing calculations.",
    )
    take_profit_pips: float = Field(
        default=30.0,
        description="Baseline take-profit distance in pips for sizing calculations.",
    )
    trailing_start_pips: float = Field(
        default=10.0,
        description="Pip profit threshold before starting trailing stops.",
    )
    max_consecutive_losses: int = Field(
        default=3,
        description="Pause trading after this many consecutive losing trades.",
    )


class MT5Settings(BaseModel):
    """Aggregate configuration for live/paper trading."""

    account: MT5AccountSettings
    strategy: MT5StrategySettings = Field(default_factory=MT5StrategySettings)
    risk: MT5RiskSettings = Field(default_factory=MT5RiskSettings)
    paper_mode: bool = Field(
        default=True,
        description="If True, simulate fills instead of sending real MT5 orders.",
    )


def load_mt5_settings(env_prefix: str = "DERIV_MT5_") -> MT5Settings:
    """Load MT5 settings from environment variables / .env."""

    load_env_file()
    mapping = {
        "login": f"{env_prefix}LOGIN",
        "password": f"{env_prefix}PASSWORD",
        "server": f"{env_prefix}SERVER",
        "terminal_path": f"{env_prefix}TERMINAL_PATH",
        "symbols": f"{env_prefix}SYMBOLS",
    }

    login = int(_require_env(mapping["login"]))
    password = _require_env(mapping["password"])
    server = _require_env(mapping["server"])
    terminal_path = _optional_env(mapping["terminal_path"])

    symbol_list = _optional_env(mapping["symbols"])
    symbols = (
        [symbol.strip() for symbol in symbol_list.split(",") if symbol.strip()]
        if symbol_list
        else None
    )

    account = MT5AccountSettings(
        login=login,
        password=SecretStr(password),
        server=server,
        terminal_path=Path(terminal_path).expanduser() if terminal_path else None,
    )

    strategy = MT5StrategySettings()
    if symbols:
        strategy.symbol_whitelist = symbols

    paper_mode_env = _optional_env(f"{env_prefix}PAPER_MODE")
    paper_mode = True if paper_mode_env is None else paper_mode_env.lower() != "false"

    risk = MT5RiskSettings()

    return MT5Settings(account=account, strategy=strategy, risk=risk, paper_mode=paper_mode)


def _require_env(name: str) -> str:
    value = _optional_env(name)
    if value is None:
        raise RuntimeError(f"Required MT5 environment variable '{name}' is missing.")
    return value


def _optional_env(name: str) -> str | None:
    import os

    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()

