from pathlib import Path
import os
import numpy as np
import pandas as pd
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path(os.getenv("DATA_PATH", ROOT / "data" / "online_retail.csv"))

def make_demo_data(n=9000):
    # Deterministic synthetic fallback. It is visibly labelled as demo data.
    rng = np.random.default_rng(42)
    dates = pd.to_datetime("2010-12-01") + pd.to_timedelta(rng.integers(0, 374, n), unit="D")
    countries = np.array(["United Kingdom","Germany","France","EIRE","Spain","Netherlands","Belgium","Switzerland"])
    products = np.array(["CERAMIC MUG","GIFT BOX","LED LANTERN","COTTON TOTE BAG","WOODEN FRAME","PARTY BUNTING","TEA LIGHT SET","NOTEBOOK"])
    qty = rng.integers(1, 15, n)
    # Include a small, deterministic share of return lines so the demo can
    # exercise the returns KPI without pretending these are real transactions.
    return_mask = rng.random(n) < 0.018
    qty[return_mask] *= -1
    price = np.round(rng.lognormal(1.0, 0.65, n), 2)
    cust = rng.integers(12000, 16500, n).astype(float)
    frame = pd.DataFrame({
        "InvoiceNo": [str(570000+i//3) for i in range(n)],
        "StockCode": rng.choice(["10001","10002","10003","10004","10005","10006"], n),
        "Description": rng.choice(products, n),
        "Quantity": qty,
        "InvoiceDate": dates,
        "UnitPrice": price,
        "CustomerID": cust,
        "Country": rng.choice(countries, n, p=[.68,.08,.07,.06,.04,.03,.02,.02])
    })
    return frame

def load_data():
    if DATA_PATH.exists():
        try:
            df = pd.read_csv(DATA_PATH)
            source = "UCI Online Retail · CC BY 4.0"
        except Exception:
            df, source = make_demo_data(), "Synthetic demo dataset"
    else:
        df, source = make_demo_data(), "Synthetic demo dataset · UCI download not yet installed"
    required = ["InvoiceNo","StockCode","Description","Quantity","InvoiceDate","UnitPrice","CustomerID","Country"]
    for c in required:
        if c not in df.columns:
            df, source = make_demo_data(), "Synthetic demo dataset · invalid source schema"
            break
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0)
    df["Revenue"] = df["Quantity"] * df["UnitPrice"]
    df["IsReturn"] = df["InvoiceNo"].astype(str).str.upper().str.startswith("C") | (df["Quantity"] < 0)
    return df.dropna(subset=["InvoiceDate"]), source

DATA, DATA_SOURCE = load_data()

def filtered(country="All", start=None, end=None, search=None):
    d = DATA.copy()
    if country and country != "All":
        d = d[d.Country == country]
    if start:
        d = d[d.InvoiceDate >= pd.to_datetime(start)]
    if end:
        d = d[d.InvoiceDate < pd.to_datetime(end) + pd.Timedelta(days=1)]
    if search:
        d = d[d.Description.astype(str).str.contains(search, case=False, na=False)]
    return d

def sales_frame(d):
    return d[(~d.IsReturn) & (d.Quantity > 0) & (d.UnitPrice > 0)].copy()

def overview(d):
    s = sales_frame(d)
    inv = s.groupby("InvoiceNo")
    returns = d[d.IsReturn]
    return {
        "revenue": round(float(s.Revenue.sum()),2),
        "orders": int(s.InvoiceNo.nunique()),
        "customers": int(s.CustomerID.nunique()),
        "aov": round(float(inv.Revenue.sum().mean()),2) if len(inv) else 0,
        "units": int(s.Quantity.sum()),
        "return_lines": int(len(returns)),
        "return_rate": round(float(len(returns)/max(len(d),1)*100),2),
        "rows": int(len(d)),
        "source": DATA_SOURCE,
        "date_min": str(d.InvoiceDate.min().date()) if len(d) else None,
        "date_max": str(d.InvoiceDate.max().date()) if len(d) else None
    }

def trends(d):
    s=sales_frame(d)
    if s.empty: return []
    g=s.assign(Month=s.InvoiceDate.dt.to_period("M").astype(str)).groupby("Month").agg(revenue=("Revenue","sum"),orders=("InvoiceNo","nunique")).reset_index()
    return [{"month":r.Month,"revenue":round(float(r.revenue),2),"orders":int(r.orders)} for r in g.itertuples()]

def products(d, limit=10):
    s=sales_frame(d)
    g=s.groupby("Description").agg(revenue=("Revenue","sum"),units=("Quantity","sum"),orders=("InvoiceNo","nunique")).reset_index()
    g=g.sort_values("revenue",ascending=False).head(limit)
    return [{"product":str(r.Description),"revenue":round(float(r.revenue),2),"units":int(r.units),"orders":int(r.orders)} for r in g.itertuples()]

def countries(d, limit=10):
    s=sales_frame(d)
    g=s.groupby("Country").agg(revenue=("Revenue","sum"),orders=("InvoiceNo","nunique"),customers=("CustomerID","nunique")).reset_index().sort_values("revenue",ascending=False).head(limit)
    return [{"country":str(r.Country),"revenue":round(float(r.revenue),2),"orders":int(r.orders),"customers":int(r.customers)} for r in g.itertuples()]

def rfm_segments(d):
    s=sales_frame(d).dropna(subset=["CustomerID"])
    if s.empty: return {"segments":[],"customers":[]}
    snap=s.InvoiceDate.max()+pd.Timedelta(days=1)
    r=s.groupby("CustomerID").agg(last=("InvoiceDate","max"),frequency=("InvoiceNo","nunique"),monetary=("Revenue","sum")).reset_index()
    r["recency"]=(snap-r["last"]).dt.days
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    cols=["recency","frequency","monetary"]
    X=np.log1p(r[cols].clip(lower=0))
    X=StandardScaler().fit_transform(X)
    k=min(4,len(r))
    r["cluster"]=KMeans(n_clusters=k,random_state=42,n_init=10).fit_predict(X)
    rank=r.groupby("cluster").monetary.mean().sort_values(ascending=False)
    labels={cl:["Champions","Loyal customers","Promising","Needs attention"][i] for i,cl in enumerate(rank.index)}
    r["segment"]=r.cluster.map(labels)
    seg=r.groupby("segment").agg(customers=("CustomerID","count"),revenue=("monetary","sum"),avg_recency=("recency","mean")).reset_index()
    seg=seg.sort_values("revenue",ascending=False)
    top=r.sort_values("monetary",ascending=False).head(12)
    return {"segments":[{"segment":x.segment,"customers":int(x.customers),"revenue":round(float(x.revenue),2),"avg_recency":round(float(x.avg_recency),1)} for x in seg.itertuples()],
            "customers":[{"customer":str(int(x.CustomerID)),"segment":x.segment,"frequency":int(x.frequency),"monetary":round(float(x.monetary),2),"recency":int(x.recency)} for x in top.itertuples()]}

def forecast(d):
    t=trends(d)
    if len(t)<3: return {"baseline":[],"note":"Not enough monthly history for a trend baseline."}
    y=np.array([x["revenue"] for x in t],dtype=float)
    x=np.arange(len(y))
    slope,intercept=np.polyfit(x,y,1)
    out=[{"month":z["month"],"actual":z["revenue"],"baseline":round(float(max(0,intercept+slope*i)),2)} for i,z in enumerate(t)]
    last=pd.Period(t[-1]["month"],freq="M")
    for i in range(1,4):
        p=last+i
        out.append({"month":str(p),"actual":None,"baseline":round(float(max(0,intercept+slope*(len(y)+i-1))),2)})
    return {"baseline":out,"note":"Linear trend baseline, not a production forecast."}

def anomalies(d):
    s=sales_frame(d)
    if s.empty:return []
    inv=s.groupby("InvoiceNo").agg(total=("Revenue","sum"),units=("Quantity","sum"),lines=("StockCode","count")).reset_index()
    if len(inv)<20:return []
    from sklearn.ensemble import IsolationForest
    model=IsolationForest(contamination=.025,random_state=42)
    inv["flag"]=model.fit_predict(np.log1p(inv[["total","units","lines"]]))
    a=inv[inv.flag==-1].sort_values("total",ascending=False).head(12)
    return [{"invoice":str(x.InvoiceNo),"total":round(float(x.total),2),"units":int(x.units),"lines":int(x.lines),"reason":"Unusual invoice profile — review candidate"} for x in a.itertuples()]
