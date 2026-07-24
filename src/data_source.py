"""
data_source.py
--------------
Picks which transactions file to use.

Priority:
  1. data/online_retail_transactions.csv  (UCI Online Retail - preferred)
  2. data/sample_transactions.csv         (synthetic - CI / fallback)
"""

from __future__ import annotations

from pathlib import Path

from src.generate_data import generate_transactions

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

ONLINE_RETAIL_CSV = DATA_DIR / "online_retail_transactions.csv"
SAMPLE_CSV = DATA_DIR / "sample_transactions.csv"


def resolve_transactions_path(prefer_online_retail: bool = True) -> Path:
    """
    Return the best available transactions CSV path.
    Creates synthetic sample data only if nothing else exists.
    """
    if prefer_online_retail and ONLINE_RETAIL_CSV.exists():
        return ONLINE_RETAIL_CSV

    if SAMPLE_CSV.exists():
        return SAMPLE_CSV

    # Last resort: generate tiny synthetic data so the project still runs
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generate_transactions().to_csv(SAMPLE_CSV, index=False)
    return SAMPLE_CSV


def describe_data_source(path: Path) -> str:
    """Short label for logs / dashboard."""
    name = path.name
    if name == ONLINE_RETAIL_CSV.name:
        return "UCI Online Retail (UK)"
    if name == SAMPLE_CSV.name:
        return "Synthetic sample data"
    return name
