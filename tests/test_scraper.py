from scraper import CarousellScraper


def test_parse_price():
    assert CarousellScraper.parse_price("Rp 250.000") == 250000
    assert CarousellScraper.parse_price("Gratis") == 0


def test_extract_listing_id():
    url = "/p/botol-minum-corkcicle-16oz-1399887766/?t-id=xyz"
    assert CarousellScraper.extract_listing_id(url) == "1399887766"


def test_parse_html(sample_html):
    scraper = CarousellScraper()
    items = scraper.parse_html(sample_html, keyword="botol")
    assert len(items) == 2
    assert items[0]["listing_id"] == "1399887766"
    assert items[0]["price"] == 250000
    assert items[1]["condition"] == "Baru"