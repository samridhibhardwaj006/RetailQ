from pathlib import Path
import re
from pypdf import PdfReader

DOCS = [
("Dataset guide","The Online Retail dataset contains invoice-line transactions from a UK-based non-store retailer between December 2010 and December 2011. InvoiceNo beginning with C indicates a cancellation. Quantity may be negative for returns. UnitPrice is in pounds sterling. CustomerID can be missing."),
("Metric definitions","Gross sales in RetailIQ sum positive quantity multiplied by positive unit price for non-cancelled invoices. Average order value is gross sales divided by distinct valid invoices. Return rate is the share of source lines marked as returns or cancellations. Customer segmentation excludes missing customer IDs."),
("Customer strategy note","RFM means Recency, Frequency and Monetary value. Champions are customers with high monetary value in the current clustering. Loyal customers have relatively strong purchase frequency/value. Promising and Needs attention are heuristic cluster labels, not ground-truth customer categories."),
("Data limitations","The dataset is historical, anonymised and does not identify the retailer by name. It is not a current feed. Missing customer identifiers exist. Forecasts and anomaly flags are analytical baselines and should be reviewed by a human.")
]

def ingest(name, content):
    DOCS.append((name,content[:120000]))
    return {"name":name,"characters":len(content)}

def upload_content(filename, raw):
    suffix=Path(filename).suffix.lower()
    if suffix==".pdf":
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(raw); f.flush()
            reader=PdfReader(f.name)
            content="\n".join(p.extract_text() or "" for p in reader.pages)
    else:
        content=raw.decode("utf-8",errors="ignore")
    return ingest(filename,content)

def retrieve(query, limit=4):
    terms=set(re.findall(r"[a-z0-9]+",query.lower()))
    scored=[]
    for name,content in DOCS:
        words=set(re.findall(r"[a-z0-9]+",(name+" "+content).lower()))
        score=len(terms & words)
        if score: scored.append((score,name,content))
    scored.sort(reverse=True)
    return [{"document":n,"excerpt":c[:650]} for _,n,c in scored[:limit]]
