"""
build_dashboard.py
------------------
Builds a simple HTML dashboard from outputs/customer_clv.csv.
Filters work in the browser (no Streamlit), so they will not crash.
"""

from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.segmentation import SEGMENT_ORDER, segment_summary

OUTPUT_CSV = PROJECT_ROOT / "outputs" / "customer_clv.csv"
DASHBOARD_HTML = PROJECT_ROOT / "outputs" / "dashboard.html"


def build_dashboard(open_browser: bool = False) -> Path:
    if not OUTPUT_CSV.exists():
        raise FileNotFoundError(
            f"Missing {OUTPUT_CSV}. Run this first:\n  python scripts/run_pipeline.py"
        )

    df = pd.read_csv(OUTPUT_CSV)
    summary = segment_summary(df)
    summary["segment"] = pd.Categorical(summary["segment"], categories=SEGMENT_ORDER, ordered=True)
    summary = summary.sort_values("segment")

    customers = (
        df.sort_values("clv", ascending=False)[
            [
                "customer_id",
                "frequency",
                "recency",
                "monetary_value",
                "predicted_purchases",
                "predicted_avg_spend",
                "clv",
                "segment",
            ]
        ]
        .round(2)
        .astype(object)
        .to_dict(orient="records")
    )

    payload = {
        "segment_order": SEGMENT_ORDER,
        "kpis": {
            "customers": int(len(df)),
            "total_clv": float(df["clv"].sum()),
            "avg_clv": float(df["clv"].mean()),
            "champions": int((df["segment"] == "Champions").sum()),
        },
        "segments": summary["segment"].astype(str).tolist(),
        "segment_customers": summary["customers"].astype(int).tolist(),
        "segment_clv": summary["total_clv"].astype(float).tolist(),
        "summary_rows": summary.round(2).astype(object).to_dict(orient="records"),
        "customers": customers,
    }

    html = _render_html(payload)
    DASHBOARD_HTML.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_HTML.write_text(html, encoding="utf-8")
    print(f"Dashboard ready -> {DASHBOARD_HTML}")

    if open_browser:
        webbrowser.open(DASHBOARD_HTML.resolve().as_uri())
        print("Opened in your browser.")

    return DASHBOARD_HTML


