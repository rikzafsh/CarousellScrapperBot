from datetime import time, timedelta, timezone
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from analisis import DataAnalyzer
from config import Config, setup_logger
from db import DatabaseManager
from laporan import ReportGenerator
from pesan import MessageFormatter
from scraper import CarousellScraper

logger = setup_logger("telegram_bot")
WIB = timezone(timedelta(hours=7))


class CarousellTelegramBot:
    def __init__(self):
        self.scraper = CarousellScraper()
        self.db = DatabaseManager()
        self.reporter = ReportGenerator()

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = (
            "👋 *Bot Scraper & Pantau Harga Carousell Indonesia*\n\n"
            "Perintah tersedia:\n"
            "• `/scrape [keyword]` — Ambil data sekarang (default: `botol`)\n"
            "• `/analisis [keyword]` — Lihat statistik harga\n"
            "• `/laporan [keyword]` — Unduh file Excel (.xlsx)\n"
            "• `/id` — Cek Chat ID Telegram kamu\n\n"
            "⏰ *Jadwal Otomatis:* Aktif setiap hari pukul *07:00 WIB*."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    async def cmd_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            f"Chat ID kamu: `{update.effective_chat.id}`", parse_mode=ParseMode.MARKDOWN
        )

    async def cmd_scrape(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyword = " ".join(context.args).strip() or Config.DEFAULT_KEYWORD
        await update.message.reply_text(
            f"⏳ Mengambil data Carousell untuk `{keyword}`...", parse_mode=ParseMode.MARKDOWN
        )

        items = self.scraper.scrape(keyword=keyword)
        sync_result = self.db.save_listings(items, keyword=keyword)

        if sync_result["new"] or sync_result["price_drops"]:
            msg = MessageFormatter.format_new_items_alert(
                sync_result["new"], sync_result["price_drops"], keyword
            )
        else:
            msg = (
                f"✅ Selesai memindai *{len(items)}* produk untuk `{keyword}`.\n"
                "Belum ada produk baru atau penurunan harga sejak pengecekan terakhir."
            )

        await update.message.reply_text(
            msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

    async def cmd_analisis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyword = " ".join(context.args).strip() or Config.DEFAULT_KEYWORD
        items = self.db.get_listings(keyword=keyword, limit=200)
        summary = DataAnalyzer.analyze(items)
        msg = MessageFormatter.format_analysis(summary, keyword)
        await update.message.reply_text(
            msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

    async def cmd_laporan(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyword = " ".join(context.args).strip() or Config.DEFAULT_KEYWORD
        items = self.db.get_listings(keyword=keyword, limit=500)
        if not items:
            await update.message.reply_text(
                "Data kosong. Jalankan `/scrape` terlebih dahulu.", parse_mode=ParseMode.MARKDOWN
            )
            return

        summary = DataAnalyzer.analyze(items)
        excel_path = self.reporter.export_excel(items, summary, keyword=keyword)
        with open(excel_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=excel_path.name,
                caption=f"📑 Laporan Carousell `{keyword}` ({len(items)} produk)",
                parse_mode=ParseMode.MARKDOWN,
            )

    async def scheduled_monitor(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyword = Config.DEFAULT_KEYWORD
        logger.info("Menjalankan jadwal harian 07:00 WIB untuk '%s'", keyword)
        items = self.scraper.scrape(keyword=keyword)
        sync_result = self.db.save_listings(items, keyword=keyword)

        if not Config.TELEGRAM_CHAT_ID:
            logger.warning("TELEGRAM_CHAT_ID kosong, notifikasi dilewati.")
            return

        if sync_result["new"] or sync_result["price_drops"]:
            msg = MessageFormatter.format_new_items_alert(
                sync_result["new"], sync_result["price_drops"], keyword
            )
        else:
            msg = (
                f"🌅 *Laporan Harian 07:00 WIB (`{keyword}`)*\n"
                f"Berhasil memindai *{len(items)}* produk. Tidak ada listing baru sejak kemarin."
            )

        await context.bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    def run(self) -> None:
        if not Config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN belum diisi di file .env")

        app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_start))
        app.add_handler(CommandHandler("id", self.cmd_id))
        app.add_handler(CommandHandler("scrape", self.cmd_scrape))
        app.add_handler(CommandHandler("analisis", self.cmd_analisis))
        app.add_handler(CommandHandler("laporan", self.cmd_laporan))

        # Jadwalkan otomatis setiap jam 17:00 WIB
        jadwal_sore = time(hour=17, minute=0, tzinfo=WIB)
        app.job_queue.run_daily(
            self.scheduled_monitor,
            time=jadwal_sore,
            name="carousell_daily_1700",
        )

        logger.info("Bot Telegram aktif. Jadwal harian diatur pada 07:00 WIB.")
        app.run_polling()