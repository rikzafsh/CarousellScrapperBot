import sqlite3
from datetime import datetime, timezone
from typing import Any
from config import Config


class DatabaseManager:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or Config.DB_PATH
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    listing_id TEXT PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    condition TEXT,
                    seller TEXT,
                    time_posted TEXT,
                    url TEXT NOT NULL,
                    image_url TEXT,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scrape_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    total_scraped INTEGER NOT NULL,
                    new_count INTEGER NOT NULL,
                    price_drop_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_listings(
        self, items: list[dict[str, Any]], keyword: str = ""
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        new_items: list[dict[str, Any]] = []
        price_drops: list[dict[str, Any]] = []

        with self._connect() as conn:
            for item in items:
                lid = item["listing_id"]
                existing = conn.execute(
                    "SELECT price FROM listings WHERE listing_id = ?", (lid,)
                ).fetchone()

                if existing is None:
                    conn.execute(
                        """
                        INSERT INTO listings (
                            listing_id, keyword, title, price, condition,
                            seller, time_posted, url, image_url, first_seen, last_seen
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            lid,
                            item.get("keyword") or keyword,
                            item["title"],
                            item["price"],
                            item.get("condition", ""),
                            item.get("seller", ""),
                            item.get("time_posted", ""),
                            item["url"],
                            item.get("image_url", ""),
                            now,
                            now,
                        ),
                    )
                    new_items.append(item)
                else:
                    old_price = existing["price"]
                    new_price = item["price"]
                    if 0 < new_price < old_price:
                        drop_info = {**item, "old_price": old_price}
                        price_drops.append(drop_info)

                    conn.execute(
                        """
                        UPDATE listings
                        SET title = ?, price = ?, condition = ?, time_posted = ?, last_seen = ?
                        WHERE listing_id = ?
                        """,
                        (
                            item["title"],
                            new_price,
                            item.get("condition", ""),
                            item.get("time_posted", ""),
                            now,
                            lid,
                        ),
                    )

            conn.execute(
                """
                INSERT INTO scrape_logs (keyword, total_scraped, new_count, price_drop_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    keyword or Config.DEFAULT_KEYWORD,
                    len(items),
                    len(new_items),
                    len(price_drops),
                    now,
                ),
            )

        return {
            "new": new_items,
            "price_drops": price_drops,
            "total_processed": len(items),
        }

    def get_listings(self, keyword: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            if keyword:
                rows = conn.execute(
                    "SELECT * FROM listings WHERE keyword = ? ORDER BY last_seen DESC LIMIT ?",
                    (keyword, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM listings ORDER BY last_seen DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]