def _render_html(payload: dict) -> str:
    data_json = json.dumps(payload)
    k = payload["kpis"]

    filter_boxes = "".join(
        f'<label class="chip"><input type="checkbox" class="seg-filter" value="{seg}" checked /> {seg}</label>'
        for seg in payload["segment_order"]
    )

    summary_rows = "".join(
        "<tr>"
        f"<td>{r['segment']}</td>"
        f"<td>{int(r['customers']):,}</td>"
        f"<td>${float(r['avg_clv']):,.2f}</td>"
        f"<td>${float(r['total_clv']):,.2f}</td>"
        f"<td>{float(r['avg_frequency']):.2f}</td>"
        f"<td>${float(r['avg_spend']):,.2f}</td>"
        "</tr>"
        for r in payload["summary_rows"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CLV Prediction Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;650;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
  <style>
    :root {{
      --ink: #1a2f24;
      --muted: #4a6356;
      --accent: #0b6e4f;
      --accent-2: #2f6f5e;
      --card: #d7e2d6;
      --panel: #c8d6c6;
      --line: rgba(26, 47, 36, 0.16);
      --chip: #b9cbb7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: "Source Sans 3", "Segoe UI", sans-serif;
      color: var(--ink);
      background-color: #9fb5a3;
      background-image:
        radial-gradient(ellipse 1000px 560px at 10% -8%, rgba(11, 110, 79, 0.28), transparent 58%),
        radial-gradient(ellipse 900px 520px at 95% 5%, rgba(47, 111, 94, 0.2), transparent 55%),
        linear-gradient(165deg, #a7bdaa 0%, #b4c6b5 48%, #9eb3a2 100%),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180' viewBox='0 0 180 180'%3E%3Cg fill='none' stroke='%231a2f24' stroke-opacity='0.07' stroke-width='1.2'%3E%3Cpath d='M20 140 V70 M40 140 V95 M60 140 V50 M80 140 V110 M100 140 V65 M120 140 V85 M140 140 V45'/%3E%3Ccircle cx='40' cy='40' r='3' fill='%231a2f24' fill-opacity='0.08'/%3E%3Ccircle cx='90' cy='28' r='3' fill='%231a2f24' fill-opacity='0.08'/%3E%3Ccircle cx='140' cy='48' r='3' fill='%231a2f24' fill-opacity='0.08'/%3E%3Cpath d='M40 40 L90 28 L140 48'/%3E%3C/g%3E%3C/svg%3E");
      background-attachment: fixed;
    }}
    .wrap {{
      position: relative;
      z-index: 1;
      width: min(1480px, calc(100% - 28px));
      margin: 0 auto;
      padding: 18px 0 36px;
    }}
    .hero {{
      margin-bottom: 18px;
      padding: 22px 22px 18px;
      border-radius: 18px;
      border: 1px solid rgba(184, 212, 196, 0.35);
      background:
        linear-gradient(135deg, #0b6e4f 0%, #164a3a 55%, #1a2f24 100%);
      color: #e8f4ef;
      box-shadow: 0 18px 40px rgba(26, 47, 36, 0.22);
      overflow: hidden;
      position: relative;
    }}
    .hero::before {{
      content: "";
      position: absolute;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='220' height='120' viewBox='0 0 220 120'%3E%3Cg fill='none' stroke='%23bfe3d4' stroke-opacity='0.28' stroke-width='1.5'%3E%3Cpath d='M10 100 V55 M30 100 V70 M50 100 V40 M70 100 V78 M90 100 V48 M110 100 V62 M130 100 V35 M150 100 V58 M170 100 V45 M190 100 V72'/%3E%3Cpath d='M20 30 C50 10, 80 50, 110 28 C140 8, 170 40, 200 22'/%3E%3C/g%3E%3C/svg%3E");
      background-size: 240px 130px;
      opacity: 0.9;
      pointer-events: none;
    }}
    .hero > * {{ position: relative; z-index: 1; }}
    h1 {{
      margin: 0 0 8px;
      font-family: Sora, sans-serif;
      font-size: clamp(1.45rem, 3vw, 1.95rem);
      font-weight: 650;
      letter-spacing: -0.02em;
    }}
    .sub {{
      margin: 0;
      color: #c5ddd2;
      font-size: 0.98rem;
    }}
    .tag-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }}
    .tag {{
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      padding: 5px 10px;
      border-radius: 999px;
      background: rgba(163, 201, 184, 0.22);
      border: 1px solid rgba(163, 201, 184, 0.4);
      color: #d7ebe3;
    }}
    .kpis {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }}
    .card, .about {{
      background: var(--card);
      backdrop-filter: none;
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 10px 28px rgba(26, 47, 36, 0.12);
    }}
    .flow {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.82rem;
      background: var(--panel);
      border: 1px dashed rgba(11, 110, 79, 0.35);
      border-radius: 10px;
      padding: 12px;
      overflow-x: auto;
      white-space: pre;
      color: #1a2f24;
      margin: 8px 0 14px;
    }}
    .label {{ font-size: 0.8rem; color: var(--muted); font-weight: 600; }}
    .value {{
      font-family: Sora, sans-serif;
      font-size: 1.35rem;
      font-weight: 700;
      margin-top: 6px;
      color: var(--accent);
    }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 18px; }}
    .filters {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 14px; }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 12px;
      background: var(--chip);
      cursor: pointer;
      user-select: none;
    }}
    .about {{ padding: 18px 18px 8px; margin-bottom: 18px; }}
    .about h2 {{
      margin: 0 0 10px;
      font-family: Sora, sans-serif;
      font-size: 1.15rem;
    }}
    .about h3 {{
      margin: 14px 0 6px;
      font-family: Sora, sans-serif;
      font-size: 0.98rem;
    }}
    .about p, .about li {{ color: #243b32; line-height: 1.55; font-size: 0.95rem; }}
    .about ul {{ margin: 0 0 12px; padding-left: 18px; }}
    .seg-def {{ display: grid; grid-template-columns: 140px 1fr; gap: 6px 12px; margin: 8px 0 12px; font-size: 0.92rem; }}
    .seg-def strong {{ color: var(--accent); }}
    .hint {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; background: transparent; }}
    th, td {{ padding: 10px 8px; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ color: var(--muted); font-weight: 700; background: var(--panel); }}
    tbody tr:nth-child(even) {{ background: rgba(26, 47, 36, 0.06); }}
    tbody tr:nth-child(odd) {{ background: rgba(26, 47, 36, 0.02); }}
    .scroll {{
      max-height: 420px;
      overflow: auto;
      background: var(--panel);
      border-radius: 10px;
      border: 1px solid var(--line);
    }}
    canvas {{
      width: 100% !important;
      max-height: 280px;
      background: var(--panel) !important;
      border-radius: 10px;
    }}
    @media (max-width: 800px) {{
      .kpis, .grid {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 520px) {{
      .kpis, .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <h1>Customer Lifetime Value (CLV) Dashboard</h1>
      <p class="sub">UCI Online Retail (UK) · predict future customer value · guide retention strategy</p>
      <div class="tag-row">
        <span class="tag">RFM features</span>
        <span class="tag">BG/NBD</span>
        <span class="tag">Gamma-Gamma</span>
        <span class="tag">Value segments</span>
      </div>
    </header>

    <section class="about">
      <h2>What this project does</h2>
      <p>
        This dashboard summarizes an end-to-end customer analytics pipeline that estimates
        <strong>Customer Lifetime Value (CLV)</strong> - the expected future revenue from each customer -
        and groups customers into retention-focused segments.
      </p>

      <h3>Problem</h3>
      <p>
        Retail businesses cannot efficiently allocate retention effort if every customer is treated equally.
        Historical purchases exist, but future value is unknown without a formal prediction method.
      </p>

      <h3>Solution</h3>
      <p>
        Transaction histories are converted into RFM features. The <strong>BG/NBD</strong> model predicts
        future purchase counts; the <strong>Gamma-Gamma</strong> model predicts average spend. Combined, they
        yield a 12-month CLV score. Customers are then labeled for targeting.
      </p>

      <h3>Workflow</h3>
      <div class="flow">Transactions → RFM table → BG/NBD + Gamma-Gamma → CLV → Segments → Dashboard</div>

      <h3>Segment definitions</h3>
      <div class="seg-def">
        <strong>Champions</strong><span>High recent activity, high frequency, high spend / CLV</span>
        <strong>Loyal</strong><span>Reliable repeat buyers with solid value</span>
        <strong>Potential</strong><span>Moderate engagement; opportunity to grow</span>
        <strong>At-Risk</strong><span>Previously active, now declining - retention priority</span>
        <strong>Lost</strong><span>Low engagement / inactive customers</span>
      </div>

      <h3>How to read this page</h3>
      <ul>
        <li><strong>KPI cards</strong> - portfolio size and predicted value at a glance</li>
        <li><strong>Charts</strong> - customer count and total CLV by segment</li>
        <li><strong>Segment table</strong> - average behavior within each group</li>
        <li><strong>Customer explorer</strong> - filter by segment and inspect individual CLV scores</li>
      </ul>
    </section>

    <div class="kpis">
      <div class="card"><div class="label">Customers</div><div class="value" id="kpiCustomers">{k['customers']:,}</div></div>
      <div class="card"><div class="label">Total predicted CLV</div><div class="value" id="kpiTotal">${k['total_clv']:,.0f}</div></div>
      <div class="card"><div class="label">Average CLV</div><div class="value" id="kpiAvg">${k['avg_clv']:,.0f}</div></div>
      <div class="card"><div class="label">Champions</div><div class="value" id="kpiChampions">{k['champions']:,}</div></div>
    </div>

    <div class="grid">
      <div class="card">
        <canvas id="customersChart"></canvas>
        <p class="hint" style="margin-top:10px;">
          <strong>What this means:</strong> how many customers fall into each value group.
          A taller bar means more customers in that segment.
        </p>
      </div>
      <div class="card">
        <canvas id="clvChart"></canvas>
        <p class="hint" style="margin-top:10px;">
          <strong>What this means:</strong> total predicted future revenue from each segment.
          Champions may be fewer people but often contribute the most total CLV.
        </p>
      </div>
    </div>

    <div class="card" style="margin-bottom:18px;">
      <h3 style="margin-top:0;">Segment summary</h3>
      <table>
        <thead>
          <tr>
            <th>Segment</th><th>Customers</th><th>Avg CLV</th>
            <th>Total CLV</th><th>Avg frequency</th><th>Avg spend</th>
          </tr>
        </thead>
        <tbody>{summary_rows}</tbody>
      </table>
    </div>

    <div class="card">
      <h3 style="margin-top:0;">Explore customers</h3>
      <p class="hint">Use segment filters to focus the table. Clearing filters only hides rows; it does not re-run models.</p>
      <div class="filters">{filter_boxes}</div>
      <div class="hint" id="resultCount"></div>
      <div class="scroll">
        <table>
          <thead>
            <tr>
              <th>Customer</th><th>Segment</th><th>CLV</th>
              <th>Pred. purchases</th><th>Pred. spend</th><th>Frequency</th>
            </tr>
          </thead>
          <tbody id="customerBody"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    const data = {data_json};
    const money = (n) => '$' + Number(n).toLocaleString(undefined, {{ maximumFractionDigits: 2 }});
    Chart.register(ChartDataLabels);
    const chartBgPlugin = {{
      id: 'chartAreaBg',
      beforeDraw(chart) {{
        const {{ ctx, width, height }} = chart;
        ctx.save();
        ctx.globalCompositeOperation = 'destination-over';
        ctx.fillStyle = '#c8d6c6';
        ctx.fillRect(0, 0, width, height);
        ctx.restore();
      }}
    }};

    const segmentColors = ['#0b6e4f', '#2f6f5e', '#c4a35a', '#c4733a', '#6b7280'];

    const customersChart = new Chart(document.getElementById('customersChart'), {{
      type: 'bar',
      plugins: [chartBgPlugin],
      data: {{
        labels: data.segments,
        datasets: [{{
          label: 'Customers',
          data: data.segment_customers,
          backgroundColor: segmentColors,
          borderSkipped: false
        }}]
      }},
      options: {{
        layout: {{ padding: {{ top: 24 }} }},
        plugins: {{
          title: {{ display: true, text: 'Customers by segment' }},
          datalabels: {{
            anchor: 'end',
            align: 'top',
            clamp: true,
            color: '#334155',
            font: {{ weight: '600', size: 11 }},
            formatter: (value) => Number(value).toLocaleString()
          }}
        }},
        scales: {{ y: {{ beginAtZero: true, grace: '10%' }} }}
      }}
    }});

    const clvChart = new Chart(document.getElementById('clvChart'), {{
      type: 'bar',
      plugins: [chartBgPlugin],
      data: {{
        labels: data.segments,
        datasets: [{{
          label: 'Total CLV',
          data: data.segment_clv,
          backgroundColor: segmentColors,
          borderSkipped: false
        }}]
      }},
      options: {{
        layout: {{ padding: {{ top: 24 }} }},
        plugins: {{
          title: {{ display: true, text: 'Total CLV by segment ($)' }},
          datalabels: {{
            anchor: 'end',
            align: 'top',
            clamp: true,
            color: '#334155',
            font: {{ weight: '600', size: 11 }},
            formatter: (value) => '$' + Number(value).toLocaleString(undefined, {{ maximumFractionDigits: 0 }})
          }}
        }},
        scales: {{ y: {{ beginAtZero: true, grace: '10%' }} }}
      }}
    }});

    function selectedSegments() {{
      return Array.from(document.querySelectorAll('.seg-filter:checked')).map((el) => el.value);
    }}

    function renderCustomers() {{
      const selected = selectedSegments();
      const body = document.getElementById('customerBody');
      const count = document.getElementById('resultCount');

      if (selected.length === 0) {{
        body.innerHTML = '<tr><td colspan="6">No segments selected. Turn at least one filter back on.</td></tr>';
        count.textContent = 'Showing 0 customers';
        return;
      }}

      const rows = data.customers.filter((r) => selected.includes(r.segment)).slice(0, 200);
      count.textContent = 'Showing ' + rows.length + ' customers (max 200) for selected segments';
      body.innerHTML = rows.map((r) => (
        '<tr>' +
        '<td>' + r.customer_id + '</td>' +
        '<td>' + r.segment + '</td>' +
        '<td>' + money(r.clv) + '</td>' +
        '<td>' + Number(r.predicted_purchases).toFixed(2) + '</td>' +
        '<td>' + money(r.predicted_avg_spend) + '</td>' +
        '<td>' + Number(r.frequency).toFixed(0) + '</td>' +
        '</tr>'
      )).join('');
    }}

    document.querySelectorAll('.seg-filter').forEach((el) => {{
      el.addEventListener('change', renderCustomers);
    }});
    renderCustomers();
  </script>
</body>
</html>
"""


def main() -> None:
    build_dashboard(open_browser=True)


if __name__ == "__main__":  # pragma: no cover
    main()
