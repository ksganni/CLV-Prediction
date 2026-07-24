"""Tests for Online Retail column conversion (no network needed)."""

from pathlib import Path

import pandas as pd

from src.data_source import describe_data_source, resolve_transactions_path
from src.download_online_retail import online_retail_to_transactions


def test_online_retail_to_transactions(tmp_path: Path):
    # Tiny fake Excel-like table written then read back through the converter path
    raw = pd.DataFrame(
        {
            "InvoiceNo": ["536365", "536365", "536366", "C536367"],
            "StockCode": ["85123A", "71053", "84406B", "22423"],
            "Description": ["A", "B", "C", "D"],
            "Quantity": [6, 6, 2, -1],
            "InvoiceDate": pd.to_datetime(
                ["2010-12-01 08:26:00", "2010-12-01 08:26:00", "2010-12-02 09:00:00", "2010-12-03 10:00:00"]
            ),
            "UnitPrice": [2.55, 3.39, 2.75, 12.60],
            "CustomerID": [17850.0, 17850.0, 17850.0, 17850.0],
            "Country": ["United Kingdom", "United Kingdom", "France", "United Kingdom"],
        }
    )
    xlsx_path = tmp_path / "tiny.xlsx"
    raw.to_excel(xlsx_path, index=False)

    uk = online_retail_to_transactions(xlsx_path, uk_only=True)
    assert set(uk.columns) >= {"customer_id", "invoice_date", "quantity", "unit_price"}
    assert (uk["country"] == "United Kingdom").all()
    assert uk["customer_id"].iloc[0] == "17850"
    # Same calendar day should be normalized
    assert uk["invoice_date"].dt.hour.eq(0).all()


def test_resolve_prefers_online_retail(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    online = data_dir / "online_retail_transactions.csv"
    sample = data_dir / "sample_transactions.csv"
    online.write_text("customer_id,invoice_date,quantity,unit_price\n1,2020-01-01,1,1.0\n")
    sample.write_text("customer_id,invoice_date,quantity,unit_price\n2,2020-01-01,1,1.0\n")

    import src.data_source as ds

    monkeypatch.setattr(ds, "DATA_DIR", data_dir)
    monkeypatch.setattr(ds, "ONLINE_RETAIL_CSV", online)
    monkeypatch.setattr(ds, "SAMPLE_CSV", sample)

    chosen = resolve_transactions_path()
    assert chosen == online
    assert "Online Retail" in describe_data_source(chosen)
