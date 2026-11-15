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


class CarousellTelegramBot:
    def __init__(self):
        self.scraper = CarousellScraper()
        self.db = DatabaseManager()
        self.reporter = ReportGenerator()

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = (
            "👋 *Bot Scraper & Pantau Harga Carousell Indonesia*\n\n"
            "Perintah yang tersedia:\n"
            "• `/scrape [keyword]` — Ambil data terbaru (default: `botol`)\n"
            "• `/analisis [keyword]` — Lihat statistik harga dari database\n"
            "• `/laporan [keyword]` — Unduh laporan Excel (.xlsx)\n"
            "• `/pantau on|off` — Aktifkan pemantauan otomatis berkala"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    async def cmd_scrape(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyword = " ".join(context.args).strip() or Config.DEFAULT_KEYWORD
        await update.message.reply_text(f"⏳ Mengambil data Carousell untuk `{keyword}`...", parse_mode=ParseMode.MARKDOWN)

        items = self.scraper.scrape(keyword=keyword)
        sync_result = self.db.save_listings(items, keyword=keyword)

        if sync_result["new"] or sync_result["price_drops"]:
            msg = MessageFormatter.format_new_items_alert(
                sync_result["new"], sync_result["price_drops"], keyword
            )
        else:
            msg = (
                f"✅ Selesai memindai *{len(items)}* produk untuk `{keyword}`.\n"
                "Belum ada produk baru atau perubahan harga sejak pengecekan terakhir."
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
            await update.message.reply_text("Data kosong. Jalankan `/scrape` terlebih dahulu.", parse_mode=ParseMode.MARKDOWN)
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
        logger.info("Menjalankan jadwal pantau otomatis untuk '%s'", keyword)
        items = self.scraper.scrape(keyword=keyword)
        sync_result = self.db.save_listings(items, keyword=keyword)

        if (sync_result["new"] or sync_result["price_drops"]) and Config.TELEGRAM_CHAT_ID:
            msg = MessageFormatter.format_new_items_alert(
                sync_result["new"], sync_result["price_drops"], keyword
            )
            await context.bot.send_message(
                chat_id=Config.TELEGRAM_CHAT_ID,
                text=msg,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

    async def cmd_pantau(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        mode = context.args[0].lower() if context.args else "on"
        job_name = "carousell_auto_monitor"

        for job in context.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()

        if mode == "off":
            await update.message.reply_text("🛑 Pemantauan otomatis dimatikan.")
            return

        interval_sec = Config.SCRAPE_INTERVAL_MINUTES * 60
        context.job_queue.run_repeating(
            self.scheduled_monitor, interval=interval_sec, first=10, name=job_name
        )
        await update.message.reply_text(
            f"🟢 Pemantauan otomatis aktif setiap *{Config.SCRAPE_INTERVAL_MINUTES} menit*.",
            parse_mode=ParseMode.MARKDOWN,
        )

    def run(self) -> None:
        if not Config.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN belum diisi di file .env")

        app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_start))
        app.add_handler(CommandHandler("scrape", self.cmd_scrape))
        app.add_handler(CommandHandler("analisis", self.cmd_analisis))
        app.add_handler(CommandHandler("laporan", self.cmd_laporan))
        app.add_handler(CommandHandler("pantau", self.cmd_pantau))

        logger.info("Bot Telegram berjalan...")
        app.run_polling()