from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from io import StringIO
import pandas as pd
from . import data, knowledge

ROOT=Path(__file__).resolve().parent
app=FastAPI(title="RetailIQ API",version="1.0.0",description="Open-data retail analytics and customer intelligence")
app.mount("/static",StaticFiles(directory=ROOT/"static"),name="static")

def frame(country="All",start=None,end=None,search=None):
    return data.filtered(country,start,end,search)

@app.get("/",response_class=HTMLResponse)
def home(): return (ROOT/"static"/"index.html").read_text()

@app.get("/api/health")
def health(): return {"status":"ok","dataset":data.DATA_SOURCE,"rows":len(data.DATA)}

@app.get("/api/filters")
def filters():
    d=data.DATA
    return {"countries":sorted(d.Country.dropna().astype(str).unique().tolist()),"start":str(d.InvoiceDate.min().date()),"end":str(d.InvoiceDate.max().date()),"source":data.DATA_SOURCE}

@app.get("/api/overview")
def get_overview(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None):
    return data.overview(frame(country,start,end,search))

@app.get("/api/trends")
def get_trends(country:str="All",start:str|None=None,end:str|None=None):
    return data.trends(frame(country,start,end))

@app.get("/api/products")
def get_products(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None,limit:int=10):
    return data.products(frame(country,start,end,search),limit)

@app.get("/api/countries")
def get_countries(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None,limit:int=10):
    return data.countries(frame(country,start,end,search),limit)

@app.get("/api/segments")
def get_segments(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None):
    return data.rfm_segments(frame(country,start,end,search))

@app.get("/api/forecast")
def get_forecast(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None):
    return data.forecast(frame(country,start,end,search))

@app.get("/api/anomalies")
def get_anomalies(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None):
    return data.anomalies(frame(country,start,end,search))

@app.get("/api/documents")
def get_documents():
    return [{"name":n,"characters":len(c)} for n,c in knowledge.DOCS]

@app.post("/api/documents")
async def add_document(file:UploadFile=File(...)):
    if not file.filename.lower().endswith((".txt",".md",".pdf")):
        return JSONResponse({"error":"Upload PDF, TXT or MD only."},status_code=400)
    result=knowledge.upload_content(file.filename,await file.read())
    return {"status":"indexed","document":result}

@app.post("/api/ask")
def ask(payload:dict):
    q=str(payload.get("question","")).strip()
    if not q:return JSONResponse({"error":"Enter a question."},status_code=400)
    low=q.lower()
    d=data.DATA
    sources=[]
    if any(w in low for w in ["country","region","geograph","market"]):
        rows=data.countries(d,5)
        answer=f"Top market by gross sales is {rows[0]['country']} (£{rows[0]['revenue']:,.2f}) based on the selected dataset." if rows else "No sales rows found."
        evidence=rows[:5]; route="country_performance"
    elif any(w in low for w in ["product","best seller","bestseller","top item"]):
        rows=data.products(d,5)
        answer=f"Top product by gross sales is {rows[0]['product']} (£{rows[0]['revenue']:,.2f})." if rows else "No product rows found."
        evidence=rows; route="product_performance"
    elif any(w in low for w in ["customer","segment","rfm","loyal"]):
        r=data.rfm_segments(d)
        answer="Customer segmentation uses Recency, Frequency and Monetary value with K-means. Segment totals are shown in the evidence."
        evidence=r["segments"]; route="customer_segmentation"
    elif any(w in low for w in ["return","cancel"]):
        ov=data.overview(d)
        answer=f"There are {ov['return_lines']:,} return/cancellation lines, representing {ov['return_rate']}% of all source lines."
        evidence=[{"return_lines":ov["return_lines"],"return_rate_percent":ov["return_rate"]}]; route="returns_analysis"
    elif any(w in low for w in ["forecast","next month","future","trend"]):
        evidence=data.forecast(d)["baseline"]
        answer="This is a simple linear monthly-revenue trend baseline. The last three rows are projected months; treat them as directional, not guaranteed."
        route="trend_baseline"
    elif any(w in low for w in ["anomal","unusual","outlier"]):
        evidence=data.anomalies(d)
        answer=f"Found {len(evidence)} unusual invoice profiles for review. An anomaly is not proof of fraud."
        route="anomaly_detection"
    else:
        evidence=knowledge.retrieve(q)
        answer="I searched the built-in dataset guide and uploaded documents. Review the cited excerpts below; ask about revenue, products, countries, customer segments, returns, forecasts or anomalies for live analytics."
        route="knowledge_retrieval"
    return {"answer":answer,"route":route,"evidence":evidence,"retrieved_documents":knowledge.retrieve(q),"mode":"offline explainable analytics"}

@app.get("/api/export.csv")
def export(country:str="All",start:str|None=None,end:str|None=None,search:str|None=None):
    d=data.sales_frame(frame(country,start,end,search))
    buf=StringIO(); d.to_csv(buf,index=False); buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=retailiq_filtered_sales.csv"})
