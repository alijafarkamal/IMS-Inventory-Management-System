"""Simple persistence helper for notifier/email settings.

Stores a JSON file under the app `DATA_DIR` so settings persist between runs.
This keeps UI and notifier configuration decoupled from environment variables.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

from inventory_app.config import DATA_DIR
from inventory_app.utils.logging import logger


FILE_PATH = Path(DATA_DIR) / "notification_config.json"


def load_notification_config() -> Dict[str, Any]:
    if not FILE_PATH.exists():
        return {"sender": "", "recipients": []}
    try:
        with FILE_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            # Normalise recipients to list
            recipients = data.get("recipients", []) or []
            if isinstance(recipients, str):
                recipients = [r.strip() for r in recipients.split(",") if r.strip()]
            return {"sender": data.get("sender", ""), "recipients": recipients}
    except Exception as e:
        logger.error(f"Failed to load notification config: {e}")
        return {"sender": "", "recipients": []}


def save_notification_config(sender: str, recipients: list[str]) -> None:
    data = {"sender": sender or "", "recipients": recipients or []}
    try:
        with FILE_PATH.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception as e:
        logger.error(f"Failed to save notification config: {e}")
