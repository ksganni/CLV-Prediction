"""
generate_data.py
----------------
Creates a fake retail transaction CSV so you can run
the project without downloading anything.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def generate_transactions(
    n_customers: int = 500,
    start: str = "2023-01-01",
    end: str = "2024-12-31",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate realistic-ish purchase history for demo customers."""
    rng = np.random.default_rng(seed)
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    days = (end_ts - start_ts).days

    rows: list[dict] = []
    invoice_id = 10000

    for customer_id in range(1, n_customers + 1):
        # Mix of buyer types: champions, loyal, at-risk, lost, new
        buyer_type = rng.choice(
            ["champion", "loyal", "potential", "atrisk", "lost"],
            p=[0.12, 0.25, 0.28, 0.20, 0.15],
        )

        if buyer_type == "champion":
            n_orders = int(rng.integers(8, 20))
            avg_qty = 4
            avg_price = 45
        elif buyer_type == "loyal":
            n_orders = int(rng.integers(5, 12))
            avg_qty = 3
            avg_price = 30
        elif buyer_type == "potential":
            n_orders = int(rng.integers(2, 6))
            avg_qty = 2
            avg_price = 22
        elif buyer_type == "atrisk":
            n_orders = int(rng.integers(3, 8))
            avg_qty = 3
            avg_price = 28
        else:  # lost
            n_orders = int(rng.integers(1, 3))
            avg_qty = 1
            avg_price = 15

        # Spread purchases across the timeline (at-risk / lost buy earlier)
        if buyer_type in {"atrisk", "lost"}:
            window_end = int(days * 0.55)
        else:
            window_end = days

        purchase_days = sorted(rng.integers(0, max(window_end, 1), size=n_orders))

        for day_offset in purchase_days:
            invoice_id += 1
            items_in_invoice = int(rng.integers(1, 4))
            for _ in range(items_in_invoice):
                rows.append(
                    {
                        "invoice_id": invoice_id,
                        "customer_id": customer_id,
                        "invoice_date": start_ts + pd.Timedelta(days=int(day_offset)),
                        "quantity": max(1, int(rng.normal(avg_qty, 1))),
                        "unit_price": round(max(1.0, float(rng.normal(avg_price, avg_price * 0.25))), 2),
                    }
                )

    return pd.DataFrame(rows)


def main(project_root: Path | None = None) -> Path:
    root = project_root or Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_path = data_dir / "sample_transactions.csv"

    df = generate_transactions()
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df):,} rows for {df['customer_id'].nunique()} customers -> {out_path}")
    return out_path


if __name__ == "__main__":  # pragma: no cover
    main()
