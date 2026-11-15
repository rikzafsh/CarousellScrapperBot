import logging
import os
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
LOG_DIR = BASE_DIR / os.getenv("LOG_DIR", "logs")

for folder in (DATA_DIR, OUTPUT_DIR, LOG_DIR):
    folder.mkdir(parents=True, exist_ok=True)


class Config:
    TARGET_URL: str = os.getenv(
        "TARGET_URL",
        "https://id.carousell.com/search/botol?addRecent=true&canChangeKeyword=true&includeSuggestions=true&sort_by=3&t-search_query_source=direct_search",
    )
    DEFAULT_KEYWORD: str = os.getenv("DEFAULT_KEYWORD", "botol")
    MAX_ITEMS: int = int(os.getenv("MAX_ITEMS", "40"))
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    SCRAPE_INTERVAL_MINUTES: int = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "15"))

    DB_PATH: str = str(BASE_DIR / os.getenv("DB_PATH", "data/carousell.db"))
    OUTPUT_DIR: Path = OUTPUT_DIR
    LOG_DIR: Path = LOG_DIR
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))

    @staticmethod
    def build_search_url(keyword: str | None = None) -> str:
        if not keyword or keyword.strip().lower() == Config.DEFAULT_KEYWORD.lower():
            return Config.TARGET_URL
        encoded = quote(keyword.strip())
        return (
            f"https://id.carousell.com/search/{encoded}"
            "?addRecent=true&canChangeKeyword=true&includeSuggestions=true"
            "&sort_by=3&t-search_query_source=direct_search"
        )


def setup_logger(name: str = "carousell_bot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger