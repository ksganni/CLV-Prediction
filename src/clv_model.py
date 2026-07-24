"""
clv_model.py
------------
Predicts Customer Lifetime Value using:
  1. BG/NBD  -> expected future purchases
  2. Gamma-Gamma -> expected average spend
  3. CLV = purchases * spend (over a time horizon)
"""

from __future__ import annotations

import warnings

import pandas as pd
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import ConvergenceError


def fit_bgnbd(
    rfm: pd.DataFrame,
    penalizer: float | None = None,
) -> BetaGeoFitter:
    """
    Fit BG/NBD on RFM frequency / recency / T.

    Online Retail can fail with some penalizer values, so we try a few
    safe options unless a specific penalizer is requested.
    """
    candidates = [penalizer] if penalizer is not None else [0.0, 0.05, 0.1, 0.5, 1.0]
    last_error: Exception | None = None

    for coef in candidates:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = BetaGeoFitter(penalizer_coef=float(coef))
                model.fit(rfm["frequency"], rfm["recency"], rfm["T"])
            return model
        except ConvergenceError as exc:
            last_error = exc

    raise ConvergenceError(
        "BG/NBD did not converge. Tried penalizers "
        f"{candidates}. Last error: {last_error}"
    )


def fit_gamma_gamma(rfm: pd.DataFrame, penalizer: float = 0.0) -> GammaGammaFitter:
    """
    Fit Gamma-Gamma on returning customers with positive spend.
    Extreme spend outliers are excluded from fitting (they break convergence).
    """
    returning = rfm[(rfm["frequency"] > 0) & (rfm["monetary_value"] > 0)].copy()
    if returning.empty:
        raise ValueError("Need customers with repeat purchases to fit Gamma-Gamma.")

    # Drop extreme outliers from the fit only (keep them in prediction set)
    cap = returning["monetary_value"].quantile(0.995)
    train = returning[returning["monetary_value"] <= cap]
    if len(train) < 50:
        train = returning

    model = GammaGammaFitter(penalizer_coef=penalizer)
    model.fit(train["frequency"], train["monetary_value"])
    return model


def predict_clv(
    rfm: pd.DataFrame,
    bgnbd: BetaGeoFitter,
    ggf: GammaGammaFitter,
    months: int = 12,
    discount_rate: float = 0.01,
) -> pd.DataFrame:
    """
    Add predicted purchases, predicted spend, and CLV columns.
    `months` is the forecast horizon (default 12 months).
    """
    result = rfm.copy()
    t_days = months * 30

    result["predicted_purchases"] = bgnbd.predict(
        t_days,
        result["frequency"],
        result["recency"],
        result["T"],
    )

    # Gamma-Gamma only works well for returning customers
    result["predicted_avg_spend"] = 0.0
    returning_mask = (result["frequency"] > 0) & (result["monetary_value"] > 0)
    if returning_mask.any():
        result.loc[returning_mask, "predicted_avg_spend"] = ggf.conditional_expected_average_profit(
            result.loc[returning_mask, "frequency"],
            result.loc[returning_mask, "monetary_value"],
        )

    # For one-time buyers, fall back to overall mean spend of returning customers
    fallback = result.loc[returning_mask, "monetary_value"].mean() if returning_mask.any() else 0.0
    result.loc[~returning_mask, "predicted_avg_spend"] = fallback

    # customer_lifetime_value needs positive monetary_value
    monetary_for_clv = result["monetary_value"].clip(lower=0.01)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result["clv"] = ggf.customer_lifetime_value(
            bgnbd,
            result["frequency"],
            result["recency"],
            result["T"],
            monetary_for_clv,
            time=months,
            discount_rate=discount_rate,
            freq="D",
        )

    # One-time buyers may get 0 monetary_value; use simple estimate instead
    simple = result["predicted_purchases"] * result["predicted_avg_spend"]
    needs_fallback = result["monetary_value"] <= 0
    result.loc[needs_fallback, "clv"] = simple.loc[needs_fallback]

    result["clv"] = result["clv"].clip(lower=0).round(2)
    result["predicted_purchases"] = result["predicted_purchases"].clip(lower=0).round(2)
    result["predicted_avg_spend"] = result["predicted_avg_spend"].clip(lower=0).round(2)
    return result


def run_clv_pipeline(rfm: pd.DataFrame, months: int = 12) -> tuple[pd.DataFrame, BetaGeoFitter, GammaGammaFitter]:
    """Fit both models and return predictions + fitted models."""
    bgnbd = fit_bgnbd(rfm)
    ggf = fit_gamma_gamma(rfm)
    predictions = predict_clv(rfm, bgnbd, ggf, months=months)
    return predictions, bgnbd, ggf
