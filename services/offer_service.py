"""Teklif servis katmanı."""
import datetime, logging
from pathlib import Path
from app_paths import CFG_PATH, PDF_DIR
from typing import List, Optional
from database.db_manager import get_db

logger = logging.getLogger("offer_service")


def _get_offer_prefix() -> str:
    if CFG_PATH.exists():
        try:
            for line in CFG_PATH.read_text(encoding="utf-8").splitlines():
                if line.startswith("offer_prefix="):
                    val = line.partition("=")[2].strip()
                    if val: return val
        except Exception as e:
            logger.warning("Config okunamadı: %s", e)
    return "SNS"


_OFFER_KEYS = ("company_name", "customer_address", "contact_person",
               "offer_no", "date", "currency", "validity", "payment_term", "status")
_SHORT_KEYS = ("company_name", "offer_no", "date", "currency", "status")


def _normalize(d: dict, keys=_OFFER_KEYS) -> dict:
    """None değerleri boş stringe çevirir (migration öncesi NULL kayıtlar için)."""
    for k in keys:
        if d.get(k) is None:
            d[k] = ""
    return d


class OfferService:
    def generate_offer_no(self) -> str:
        """Yeni teklif numarası üret — atomik transaction ile race condition önlendi.
        Format: PREFIX-000001 (prefix ayarlardan gelir, varsayılan SNS)
        Sayaç yıl bazlı değil, global olarak artırılır.
        """
        db = get_db()
        prefix = _get_offer_prefix()
        with db.transaction() as conn:
            # Mevcut en büyük sayaç değerini al (year=0 global sayaç için)
            row = conn.execute(
                "SELECT last_number FROM offer_counter WHERE year = 0"
            ).fetchone()
            if row:
                next_num = row["last_number"] + 1
                conn.execute(
                    "UPDATE offer_counter SET last_number=? WHERE year=0",
                    (next_num,)
                )
            else:
                # İlk çalıştırma — mevcut tekliflerden en büyük numarayı bul
                max_row = conn.execute(
                    "SELECT MAX(id) as max_id FROM offers"
                ).fetchone()
                next_num = (max_row["max_id"] or 0) + 1 if max_row else 1
                # Eski yıl bazlı kayıtları temizle, global sayaç ekle
                conn.execute("DELETE FROM offer_counter")
                conn.execute(
                    "INSERT INTO offer_counter (year, last_number) VALUES (0, ?)",
                    (next_num,)
                )
        return f"{prefix}-{next_num:06d}"

    def get_all(self) -> List[dict]:
        db = get_db()
        rows = db.fetchall("""
            SELECT o.*,
                   COALESCE(o.company_name, c.company_name, '') AS company_name,
                   COALESCE(o.customer_address, c.address,  '') AS customer_address,
                   COALESCE(o.contact_person,  c.contact_person, '') AS contact_person
            FROM offers o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.id DESC
        """)
        return [_normalize(dict(r)) for r in rows]

    def get_recent(self, limit=10) -> List[dict]:
        db = get_db()
        rows = db.fetchall("""
            SELECT o.*,
                   COALESCE(o.company_name, c.company_name, '') AS company_name
            FROM offers o
            LEFT JOIN customers c ON o.customer_id = c.id
            ORDER BY o.id DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in rows]

    def get_by_id(self, offer_id: int) -> Optional[dict]:
        db = get_db()
        row = db.fetchone("""
            SELECT o.*,
                   COALESCE(o.company_name, c.company_name, '') AS company_name,
                   COALESCE(o.customer_address, c.address,  '') AS customer_address,
                   COALESCE(o.contact_person,  c.contact_person, '') AS contact_person
            FROM offers o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """, (offer_id,))
        if not row: return None
        offer_dict = dict(row)
        items = db.fetchall("SELECT * FROM offer_items WHERE offer_id=? ORDER BY id", (offer_id,))
        offer_dict["items"] = [dict(i) for i in items]
        return offer_dict

    def save(self, offer_data: dict) -> int:
        """Teklif ve kalemlerini atomik olarak kaydet — hata olursa tümü geri alınır."""
        db = get_db()
        offer_id = offer_data.get("id")
        company  = offer_data.get("company_name", "")
        address  = offer_data.get("customer_address", "")
        contact  = offer_data.get("contact_person", "")
        validity = offer_data.get("validity", "")
        val_note = offer_data.get("validity_note", "")
        payment  = offer_data.get("payment_term", "")
        status   = offer_data.get("status", "Beklemede")

        with db.transaction() as conn:
            if offer_id:
                conn.execute("""
                    UPDATE offers SET
                      customer_id=?, company_name=?, customer_address=?, contact_person=?,
                      date=?, currency=?, total_amount=?,
                      validity=?, validity_note=?, payment_term=?, status=?
                    WHERE id=?
                """, (offer_data.get("customer_id"), company, address, contact,
                      offer_data["date"], offer_data["currency"], offer_data["total_amount"],
                      validity, val_note, payment, status, offer_id))
                conn.execute("DELETE FROM offer_items WHERE offer_id=?", (offer_id,))
            else:
                cursor = conn.execute("""
                    INSERT INTO offers
                      (offer_no, customer_id, company_name, customer_address, contact_person,
                       date, currency, total_amount, validity, validity_note, payment_term, status)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """, (offer_data["offer_no"], offer_data.get("customer_id"), company, address, contact,
                      offer_data["date"], offer_data["currency"], offer_data["total_amount"],
                      validity, val_note, payment, status))
                offer_id = cursor.lastrowid

            for item in offer_data.get("items", []):
                conn.execute("""
                    INSERT INTO offer_items
                      (offer_id, product_id, product_code, product_name, description,
                       quantity, unit, delivery_time, unit_price, total_price)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                """, (offer_id, item.get("product_id"), item.get("product_code",""),
                      item.get("product_name",""), item.get("description",""),
                      item.get("quantity",1), item.get("unit","Adet"),
                      item.get("delivery_time","2-3 Hafta"),
                      item.get("unit_price",0), item.get("total_price",0)))

        logger.info("Teklif kaydedildi: id=%d, no=%s", offer_id, offer_data.get("offer_no",""))
        return offer_id

    def update_status(self, offer_id: int, status: str):
        """Teklif durumunu güncelle: Beklemede / Onaylandı / İptal."""
        db = get_db()
        db.execute("UPDATE offers SET status=? WHERE id=?", (status, offer_id))
        logger.info("Teklif durumu güncellendi: id=%d → %s", offer_id, status)

    def delete(self, offer_id: int):
        """Teklifi sil — DB kaydı + varsa PDF dosyası."""
        db = get_db()
        # PDF dosyasını sil (offer_no gerekli — önce al)
        row = db.fetchone("SELECT offer_no FROM offers WHERE id=?", (offer_id,))
        if row:
            pdf_path = PDF_DIR / f"{row['offer_no']}.pdf"
            try:
                if pdf_path.exists():
                    pdf_path.unlink()
                    logger.info("PDF silindi: %s", pdf_path.name)
            except Exception as e:
                logger.warning("PDF silinemedi: %s", e)
        with db.transaction() as conn:
            conn.execute("DELETE FROM offer_items WHERE offer_id=?", (offer_id,))
            conn.execute("DELETE FROM offers WHERE id=?", (offer_id,))


    def get_by_date_range(self, date_from: str, date_to: str) -> list:
        """Tarih aralığına göre teklifler. Format: YYYY-MM-DD"""
        db = get_db()
        rows = db.fetchall("""
            SELECT o.*,
                   COALESCE(o.company_name, c.company_name, '') AS company_name
            FROM offers o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.date >= ? AND o.date <= ?
            ORDER BY o.date DESC
        """, (date_from, date_to))
        return [_normalize(dict(r), _SHORT_KEYS) for r in rows]

    def get_by_customer(self, customer_id: int) -> list:
        """Müşteriye ait tüm teklifler."""
        db = get_db()
        rows = db.fetchall("""
            SELECT o.*,
                   COALESCE(o.company_name, c.company_name, '') AS company_name
            FROM offers o
            LEFT JOIN customers c ON o.customer_id = c.id
            WHERE o.customer_id = ?
            ORDER BY o.id DESC
        """, (customer_id,))
        return [_normalize(dict(r), _SHORT_KEYS) for r in rows]

    def count(self) -> int:
        row = get_db().fetchone("SELECT COUNT(*) as cnt FROM offers")
        return row["cnt"] if row else 0
