"""
run_pipeline.py
---------------
One command to:
  1. Prefer UCI Online Retail data (if downloaded)
  2. Else use / create synthetic sample data
  3. Build RFM table
  4. Fit BG/NBD + Gamma-Gamma
  5. Segment customers
  6. Save results to outputs/
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as: python scripts/run_pipeline.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.clv_model import run_clv_pipeline
from src.data_prep import prepare_rfm
from src.data_source import describe_data_source, resolve_transactions_path
from src.segmentation import kmeans_segments, segment_customers, segment_summary


def main() -> None:
    data_path = resolve_transactions_path()
    source_label = describe_data_source(data_path)
    print(f"Using dataset: {source_label}")
    print(f"  File: {data_path}")

    if data_path.name != "online_retail_transactions.csv":
        print(
            "Tip: for the famous public dataset, run:\n"
            "  python src/download_online_retail.py"
        )

    out_dir = PROJECT_ROOT / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Building RFM summary...")
    rfm = prepare_rfm(data_path)
    print(f"  Customers in RFM table: {len(rfm)}")

    print("Fitting BG/NBD + Gamma-Gamma and predicting CLV...")
    predictions, _, _ = run_clv_pipeline(rfm, months=12)

    print("Segmenting customers...")
    segmented = segment_customers(predictions)
    segmented = kmeans_segments(segmented)

    customers_path = out_dir / "customer_clv.csv"
    summary_path = out_dir / "segment_summary.csv"

    segmented.to_csv(customers_path, index=False)
    summary = segment_summary(segmented)
    summary.to_csv(summary_path, index=False)

    print("\n=== Segment summary ===")
    print(summary.to_string(index=False))
    print(f"\nSaved customer predictions -> {customers_path}")
    print(f"Saved segment summary     -> {summary_path}")

    from src.build_dashboard import build_dashboard

    dashboard_path = build_dashboard(open_browser=False)
    print(f"Saved dashboard           -> {dashboard_path}")
    print("\nDone! Open the dashboard with:")
    print("  python src/build_dashboard.py")


if __name__ == "__main__":
    main()
