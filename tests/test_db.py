def test_save_and_price_drop(temp_db):
    item_v1 = [
        {
            "listing_id": "1001",
            "keyword": "botol",
            "title": "Botol Hydro Flask",
            "price": 300000,
            "condition": "Baru",
            "seller": "user1",
            "time_posted": "1 jam lalu",
            "url": "https://id.carousell.com/p/botol-1001/",
        }
    ]
    res1 = temp_db.save_listings(item_v1, keyword="botol")
    assert len(res1["new"]) == 1
    assert len(res1["price_drops"]) == 0

    item_v2 = [{**item_v1[0], "price": 220000}]
    res2 = temp_db.save_listings(item_v2, keyword="botol")
    assert len(res2["new"]) == 0
    assert len(res2["price_drops"]) == 1
    assert res2["price_drops"][0]["old_price"] == 300000