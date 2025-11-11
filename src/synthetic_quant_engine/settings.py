"""Runtime settings helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass(slots=True)
class DerivSettings:
    """Configuration required to communicate with the Deriv API."""

    app_id: int
    api_token: Optional[str] = None
    endpoint: Optional[str] = None


def load_env_file() -> None:
    """Load environment variables from a local .env file if present."""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Call load_dotenv without arguments to respect default behaviour.
        load_dotenv()


def get_deriv_settings() -> DerivSettings:
    """Return Deriv API credentials sourced from environment variables."""
    load_env_file()

    app_id = os.getenv("DERIV_APP_ID")
    if not app_id:
        raise RuntimeError(
            "DERIV_APP_ID is not set. Provide it via environment variable or .env file."
        )

    api_token = os.getenv("DERIV_API_TOKEN")
    endpoint = os.getenv("DERIV_API_ENDPOINT")

    try:
        app_id_int = int(app_id)
    except ValueError as exc:
        raise RuntimeError("DERIV_APP_ID must be an integer.") from exc

    return DerivSettings(app_id=app_id_int, api_token=api_token, endpoint=endpoint)


