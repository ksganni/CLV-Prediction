"""Tests for customer segmentation."""

import pandas as pd

from src.segmentation import (
    SEGMENT_ORDER,
    add_rfm_scores,
    kmeans_segments,
    segment_customers,
    segment_summary,
)


def _fake_predictions(n: int = 50) -> pd.DataFrame:
    rng_freq = list(range(n))
    return pd.DataFrame(
        {
            "customer_id": [str(i) for i in range(n)],
            "frequency": [i % 10 for i in rng_freq],
            "recency": [float((i * 7) % 200) for i in rng_freq],
            "T": [float(200 + (i % 50)) for i in rng_freq],
            "monetary_value": [10.0 + (i % 40) for i in rng_freq],
            "clv": [50.0 + i * 3 for i in rng_freq],
        }
    )


def test_add_rfm_scores():
    scored = add_rfm_scores(_fake_predictions())
    assert {"R_score", "F_score", "M_score", "RFM_score"}.issubset(scored.columns)
    assert scored["R_score"].between(1, 5).all()


def test_segment_customers_labels():
    segmented = segment_customers(_fake_predictions())
    assert "segment" in segmented.columns
    assert set(segmented["segment"].astype(str)).issubset(set(SEGMENT_ORDER))


def test_segment_summary_has_rows():
    segmented = segment_customers(_fake_predictions())
    summary = segment_summary(segmented)
    assert not summary.empty
    assert "customers" in summary.columns
    assert summary["customers"].sum() == 50


def test_kmeans_segments():
    clustered = kmeans_segments(_fake_predictions(), n_clusters=4)
    assert "kmeans_cluster" in clustered.columns
    assert clustered["kmeans_cluster"].nunique() <= 4
