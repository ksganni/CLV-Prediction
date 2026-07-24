"""
download_online_retail.py
-------------------------
Downloads the famous UCI Online Retail dataset and saves a clean
transactions CSV your CLV pipeline can use.

Source:
  https://archive.ics.uci.edu/dataset/352/online+retail
"""

from __future__ import annotations

import ssl
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

# Official UCI mirror of Online Retail.xlsx
UCI_XLSX_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_XLSX = DATA_DIR / "OnlineRetail.xlsx"
CLEAN_CSV = DATA_DIR / "online_retail_transactions.csv"


def _ssl_context() -> ssl.SSLContext:
    """Use certifi certificates when available (fixes macOS Python SSL issues)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def download_xlsx(url: str = UCI_XLSX_URL, dest: Path | None = None) -> Path:
    """Download the Excel file if it is not already on disk."""
    dest = dest or RAW_XLSX
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"Raw file already exists: {dest}")
        return dest

    print(f"Downloading Online Retail from UCI...\n  {url}")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "clv-prediction/1.0"})
        with urllib.request.urlopen(request, context=_ssl_context(), timeout=120) as response:
            dest.write_bytes(response.read())
    except (urllib.error.URLError, ssl.SSLError) as exc:
        print(f"Python download failed ({exc}). Trying curl fallback...")
        subprocess.run(
            ["curl", "-L", "--fail", "-o", str(dest), url],
            check=True,
        )

    if not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError("Download failed. Check your internet connection and try again.")

    print(f"Saved raw Excel -> {dest}")
    return dest


def online_retail_to_transactions(
    xlsx_path: Path,
    uk_only: bool = True,
) -> pd.DataFrame:
    """
    Convert UCI Online Retail columns into the project's schema:
      customer_id, invoice_date, quantity, unit_price[, invoice_id, country]
    """
    raw = pd.read_excel(xlsx_path, engine="openpyxl")

    # Normalize column names just in case
    raw.columns = [str(c).strip() for c in raw.columns]

    needed = {"InvoiceNo", "InvoiceDate", "CustomerID", "Quantity", "UnitPrice"}
    missing = needed - set(raw.columns)
    if missing:
        raise ValueError(f"Unexpected Online Retail columns. Missing: {sorted(missing)}")

    df = pd.DataFrame(
        {
            "invoice_id": raw["InvoiceNo"].astype(str),
            "customer_id": raw["CustomerID"],
            "invoice_date": pd.to_datetime(raw["InvoiceDate"], errors="coerce"),
            "quantity": pd.to_numeric(raw["Quantity"], errors="coerce"),
            "unit_price": pd.to_numeric(raw["UnitPrice"], errors="coerce"),
            "country": raw["Country"] if "Country" in raw.columns else "Unknown",
        }
    )

    # Classic CLV tutorials often keep United Kingdom only
    if uk_only and "country" in df.columns:
        df = df[df["country"] == "United Kingdom"]

    # Drop guest checkouts / bad rows early
    df = df.dropna(subset=["customer_id", "invoice_date"])
    df["customer_id"] = df["customer_id"].astype(int).astype(str)

    # Use calendar day as the purchase date (standard for RFM / Lifetimes)
    df["invoice_date"] = df["invoice_date"].dt.normalize()

    return df.reset_index(drop=True)


def save_clean_csv(df: pd.DataFrame, dest: Path | None = None) -> Path:
    dest = dest or CLEAN_CSV
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest, index=False)
    print(
        f"Wrote {len(df):,} rows for {df['customer_id'].nunique():,} customers -> {dest}"
    )
    return dest


def main(uk_only: bool = True) -> Path:
    xlsx = download_xlsx()
    clean = online_retail_to_transactions(xlsx, uk_only=uk_only)
    return save_clean_csv(clean)


if __name__ == "__main__":  # pragma: no cover
    main()
