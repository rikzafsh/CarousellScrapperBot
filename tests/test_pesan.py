from pesan import MessageFormatter


def test_format_new_items_alert():
    new_items = [
        {
            "title": "Botol Tumbler",
            "price": 75000,
            "condition": "Baru",
            "time_posted": "2 menit lalu",
            "url": "https://id.carousell.com/p/botol-tumbler-999/",
        }
    ]
    msg = MessageFormatter.format_new_items_alert(new_items, [], "botol")
    assert "Botol Tumbler" in msg
    assert "Rp 75.000" in msg