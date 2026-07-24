"""Tests for CLV model pipeline."""

import pandas as pd
import pytest

from src.clv_model import fit_bgnbd, fit_gamma_gamma, predict_clv, run_clv_pipeline
from src.generate_data import generate_transactions
from src.data_prep import clean_transactions, build_rfm_summary


@pytest.fixture(scope="module")
def sample_rfm() -> pd.DataFrame:
    raw = generate_transactions(n_customers=120, seed=7)
    clean = clean_transactions(raw)
    return build_rfm_summary(clean)


def test_fit_bgnbd(sample_rfm):
    model = fit_bgnbd(sample_rfm)
    assert model.params_ is not None
    assert len(model.params_) > 0


def test_fit_gamma_gamma(sample_rfm):
    model = fit_gamma_gamma(sample_rfm)
    assert model.params_ is not None


def test_predict_clv_columns(sample_rfm):
    bgnbd = fit_bgnbd(sample_rfm)
    ggf = fit_gamma_gamma(sample_rfm)
    preds = predict_clv(sample_rfm, bgnbd, ggf, months=6)
    for col in ["predicted_purchases", "predicted_avg_spend", "clv"]:
        assert col in preds.columns
    assert (preds["clv"] >= 0).all()


def test_run_clv_pipeline(sample_rfm):
    preds, bgnbd, ggf = run_clv_pipeline(sample_rfm, months=12)
    assert len(preds) == len(sample_rfm)
    assert bgnbd is not None and ggf is not None
    assert preds["clv"].notna().all()
