import re
from datetime import datetime, timezone
from typing import Any
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import Config, setup_logger

logger = setup_logger("scraper")

CONDITION_KEYWORDS = {
    "baru",
    "seperti baru",
    "jarang dipakai",
    "sering dipakai",
    "sudah lama dipakai",
    "brand new",
    "like new",
    "lightly used",
    "well used",
    "heavily used",
}


class CarousellScraper:
    def __init__(self, headless: bool | None = None, max_items: int | None = None):
        self.headless = Config.HEADLESS if headless is None else headless
        self.max_items = max_items or Config.MAX_ITEMS

    @staticmethod
    def parse_price(price_text: str) -> int:
        """Mengubah teks harga seperti 'Rp 125.000' atau 'Gratis' menjadi integer."""
        if not price_text:
            return 0
        cleaned = price_text.strip().lower()
        if "gratis" in cleaned or "free" in cleaned:
            return 0
        digits = re.sub(r"[^\d]", "", cleaned)
        return int(digits) if digits else 0

    @staticmethod
    def extract_listing_id(href: str) -> str:
        """Mengambil ID numerik dari URL produk Carousell (/p/nama-produk-123456789/)."""
        if not href:
            return ""
        clean_path = href.split("?")[0].rstrip("/")
        match = re.search(r"-(\d+)$", clean_path)
        if match:
            return match.group(1)
        return clean_path.split("/")[-1]

    def parse_html(self, html: str, keyword: str = "") -> list[dict[str, Any]]:
        """Mem-parsing card produk dari HTML hasil render halaman pencarian."""
        soup = BeautifulSoup(html, "html.parser")
        seen_ids: set[str] = set()
        results: list[dict[str, Any]] = []

        for anchor in soup.select('a[href*="/p/"]'):
            href = anchor.get("href", "")
            listing_id = self.extract_listing_id(href)
            if not listing_id or listing_id in seen_ids:
                continue

            # Naik ke container card terdekat untuk membaca seluruh teks card
            card = anchor
            for _ in range(4):
                if card.parent and len(card.parent.get_text(" ", strip=True)) < 500:
                    card = card.parent
                else:
                    break

            texts = [
                t.strip()
                for t in card.stripped_strings
                if t.strip() and t.strip() not in {"•", "|", "Terjual", "Promosi"}
            ]
            if not texts:
                continue

            price_str = ""
            price_val = 0
            condition = "Tidak disebutkan"
            time_posted = "-"
            seller = "-"
            title_candidates: list[str] = []

            for txt in texts:
                low = txt.lower()
                if low.startswith("rp") or low == "gratis":
                    if not price_str:
                        price_str = txt
                        price_val = self.parse_price(txt)
                elif low in CONDITION_KEYWORDS:
                    condition = txt
                elif re.search(r"\b(lalu|ago|menit|jam|hari|bulan)\b", low):
                    time_posted = txt
                elif txt.startswith("@"):
                    seller = txt.lstrip("@")
                else:
                    title_candidates.append(txt)

            # Judul produk biasanya teks terpanjang di luar metadata penjual/waktu
            title = max(title_candidates, key=len) if title_candidates else f"Listing {listing_id}"
            if len(title_candidates) > 1 and seller == "-":
                seller = title_candidates[0] if title_candidates[0] != title else "-"

            img_tag = card.find("img")
            image_url = ""
            if img_tag:
                image_url = img_tag.get("src") or img_tag.get("data-src") or ""

            full_url = (
                href.split("?")[0]
                if href.startswith("http")
                else f"https://id.carousell.com{href.split('?')[0]}"
            )

            seen_ids.add(listing_id)
            results.append(
                {
                    "listing_id": listing_id,
                    "keyword": keyword or Config.DEFAULT_KEYWORD,
                    "title": title,
                    "price": price_val,
                    "price_formatted": price_str or f"Rp {price_val:,}".replace(",", "."),
                    "condition": condition,
                    "seller": seller,
                    "time_posted": time_posted,
                    "url": full_url,
                    "image_url": image_url,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            if len(results) >= self.max_items:
                break

        return results

    def scrape(self, url: str | None = None, keyword: str | None = None) -> list[dict[str, Any]]:
        target_keyword = keyword or Config.DEFAULT_KEYWORD
        target_url = url or Config.build_search_url(target_keyword)
        logger.info("Memulai scraping: %s", target_url)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                locale="id-ID",
                timezone_id="Asia/Jakarta",
                viewport={"width": 1366, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            try:
                page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_selector('a[href*="/p/"]', timeout=20000)
            except PlaywrightTimeout:
                logger.warning("Timeout menunggu card produk pada %s", target_url)

            # Scroll bertahap untuk memicu lazy-load listing
            for _ in range(3):
                page.mouse.wheel(0, 1800)
                page.wait_for_timeout(1500)
                show_more = page.locator("button:has-text('Tampilkan lebih banyak')")
                if show_more.count() > 0 and show_more.first.is_visible():
                    try:
                        show_more.first.click(timeout=3000)
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass

            html = page.content()
            browser.close()

        items = self.parse_html(html, keyword=target_keyword)
        logger.info("Berhasil mengekstrak %d produk untuk keyword '%s'", len(items), target_keyword)
        return items