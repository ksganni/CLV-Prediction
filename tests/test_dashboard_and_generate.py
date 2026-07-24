"""Coverage for dashboard builder, generate_data, and Streamlit app helper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import src.app as app_module
import src.build_dashboard as bd
import src.generate_data as gd


def _fake_customer_csv(path: Path) -> None:
    pd.DataFrame(
        {
            "customer_id": ["1", "2", "3"],
            "frequency": [5, 2, 0],
            "recency": [100.0, 40.0, 0.0],
            "T": [200.0, 120.0, 50.0],
            "monetary_value": [50.0, 20.0, 0.0],
            "predicted_purchases": [3.0, 1.0, 0.2],
            "predicted_avg_spend": [45.0, 18.0, 10.0],
            "clv": [400.0, 80.0, 5.0],
            "segment": ["Champions", "Loyal", "Lost"],
        }
    ).to_csv(path, index=False)


def test_build_dashboard_writes_html(tmp_path: Path, monkeypatch):
    out_csv = tmp_path / "customer_clv.csv"
    html_path = tmp_path / "dashboard.html"
    _fake_customer_csv(out_csv)

    monkeypatch.setattr(bd, "OUTPUT_CSV", out_csv)
    monkeypatch.setattr(bd, "DASHBOARD_HTML", html_path)

    with patch("src.build_dashboard.webbrowser.open") as open_browser:
        path = bd.build_dashboard(open_browser=True)

    assert path == html_path
    assert html_path.exists()
    text = html_path.read_text(encoding="utf-8")
    assert "Customer Lifetime Value (CLV) Dashboard" in text
    assert "What this project does" in text
    assert "Champions" in text
    assert open_browser.called


def test_build_dashboard_missing_csv(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(bd, "OUTPUT_CSV", tmp_path / "missing.csv")
    with pytest.raises(FileNotFoundError, match="run_pipeline"):
        bd.build_dashboard(open_browser=False)


def test_build_dashboard_main(tmp_path: Path, monkeypatch):
    out_csv = tmp_path / "customer_clv.csv"
    html_path = tmp_path / "dashboard.html"
    _fake_customer_csv(out_csv)
    monkeypatch.setattr(bd, "OUTPUT_CSV", out_csv)
    monkeypatch.setattr(bd, "DASHBOARD_HTML", html_path)
    with patch("src.build_dashboard.webbrowser.open"):
        bd.main()
    assert html_path.exists()


def test_generate_data_main(tmp_path: Path):
    out = gd.main(project_root=tmp_path)
    assert out.exists()
    assert out.name == "sample_transactions.csv"
    assert len(pd.read_csv(out)) > 0


def test_app_main_button_clicked(tmp_path: Path, monkeypatch):
    dash = tmp_path / "dashboard.html"
    dash.write_text("<html></html>", encoding="utf-8")
    monkeypatch.setattr(app_module, "DASHBOARD", dash)

    fake_st = MagicMock()
    fake_st.button.return_value = True
    monkeypatch.setattr(app_module, "st", fake_st)

    with patch("src.app.subprocess.run") as run:
        app_module.main()

    assert fake_st.set_page_config.called
    assert fake_st.title.called
    assert run.called
    assert fake_st.success.called
    assert fake_st.info.called


def test_app_main_button_not_clicked(tmp_path: Path, monkeypatch):
    missing = tmp_path / "missing.html"
    monkeypatch.setattr(app_module, "DASHBOARD", missing)

    fake_st = MagicMock()
    fake_st.button.return_value = False
    monkeypatch.setattr(app_module, "st", fake_st)

    app_module.main()
    assert fake_st.code.called
    fake_st.success.assert_not_called()
    fake_st.info.assert_not_called()
