from collections import Counter
from statistics import mean, median
from typing import Any


class DataAnalyzer:
    @staticmethod
    def analyze(items: list[dict[str, Any]]) -> dict[str, Any]:
        if not items:
            return {
                "total_items": 0,
                "priced_items": 0,
                "avg_price": 0,
                "median_price": 0,
                "min_price": 0,
                "max_price": 0,
                "condition_breakdown": {},
                "best_deals": [],
            }

        prices = [item["price"] for item in items if item.get("price", 0) > 0]
        avg_price = round(mean(prices)) if prices else 0
        med_price = round(median(prices)) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        conditions = Counter(item.get("condition", "Tidak disebutkan") for item in items)

        # Produk dengan harga <= 70% dari median dianggap penawaran menarik
        threshold = med_price * 0.7 if med_price > 0 else 0
        best_deals = sorted(
            [item for item in items if 0 < item.get("price", 0) <= threshold],
            key=lambda x: x["price"],
        )[:5]

        return {
            "total_items": len(items),
            "priced_items": len(prices),
            "avg_price": avg_price,
            "median_price": med_price,
            "min_price": min_price,
            "max_price": max_price,
            "condition_breakdown": dict(conditions),
            "best_deals": best_deals,
        }