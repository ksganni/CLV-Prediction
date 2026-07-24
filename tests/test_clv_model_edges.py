"""Extra coverage for CLV model edge cases."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from lifetimes.utils import ConvergenceError

from src.clv_model import fit_bgnbd, fit_gamma_gamma, predict_clv, run_clv_pipeline
from src.data_prep import build_rfm_summary, clean_transactions
from src.generate_data import generate_transactions


def test_fit_bgnbd_raises_when_all_penalizers_fail():
    rfm = pd.DataFrame(
        {
            "frequency": [1.0, 2.0],
            "recency": [10.0, 20.0],
            "T": [30.0, 40.0],
        }
    )

    with patch("src.clv_model.BetaGeoFitter") as mock_cls:
        instance = MagicMock()
        instance.fit.side_effect = ConvergenceError("nope")
        mock_cls.return_value = instance
        with pytest.raises(ConvergenceError, match="did not converge"):
            fit_bgnbd(rfm, penalizer=0.01)


def test_fit_gamma_gamma_requires_returning_customers():
    rfm = pd.DataFrame(
        {
            "frequency": [0, 0],
            "monetary_value": [0.0, 0.0],
        }
    )
    with pytest.raises(ValueError, match="repeat purchases"):
        fit_gamma_gamma(rfm)


def test_fit_gamma_gamma_uses_all_rows_when_few_returning():
    rfm = pd.DataFrame(
        {
            "frequency": [1, 2, 3, 1, 2] * 2,
            "monetary_value": [10.0, 20.0, 30.0, 15.0, 25.0] * 2,
        }
    )
    with patch("src.clv_model.GammaGammaFitter") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        out = fit_gamma_gamma(rfm, penalizer=0.01)
    assert out is instance
    assert instance.fit.called
    # Small sample (<50) should fit on all returning rows
    args, _kwargs = instance.fit.call_args
    assert len(args[0]) == 10


def test_predict_clv_one_time_buyers_branch():
    raw = generate_transactions(n_customers=80, seed=3)
    rfm = build_rfm_summary(clean_transactions(raw))
    _, bgnbd, ggf = run_clv_pipeline(rfm, months=6)

    one_timers = rfm[rfm["frequency"] == 0].copy()
    if one_timers.empty:
        one_timers = rfm.head(3).copy()
        one_timers["frequency"] = 0
        one_timers["monetary_value"] = 0.0

    out = predict_clv(one_timers, bgnbd, ggf, months=6)
    assert "clv" in out.columns
    assert out["clv"].notna().all()
