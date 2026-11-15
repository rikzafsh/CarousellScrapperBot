from flask import Flask, jsonify, render_template_string, request
from analisis import DataAnalyzer
from config import Config
from db import DatabaseManager
from scraper import CarousellScraper

app = Flask(__name__)
db = DatabaseManager()
scraper = CarousellScraper()

DASHBOARD_HTML = """
<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Carousell Scraper Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }
    .cards { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .card { background: white; padding: 1rem 1.25rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1); min-width: 160px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; }
    th, td { padding: 0.75rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
    th { background: #1e293b; color: white; }
    a { color: #dc2626; text-decoration: none; font-weight: 600; }
  </style>
</head>
<body>
  <h1>📦 Hasil Scraping Carousell ({{ keyword }})</h1>
  <div class="cards">
    <div class="card"><div>Total Produk</div><strong>{{ summary.total_items }}</strong></div>
    <div class="card"><div>Rata-rata Harga</div><strong>Rp {{ "{:,}".format(summary.avg_price).replace(",", ".") }}</strong></div>
    <div class="card"><div>Termurah</div><strong>Rp {{ "{:,}".format(summary.min_price).replace(",", ".") }}</strong></div>
    <div class="card"><div>Termahal</div><strong>Rp {{ "{:,}".format(summary.max_price).replace(",", ".") }}</strong></div>
  </div>
  <table>
    <thead>
      <tr><th>Judul</th><th>Harga</th><th>Kondisi</th><th>Penjual</th><th>Waktu</th><th>Link</th></tr>
    </thead>
    <tbody>
      {% for item in items %}
      <tr>
        <td>{{ item.title }}</td>
        <td>Rp {{ "{:,}".format(item.price).replace(",", ".") }}</td>
        <td>{{ item.condition }}</td>
        <td>{{ item.seller }}</td>
        <td>{{ item.time_posted }}</td>
        <td><a href="{{ item.url }}" target="_blank">Buka</a></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""


@app.route("/")
def index():
    keyword = request.args.get("keyword", Config.DEFAULT_KEYWORD)
    items = db.get_listings(keyword=keyword, limit=100)
    summary = DataAnalyzer.analyze(items)
    return render_template_string(DASHBOARD_HTML, items=items, summary=summary, keyword=keyword)


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    payload = request.get_json(silent=True) or {}
    keyword = payload.get("keyword", Config.DEFAULT_KEYWORD)
    items = scraper.scrape(keyword=keyword)
    res = db.save_listings(items, keyword=keyword)
    return jsonify({"status": "ok", "keyword": keyword, **res})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.FLASK_PORT)