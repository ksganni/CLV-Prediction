"""Coverage for data_source helpers."""

from pathlib import Path

from src.data_source import describe_data_source, resolve_transactions_path
import src.data_source as ds


def test_resolve_falls_back_to_sample(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sample = data_dir / "sample_transactions.csv"
    sample.write_text("customer_id,invoice_date,quantity,unit_price\n1,2020-01-01,1,2.0\n")
    online = data_dir / "online_retail_transactions.csv"

    monkeypatch.setattr(ds, "DATA_DIR", data_dir)
    monkeypatch.setattr(ds, "ONLINE_RETAIL_CSV", online)
    monkeypatch.setattr(ds, "SAMPLE_CSV", sample)

    assert resolve_transactions_path() == sample
    assert describe_data_source(sample) == "Synthetic sample data"


def test_resolve_generates_sample_when_missing(tmp_path: Path, monkeypatch):
    data_dir = tmp_path / "data"
    online = data_dir / "online_retail_transactions.csv"
    sample = data_dir / "sample_transactions.csv"

    monkeypatch.setattr(ds, "DATA_DIR", data_dir)
    monkeypatch.setattr(ds, "ONLINE_RETAIL_CSV", online)
    monkeypatch.setattr(ds, "SAMPLE_CSV", sample)

    chosen = resolve_transactions_path()
    assert chosen == sample
    assert sample.exists()


def test_describe_unknown_name(tmp_path: Path):
    path = tmp_path / "other.csv"
    assert describe_data_source(path) == "other.csv"
