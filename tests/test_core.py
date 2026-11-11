from app import data

def test_dataset_has_rows():
    assert len(data.DATA) > 100

def test_overview_has_expected_metrics():
    result=data.overview(data.DATA)
    assert result["revenue"] >= 0
    assert result["orders"] >= 0
    assert "source" in result

def test_returns_are_separated():
    d=data.DATA
    s=data.sales_frame(d)
    assert not s["IsReturn"].any()
    assert (s["Quantity"] > 0).all()

def test_trend_structure():
    rows=data.trends(data.DATA)
    assert isinstance(rows,list)
    if rows:
        assert "month" in rows[0] and "revenue" in rows[0]

def test_knowledge_retrieval():
    from app.knowledge import retrieve
    assert retrieve("dataset cancellation") 
