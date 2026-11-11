# RetailIQ — Open Retail Intelligence Platform

RetailIQ is a local retail analytics workspace built with **FastAPI, Pandas, NumPy, scikit-learn, HTML, CSS and JavaScript**. It analyses the public UCI Online Retail transaction dataset when available and otherwise starts with an explicitly labelled deterministic synthetic demo dataset.

## Features

- Executive KPIs: gross revenue, distinct orders, known customers, average order value, units and return-line rate.
- Consistent market, date and product-search filters across dashboard analytics.
- Monthly revenue trend, top markets and product rankings.
- Customer RFM segmentation using StandardScaler and K-means.
- A three-month linear trend baseline (not a production forecasting model).
- Invoice-level anomaly candidates using Isolation Forest (not fraud detection).
- Natural-language question routing for common retail questions.
- Knowledge desk with built-in dataset notes and PDF/TXT/Markdown uploads.
- Filtered CSV export, health endpoint, interactive API documentation and automated tests.

## Quick start (macOS)

Python 3.10–3.12 is recommended. Python 3.13 may work depending on the availability of compatible wheels for dependencies.

```bash
cd RetailIQ
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python scripts/download_data.py   # optional; requires internet
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs> and health is at <http://127.0.0.1:8000/api/health>.

The app is designed to run even when the UCI download is unavailable. In that case it uses a clearly labelled synthetic demo dataset. To retry the real dataset download later:

```bash
pip install -r requirements-data.txt
python scripts/download_data.py
```

Restart Uvicorn after downloading so the data module reloads the CSV.

## Data provenance and attribution

Chen, D. (2015). **Online Retail** [Dataset]. UCI Machine Learning Repository. <https://doi.org/10.24432/C5BW33>

- UCI dataset page: <https://archive.ics.uci.edu/dataset/352/online+retail>
- Licence: Creative Commons Attribution 4.0 International (CC BY 4.0).
- 541,909 invoice-line records, covering 1 December 2010 to 9 December 2011.
- The dataset is historical and anonymised. It is not a live company feed, and the retailer's name is not disclosed.
- Preserve this attribution when redistributing the dataset.

## Metric definitions and limitations

- Gross revenue is the sum of positive quantity × positive unit price for non-cancelled invoice lines.
- Invoice numbers beginning with `C` and/or negative quantities are treated as return/cancellation lines and excluded from gross sales.
- Average order value is gross sales divided by distinct valid invoices.
- Return-line rate is return/cancellation source lines divided by all filtered source lines.
- Missing customer IDs are excluded from customer segmentation but not from transaction-level sales.
- RFM means Recency, Frequency and Monetary value. K-means cluster labels are heuristic interpretations, not ground-truth customer categories.
- Forecast values are a simple linear monthly trend baseline, not a production-grade forecast.
- Isolation Forest flags unusual invoice profiles for human review; flags are not evidence of fraud.
- Synthetic data is for demonstration only and is explicitly labelled in the UI and API.

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service and dataset status |
| GET | `/api/filters` | Available countries and date range |
| GET | `/api/overview` | KPI summary |
| GET | `/api/trends` | Monthly revenue and orders |
| GET | `/api/products` | Top products |
| GET | `/api/countries` | Market ranking |
| GET | `/api/segments` | RFM customer segments |
| GET | `/api/forecast` | Linear trend baseline |
| GET | `/api/anomalies` | Unusual invoice candidates |
| GET | `/api/export.csv` | Filtered sales CSV |
| POST | `/api/ask` | Natural-language analytics routing |
| GET/POST | `/api/documents` | List or upload knowledge documents |

Dashboard filters (`country`, `start`, `end`, `search`) are applied consistently to the relevant analytics and export endpoints.

## Tests

```bash
python -m pytest -q
```

## GitHub publishing

```bash
git init
git add .
git commit -m "Build RetailIQ retail intelligence platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/RetailIQ.git
git push -u origin main
```

Do not commit `.env`, credentials, or private customer data.
