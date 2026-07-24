"""
segmentation.py
---------------
Assigns each customer a value segment using RFM + CLV scores.

Segments:
  Champions  - high value, recent, frequent
  Loyal      - good value and frequency
  Potential  - newer or mid-value customers
  At-Risk    - were valuable but going quiet
  Lost       - inactive / low engagement
"""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


SEGMENT_ORDER = ["Champions", "Loyal", "Potential", "At-Risk", "Lost"]


def add_rfm_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score Recency / Frequency / Monetary into 1-5 buckets.
    Higher score = better customer behavior.
    Note: for Recency in Lifetimes, higher recency (days since first to last)
    with recent activity is good; we also use T - recency as "days since last buy".
    """
    scored = df.copy()

    # Days since last purchase (lower is better)
    scored["days_since_last"] = (scored["T"] - scored["recency"]).clip(lower=0)

    scored["R_score"] = pd.qcut(
        scored["days_since_last"].rank(method="first"),
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    scored["F_score"] = pd.qcut(
        scored["frequency"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    scored["M_score"] = pd.qcut(
        scored["monetary_value"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    scored["RFM_score"] = scored["R_score"] + scored["F_score"] + scored["M_score"]
    return scored


def rule_based_segment(row: pd.Series) -> str:
    """Simple business rules using RFM scores + CLV."""
    r, f, m = row["R_score"], row["F_score"], row["M_score"]
    rfm = row["RFM_score"]
    clv = row.get("clv", 0)

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and clv >= row.get("clv_median", 0):
        return "Loyal"
    if r <= 2 and (f >= 3 or m >= 3):
        return "At-Risk"
    if r <= 2 and f <= 2:
        return "Lost"
    if rfm >= 10:
        return "Loyal"
    return "Potential"


def segment_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Add RFM scores and a segment label to each customer."""
    scored = add_rfm_scores(df)
    scored["clv_median"] = scored["clv"].median() if "clv" in scored.columns else 0
    scored["segment"] = scored.apply(rule_based_segment, axis=1)
    scored["segment"] = pd.Categorical(scored["segment"], categories=SEGMENT_ORDER, ordered=True)
    return scored.drop(columns=["clv_median"])


def kmeans_segments(df: pd.DataFrame, n_clusters: int = 4, random_state: int = 42) -> pd.DataFrame:
    """
    Extra: cluster customers with K-Means on RFM + CLV features.
    Useful for portfolio / interview talking points.
    """
    features = df[["frequency", "recency", "monetary_value", "clv"]].fillna(0)
    scaled = StandardScaler().fit_transform(features)

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    out = df.copy()
    out["kmeans_cluster"] = km.fit_predict(scaled)
    return out


def segment_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by segment for the dashboard."""
    summary = (
        df.groupby("segment", observed=True)
        .agg(
            customers=("customer_id", "count"),
            avg_clv=("clv", "mean"),
            total_clv=("clv", "sum"),
            avg_frequency=("frequency", "mean"),
            avg_spend=("monetary_value", "mean"),
        )
        .reset_index()
    )
    summary["avg_clv"] = summary["avg_clv"].round(2)
    summary["total_clv"] = summary["total_clv"].round(2)
    summary["avg_frequency"] = summary["avg_frequency"].round(2)
    summary["avg_spend"] = summary["avg_spend"].round(2)
    return summary
