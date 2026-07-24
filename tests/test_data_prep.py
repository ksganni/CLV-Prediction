"""Tests for data preparation helpers."""

from pathlib import Path

import pandas as pd
import pytest

from src.data_prep import build_rfm_summary, clean_transactions, load_transactions, prepare_rfm


def test_clean_transactions_drops_bad_rows():
    raw = pd.DataFrame(
        {
            "customer_id": [1, 1, 2, 3],
            "invoice_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "quantity": [2, -1, 0, 3],
            "unit_price": [10.0, 5.0, 8.0, 4.0],
        }
    )
    clean = clean_transactions(raw)
    assert len(clean) == 2
    assert set(clean["customer_id"]) == {"1", "3"}
    assert "revenue" in clean.columns


def test_build_rfm_summary_shape():
    clean = pd.DataFrame(
        {
            "customer_id": ["1", "1", "1", "2", "2"],
            "invoice_date": pd.to_datetime(
                ["2024-01-01", "2024-02-01", "2024-03-01", "2024-01-15", "2024-04-01"]
            ),
            "revenue": [20.0, 30.0, 25.0, 40.0, 50.0],
        }
    )
    rfm = build_rfm_summary(clean, observation_end=pd.Timestamp("2024-04-30"))
    assert set(rfm.columns) >= {"customer_id", "frequency", "recency", "T", "monetary_value"}
    assert len(rfm) == 2
    cust1 = rfm.loc[rfm["customer_id"] == "1"].iloc[0]
    assert cust1["frequency"] == 2  # 3 purchases -> 2 repeat


def test_prepare_rfm_with_sample_file(tmp_path: Path):
    csv_path = tmp_path / "tx.csv"
    pd.DataFrame(
        {
            "customer_id": [1, 1, 2],
            "invoice_date": ["2024-01-01", "2024-02-01", "2024-01-10"],
            "quantity": [1, 2, 1],
            "unit_price": [10.0, 15.0, 20.0],
        }
    ).to_csv(csv_path, index=False)

    rfm = prepare_rfm(csv_path)
    assert not rfm.empty
    assert rfm["frequency"].min() >= 0


def test_load_transactions_missing_file():
    with pytest.raises(FileNotFoundError):
        load_transactions("does_not_exist.csv")


def test_load_transactions_missing_columns(tmp_path: Path):
    csv_path = tmp_path / "bad.csv"
    pd.DataFrame({"customer_id": [1], "quantity": [1]}).to_csv(csv_path, index=False)
    with pytest.raises(ValueError, match="Missing required columns"):
        load_transactions(csv_path)
