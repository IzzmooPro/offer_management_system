"""
EXE Dağıtım Öncesi Temizleme Scripti — clear_for_distribution.py

Temizlenenler (test verileri):
  - Tüm müşteri kayıtları  (customers tablosu)
  - Tüm teklif kayıtları   (offers + offer_items tabloları)
  - Tüm ürün kayıtları     (products tablosu)
  - Teklif sayacı sıfırlanır (offer_counter)

Korunanlar (kullanıcı ayarları):
  - Şirket bilgileri       (company.cfg / assets/company.cfg)
  - PDF şablon ayarları    (company.cfg içindeki pdf_* alanları)
  - Logo ve imzalar        (logo.png, signature1.png, signature2.png)

Kullanım:
  python clear_for_distribution.py

UYARI: Bu işlem geri alınamaz. Önce yedek alın!
"""
import sys
from pathlib import Path

# Proje kökünü yol'a ekle
sys.path.insert(0, str(Path(__file__).parent))

from app_paths import DB_PATH


def confirm(msg: str) -> bool:
    try:
        ans = input(f"{msg} (evet/hayır): ").strip().lower()
        return ans in ("evet", "e", "yes", "y")
    except (EOFError, KeyboardInterrupt):
        return False


def clear_test_data():
    print("=" * 60)
    print("  Teklif Yönetim Sistemi — Dağıtım Temizleme Scripti")
    print("=" * 60)
    print()

    if not DB_PATH.exists():
        print(f"[!] Veritabanı bulunamadı: {DB_PATH}")
        print("    Program en az bir kez çalıştırılmış olmalı.")
        return

    print(f"Veritabanı: {DB_PATH}")
    print()
    print("Silinecekler:")
    print("  • Tüm müşteri kayıtları")
    print("  • Tüm teklif ve teklif kalem kayıtları")
    print("  • Tüm ürün kayıtları")
    print("  • Teklif sayacı (sıfırlanır)")
    print()
    print("Korunacaklar:")
    print("  • Şirket bilgileri (company.cfg)")
    print("  • PDF şablon metinleri")
    print("  • Logo ve imza görselleri")
    print()

    if not confirm("⚠️  Devam etmek istiyor musunuz?"):
        print("İptal edildi.")
        return

    import sqlite3
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur  = conn.cursor()

        # Silme sırası önemli (FK kısıtları)
        cur.execute("DELETE FROM offer_items")
        cur.execute("DELETE FROM offers")
        cur.execute("DELETE FROM customers")
        cur.execute("DELETE FROM products")

        # Teklif sayacını sıfırla
        cur.execute("DELETE FROM offer_counter")

        # SQLite'ın otomatik id sayacını da sıfırla
        cur.execute("DELETE FROM sqlite_sequence WHERE name IN "
                    "('offers','offer_items','customers','products','offer_counter')")

        conn.commit()
        conn.close()

        print()
        print("✅ Test verileri temizlendi.")
        print("   Program EXE olarak dağıtılmaya hazır.")

    except Exception as e:
        print(f"\n[HATA] Temizleme başarısız: {e}")
        import traceback
        traceback.print_exc()

    print()
    input("Çıkmak için Enter'a basın...")


if __name__ == "__main__":
    clear_test_data()
