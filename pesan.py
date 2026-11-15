from typing import Any


class MessageFormatter:
    @staticmethod
    def format_rupiah(amount: int) -> str:
        if amount <= 0:
            return "Gratis / Hubungi Penjual"
        return f"Rp {amount:,}".replace(",", ".")

    @classmethod
    def format_new_items_alert(
        cls,
        new_items: list[dict[str, Any]],
        price_drops: list[dict[str, Any]],
        keyword: str,
    ) -> str:
        lines = [f"🔔 *Update Carousell: `{keyword}`*\n"]

        if new_items:
            lines.append(f"🆕 *{len(new_items)} Produk Baru Ditemukan:*")
            for item in new_items[:8]:
                price_txt = cls.format_rupiah(item["price"])
                lines.append(
                    f"• [{item['title']}]({item['url']})\n"
                    f"  💰 {price_txt} | 📦 {item.get('condition', '-')} | 🕒 {item.get('time_posted', '-')}"
                )

        if price_drops:
            lines.append(f"\n📉 *{len(price_drops)} Penurunan Harga:*")
            for item in price_drops[:5]:
                old_txt = cls.format_rupiah(item["old_price"])
                new_txt = cls.format_rupiah(item["price"])
                lines.append(
                    f"• [{item['title']}]({item['url']})\n"
                    f"  ~~{old_txt}~~ ➡️ *{new_txt}*"
                )

        return "\n".join(lines)

    @classmethod
    def format_analysis(cls, summary: dict[str, Any], keyword: str) -> str:
        if summary.get("total_items", 0) == 0:
            return f"Belum ada data tersimpan untuk kata kunci `{keyword}`."

        lines = [
            f"📊 *Analisis Harga Carousell (`{keyword}`)*",
            f"• Total listing: *{summary['total_items']}*",
            f"• Rata-rata harga: *{cls.format_rupiah(summary['avg_price'])}*",
            f"• Median harga: *{cls.format_rupiah(summary['median_price'])}*",
            f"• Harga terendah: *{cls.format_rupiah(summary['min_price'])}*",
            f"• Harga tertinggi: *{cls.format_rupiah(summary['max_price'])}*",
            "\n*Distribusi Kondisi:*",
        ]
        for cond, count in summary.get("condition_breakdown", {}).items():
            lines.append(f"  - {cond}: {count}")

        deals = summary.get("best_deals", [])
        if deals:
            lines.append("\n🔥 *Penawaran Di Bawah Pasar:*")
            for d in deals:
                lines.append(f"• [{d['title']}]({d['url']}) — *{cls.format_rupiah(d['price'])}*")

        return "\n".join(lines)