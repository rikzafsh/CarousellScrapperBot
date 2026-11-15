from analisis import DataAnalyzer


def test_analyze_prices():
    items = [
        {"title": "A", "price": 100000, "condition": "Baru", "url": "http://a"},
        {"title": "B", "price": 200000, "condition": "Baru", "url": "http://b"},
        {"title": "C", "price": 300000, "condition": "Seperti baru", "url": "http://c"},
    ]
    result = DataAnalyzer.analyze(items)
    assert result["total_items"] == 3
    assert result["avg_price"] == 200000
    assert result["min_price"] == 100000
    assert result["max_price"] == 300000