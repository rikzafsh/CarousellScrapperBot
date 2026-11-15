import csv
from datetime import datetime
from pathlib import Path
from typing import Any
from openpyxl import Workbook
from config import Config


class ReportGenerator:
    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_excel(
        self,
        items: list[dict[str, Any]],
        summary: dict[str, Any],
        keyword: str = "botol",
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"carousell_{keyword}_{timestamp}.xlsx"

        wb = Workbook()

        # Sheet 1: Daftar Produk
        ws_items = wb.active
        ws_items.title = "Daftar Produk"
        columns = [
            "listing_id",
            "title",
            "price",
            "condition",
            "seller",
            "time_posted",
            "url",
            "last_seen",
        ]
        ws_items.append(columns)
        for item in items:
            ws_items.append([item.get(col, "") for col in columns])

        # Sheet 2: Ringkasan Analisis
        ws_summary = wb.create_sheet(title="Ringkasan Analisis")
        ws_summary.append(["Metrik", "Nilai"])
        ws_summary.append(["Total Produk", summary.get("total_items", 0)])
        ws_summary.append(["Rata-rata Harga (Rp)", summary.get("avg_price", 0)])
        ws_summary.append(["Median Harga (Rp)", summary.get("median_price", 0)])
        ws_summary.append(["Harga Termurah (Rp)", summary.get("min_price", 0)])
        ws_summary.append(["Harga Termahal (Rp)", summary.get("max_price", 0)])

        wb.save(filepath)
        return filepath

    def export_csv(self, items: list[dict[str, Any]], keyword: str = "botol") -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"carousell_{keyword}_{timestamp}.csv"
        if not items:
            filepath.write_text("", encoding="utf-8-sig")
            return filepath

        fieldnames = list(items[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)
        return filepath