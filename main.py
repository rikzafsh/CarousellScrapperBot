import argparse
import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from analisis import DataAnalyzer
from app import app as flask_app
from bot import CarousellTelegramBot
from config import Config, setup_logger
from db import DatabaseManager
from laporan import ReportGenerator
from pesan import MessageFormatter
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


async def run_notify(keyword: str) -> None:
    scraper = CarousellScraper()
    db = DatabaseManager()

    items = scraper.scrape(keyword=keyword)
    sync_res = db.save_listings(items, keyword=keyword)

    if sync_res["new"] or sync_res["price_drops"]:
        msg = MessageFormatter.format_new_items_alert(
            sync_res["new"], sync_res["price_drops"], keyword
        )
    else:
        msg = (
            f"🌅 *Laporan Harian 07:00 WIB (`{keyword}`)*\n"
            f"Berhasil memindai *{len(items)}* produk. Tidak ada produk baru hari ini."
        )

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=Config.TELEGRAM_CHAT_ID,
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )
    logger.info("Notifikasi Telegram terkirim.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bot Scraper Carousell Indonesia")
    parser.add_argument(
        "--mode",
        choices=["scrape", "notify", "bot", "web"],
        default="bot",
        help="Mode: scrape (lokal), notify (scrape + kirim Telegram 1x), bot (interaktif 24/7), web (Flask)",
    )
    parser.add_argument("--keyword", default=Config.DEFAULT_KEYWORD, help="Kata kunci pencarian")
    args = parser.parse_args()

    if args.mode == "scrape":
        run_once(args.keyword)
    elif args.mode == "notify":
        asyncio.run(run_notify(args.keyword))
    elif args.mode == "bot":
        CarousellTelegramBot().run()
    elif args.mode == "web":
        flask_app.run(host="0.0.0.0", port=Config.FLASK_PORT)


if __name__ == "__main__":
    main()