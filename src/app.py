"""
app.py
------
Streamlit can crash on some Mac + Python 3.13 setups (especially when
changing filters). This page just points you to the stable HTML dashboard.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD = PROJECT_ROOT / "outputs" / "dashboard.html"


def main() -> None:
    st.set_page_config(page_title="CLV Dashboard", layout="centered")
    st.title("Use the HTML dashboard")
    st.write(
        "Streamlit is unstable on this machine (it can crash when you change filters). "
        "Use the HTML dashboard instead - filters work there without crashing."
    )

    if st.button("Build & open HTML dashboard"):
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "build_dashboard.py")],
            check=False,
        )
        st.success(f"Opened: {DASHBOARD}")

    st.code("python src/build_dashboard.py", language="bash")
    if DASHBOARD.exists():
        st.info(f"Dashboard file already exists at:\n{DASHBOARD}")


if __name__ == "__main__":  # pragma: no cover
    main()
