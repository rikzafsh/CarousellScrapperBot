import argparse
from analisis import DataAnalyzer
from app import app as flask_app
from bot import CarousellTelegramBot
from config import Config, setup_logger
from db import DatabaseManager
from laporan import ReportGenerator
from scraper import CarousellScraper

logger = setup_logger("main")


def run_once(keyword: str) -> None:
    scraper = CarousellScraper()
    db = DatabaseManager()
    reporter = ReportGenerator()

    items = scraper.scrape(keyword=keyword)
    sync_res = db.save_listings(items, keyword=keyword)
    summary = DataAnalyzer.analyze(items)
    excel_file = reporter.export_excel(items, summary, keyword=keyword)

    logger.info(
        "Selesai: %d diproses (%d baru, %d turun harga). Laporan: %s",
        sync_res["total_processed"],
        len(sync_res["new"]),
        len(sync_res["price_drops"]),
        excel_file,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot Scraper Carousell Indonesia")
    parser.add_argument(
        "--mode",
        choices=["scrape", "bot", "web"],
        default="scrape",
        help="Mode eksekusi: scrape (sekali jalan), bot (Telegram), atau web (Dashboard Flask)",
    )
    parser.add_argument("--keyword", default=Config.DEFAULT_KEYWORD, help="Kata kunci pencarian")
    args = parser.parse_args()

    if args.mode == "scrape":
        run_once(args.keyword)
    elif args.mode == "bot":
        CarousellTelegramBot().run()
    elif args.mode == "web":
        flask_app.run(host="0.0.0.0", port=Config.FLASK_PORT)


if __name__ == "__main__":
    main()