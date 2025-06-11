from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "api" / "kb"


def load_json(file_name: str) -> dict:
    """Load a JSON file from the knowledge base."""
    with open(DATA_DIR / file_name, "r") as f:
        return json.load(f)
