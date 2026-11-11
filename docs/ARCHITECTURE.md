# RetailIQ Architecture

```text
Browser: HTML + CSS + JavaScript
             |
             | HTTP / JSON
             v
         FastAPI app
          /   |   \
         /    |    \
   Data service | Knowledge service
       |        |        |
   Pandas +    |     PDF/TXT/MD
   NumPy       |     retrieval
       |
   scikit-learn
   - StandardScaler + KMeans (RFM)
   - Linear regression baseline (forecast)
   - Isolation Forest (invoice outliers)
       |
   UCI CSV or labelled synthetic demo data
```

The frontend requests dashboard modules independently. A failed chart endpoint no longer prevents successful KPI and chart modules from rendering. The interface displays a clear error notice for modules that fail.

## Data flow

1. `app.data.load_data()` loads the configured CSV if present and valid; otherwise it creates deterministic synthetic demo data.
2. The data service normalises dates and numeric fields, derives revenue and identifies returns/cancellations.
3. API routes call shared filtering and metric functions.
4. The browser renders KPI cards, charts, tables and model outputs from JSON responses.
5. CSV export uses the same market/date/product filters as the dashboard.
