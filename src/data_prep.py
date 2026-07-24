"""
data_prep.py
------------
Turns raw transaction rows into RFM summary data
that CLV models need.

RFM means:
  Recency   = days since last purchase
  Frequency = how many repeat purchases
  Monetary  = average spend per purchase
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {"customer_id", "invoice_date", "quantity", "unit_price"}


def load_transactions(csv_path: str | Path) -> pd.DataFrame:
    """Load transaction CSV and check required columns exist."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    return df


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Remove bad rows (returns, zeros, negatives)."""
    clean = df.copy()
    clean["invoice_date"] = pd.to_datetime(clean["invoice_date"], errors="coerce")
    clean["invoice_date"] = clean["invoice_date"].dt.normalize()
    clean["revenue"] = clean["quantity"] * clean["unit_price"]

    # Keep only positive purchases (drops Online Retail returns / cancellations)
    clean = clean[
        (clean["quantity"] > 0)
        & (clean["unit_price"] > 0)
        & (clean["revenue"] > 0)
    ]

    clean = clean.dropna(subset=["customer_id", "invoice_date"])
    clean["customer_id"] = clean["customer_id"].astype(str)
    return clean.reset_index(drop=True)


def build_rfm_summary(df: pd.DataFrame, observation_end: pd.Timestamp | None = None) -> pd.DataFrame:
    """
    Build one row per customer with RFM fields used by Lifetimes.

    Returns columns:
      customer_id, frequency, recency, T, monetary_value
    """
    if observation_end is None:
        observation_end = df["invoice_date"].max()

    # One purchase event per customer per day
    purchases = (
        df.groupby(["customer_id", "invoice_date"], as_index=False)["revenue"]
        .sum()
        .sort_values(["customer_id", "invoice_date"])
    )

    first_purchase = purchases.groupby("customer_id")["invoice_date"].min()
    last_purchase = purchases.groupby("customer_id")["invoice_date"].max()
    n_purchases = purchases.groupby("customer_id")["invoice_date"].count()

    # Average spend for repeat buyers (exclude first purchase for Gamma-Gamma)
    monetary = (
        purchases.groupby("customer_id")
        .apply(_avg_spend_excluding_first, include_groups=False)
        .rename("monetary_value")
    )

    summary = pd.DataFrame(
        {
            "frequency": (n_purchases - 1).clip(lower=0),
            "recency": (last_purchase - first_purchase).dt.days.astype(float),
            "T": (observation_end - first_purchase).dt.days.astype(float),
            "monetary_value": monetary,
        }
    )
    summary = summary.reset_index()
    summary = summary[summary["T"] > 0].copy()
    return summary.reset_index(drop=True)


def _avg_spend_excluding_first(group: pd.DataFrame) -> float:
    """Average revenue after the first purchase (0 if only one purchase)."""
    if len(group) <= 1:
        return 0.0
    return float(group.iloc[1:]["revenue"].mean())


def prepare_rfm(csv_path: str | Path) -> pd.DataFrame:
    """Full pipeline: load -> clean -> RFM summary."""
    raw = load_transactions(csv_path)
    cleaned = clean_transactions(raw)
    return build_rfm_summary(cleaned)
