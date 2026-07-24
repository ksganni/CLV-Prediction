# Customer Lifetime Value (CLV) Prediction

## Overview

This project estimates **Customer Lifetime Value (CLV)** for retail customers using historical transaction data. CLV is the expected future revenue a customer will generate. The implementation uses the probabilistic **BG/NBD** model for purchase frequency and the **Gamma-Gamma** model for average monetary value, then segments customers into actionable value groups for retention and marketing decisions.

**Primary dataset:** [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) (United Kingdom subset).

## Demo

Dashboard walkthrough:

[Customer Lifetime Value (CLV) Dashboard Demo](https://youtu.be/ixFJUB1APd0)

---

## Problem

Businesses often treat all customers similarly, even though:

- some customers buy frequently and spend heavily,
- some are valuable but becoming inactive,
- many customers purchase only once.

Without a systematic estimate of future value, retention spend and outreach are hard to prioritize.

---

## Solution

This repository provides an end-to-end analytical pipeline that:

1. Ingests and cleans retail transaction records.
2. Builds an RFM summary per customer (Recency, Frequency, Monetary, observation time `T`).
3. Fits **BG/NBD** to predict expected future purchases.
4. Fits **Gamma-Gamma** to predict expected average spend.
5. Computes a **12-month CLV** estimate for each customer.
6. Assigns customers to segments: **Champions**, **Loyal**, **Potential**, **At-Risk**, **Lost**.
7. Exports results to CSV and an HTML dashboard for exploration.

---

## Workflow

```text
Transactions (UCI Online Retail)
        │
        ▼
 Data cleaning + RFM feature table
        │
        ├──────────────► BG/NBD (purchase process)
        │
        └──────────────► Gamma-Gamma (spend process)
                        │
                        ▼
                   CLV prediction
                        │
                        ▼
              Customer segmentation
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
   CSV outputs                 HTML dashboard
```

---

## What the Models Do

| Component | Role |
|-----------|------|
| **RFM table** | Compresses each customer’s history into inputs required by probabilistic CLV models |
| **BG/NBD** | Estimates how many purchases a customer is expected to make in a future window |
| **Gamma-Gamma** | Estimates how much a customer is expected to spend per purchase (conditional on repeat buying) |
| **CLV** | Combines expected purchases and spend into a monetary value over a chosen horizon (default: 12 months) |
| **Segmentation** | Translates RFM + CLV into business labels for targeting and retention |

---

## Segment definitions

| Segment | Definition |
|---------|------------|
| **Champions** | High recent activity, high frequency, high spend / CLV |
| **Loyal** | Reliable repeat buyers with solid value |
| **Potential** | Moderate engagement; opportunity to grow |
| **At-Risk** | Previously active, now declining - retention priority |
| **Lost** | Low engagement / inactive customers |

---

## Repository Structure

```text
clv-prediction/
├── data/                         # Local datasets (downloaded/generated; not committed)
├── src/
│   ├── download_online_retail.py # Downloads and standardizes UCI Online Retail
│   ├── generate_data.py          # Synthetic transactions for offline/CI fallback
│   ├── data_source.py            # Selects Online Retail vs synthetic input
│   ├── data_prep.py              # Cleaning and RFM construction
│   ├── clv_model.py              # BG/NBD, Gamma-Gamma, and CLV prediction
│   ├── segmentation.py           # Rule-based segments and optional K-Means
│   ├── build_dashboard.py        # Builds the HTML results dashboard
│   └── app.py                    # Optional Streamlit entry (HTML dashboard preferred)
├── scripts/
│   └── run_pipeline.py           # End-to-end execution entry point
├── tests/                        # Unit tests (pytest, 100% coverage target)
├── outputs/                      # Generated CSVs and dashboard.html
├── .github/workflows/ci.yml      # Continuous integration
├── Dockerfile / docker-compose.yml
├── requirements.txt
└── README.md
```

### File responsibilities

| Path | Purpose |
|------|---------|
| `src/download_online_retail.py` | Fetch UCI Excel file; emit clean transaction CSV |
| `src/data_prep.py` | Validate schema, remove invalid rows, build RFM summary |
| `src/clv_model.py` | Model fitting and CLV scoring |
| `src/segmentation.py` | Segment assignment and segment-level aggregates |
| `src/build_dashboard.py` | Render interactive HTML report from pipeline outputs |
| `scripts/run_pipeline.py` | Orchestrate prep → model → segment → export |
| `tests/` | Automated verification of data, models, and utilities |

---

## Setup

### Requirements

- Python 3.11+
- Internet access (first-time Online Retail download)

### Installation

```bash
cd ~/Projects/clv-prediction
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the analysis

```bash
# 1) Download and prepare UCI Online Retail (UK)
python src/download_online_retail.py

# 2) Fit models, segment customers, write outputs/
python scripts/run_pipeline.py

# 3) Open the dashboard
python src/build_dashboard.py
```

### Verify

```bash
pytest
```

---

## Outputs

| File | Description |
|------|-------------|
| `outputs/customer_clv.csv` | Per-customer RFM features, predictions, CLV, and segment |
| `outputs/segment_summary.csv` | Aggregate metrics by segment |
| `outputs/dashboard.html` | Interactive dashboard for inspection and filtering |

CSV outputs can also be imported into Power BI or Tableau if needed.

---

## Dataset Citation

Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository.  
https://doi.org/10.24432/C5BW33

---

## Visualization Method

Dashboard charts are produced through a post-processing visualization layer rather than static plotting during model training.

After CLV estimation and segmentation, `src/build_dashboard.py` loads the scored customer table, computes segment-level aggregates, and serializes the resulting summary statistics into `outputs/dashboard.html`. Client-side rendering is performed with [Chart.js](https://www.chartjs.org/), including value labels on each bar via the Chart.js datalabels plugin.

| Figure | Metric | Analytical interpretation |
|-------|--------|---------------------------|
| Customers by segment | Customer count per segment | Distribution of the portfolio across value groups |
| Total CLV by segment | Sum of predicted 12-month CLV per segment | Concentration of expected future revenue by segment |

Distinct colors are assigned to Champions, Loyal, Potential, At-Risk, and Lost to support comparative interpretation across segments. Regenerating the dashboard after a pipeline run updates both figures from the latest model outputs:

```bash
python src/build_dashboard.py
```
