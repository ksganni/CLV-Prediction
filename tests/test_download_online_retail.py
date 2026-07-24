"""Coverage for Online Retail download helpers (mocked network)."""

import ssl
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import urllib.error

import src.download_online_retail as dl


def test_ssl_context_with_and_without_certifi(monkeypatch):
    ctx = dl._ssl_context()
    assert isinstance(ctx, ssl.SSLContext)

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "certifi":
            raise ImportError("no certifi")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    ctx2 = dl._ssl_context()
    assert isinstance(ctx2, ssl.SSLContext)


def test_download_xlsx_uses_existing_file(tmp_path: Path):
    dest = tmp_path / "OnlineRetail.xlsx"
    dest.write_bytes(b"fake-excel")
    out = dl.download_xlsx(dest=dest)
    assert out == dest


def test_download_xlsx_success(tmp_path: Path):
    dest = tmp_path / "OnlineRetail.xlsx"
    fake_response = MagicMock()
    fake_response.read.return_value = b"excel-bytes"
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("src.download_online_retail.urllib.request.urlopen", return_value=fake_response):
        out = dl.download_xlsx(dest=dest)
    assert out.exists()
    assert out.read_bytes() == b"excel-bytes"


def test_download_xlsx_curl_fallback(tmp_path: Path):
    dest = tmp_path / "OnlineRetail.xlsx"

    def fake_curl(cmd, check):
        Path(cmd[4]).write_bytes(b"from-curl")
        return MagicMock()

    with patch(
        "src.download_online_retail.urllib.request.urlopen",
        side_effect=urllib.error.URLError("ssl boom"),
    ), patch("src.download_online_retail.subprocess.run", side_effect=fake_curl) as run:
        out = dl.download_xlsx(dest=dest)
    assert out.read_bytes() == b"from-curl"
    assert run.called


def test_download_xlsx_raises_when_empty(tmp_path: Path):
    dest = tmp_path / "OnlineRetail.xlsx"
    fake_response = MagicMock()
    fake_response.read.return_value = b""
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("src.download_online_retail.urllib.request.urlopen", return_value=fake_response):
        with pytest.raises(RuntimeError, match="Download failed"):
            dl.download_xlsx(dest=dest)


def test_online_retail_missing_columns(tmp_path: Path):
    bad = pd.DataFrame({"InvoiceNo": [1], "Quantity": [1]})
    path = tmp_path / "bad.xlsx"
    bad.to_excel(path, index=False)
    with pytest.raises(ValueError, match="Missing"):
        dl.online_retail_to_transactions(path)


def test_online_retail_without_country_and_all_countries(tmp_path: Path):
    raw = pd.DataFrame(
        {
            "InvoiceNo": ["1", "2"],
            "InvoiceDate": pd.to_datetime(["2011-01-01", "2011-01-02"]),
            "CustomerID": [100.0, 101.0],
            "Quantity": [1, 2],
            "UnitPrice": [3.0, 4.0],
        }
    )
    path = tmp_path / "no_country.xlsx"
    raw.to_excel(path, index=False)
    out = dl.online_retail_to_transactions(path, uk_only=False)
    assert (out["country"] == "Unknown").all()
    assert len(out) == 2


def test_save_clean_csv_and_main(tmp_path: Path, monkeypatch):
    xlsx = tmp_path / "OnlineRetail.xlsx"
    clean = tmp_path / "online_retail_transactions.csv"
    raw = pd.DataFrame(
        {
            "InvoiceNo": ["1"],
            "InvoiceDate": pd.to_datetime(["2011-01-01"]),
            "CustomerID": [55.0],
            "Quantity": [2],
            "UnitPrice": [3.5],
            "Country": ["United Kingdom"],
        }
    )
    raw.to_excel(xlsx, index=False)

    monkeypatch.setattr(dl, "RAW_XLSX", xlsx)
    monkeypatch.setattr(dl, "CLEAN_CSV", clean)
    monkeypatch.setattr(dl, "download_xlsx", lambda: xlsx)

    out = dl.main(uk_only=True)
    assert out == clean
    assert clean.exists()
