"""
Teklif Yönetim Sistemi — Ana giriş noktası  (Version: v1)

Başlangıç sırası:
  1. app_paths import → AppData klasörleri oluşturulur + eski veri migrasyonu
  2. Loglama yapılandırılır
  3. Veri klasörü boşsa backup kontrolü yapılır
  4. QApplication + MainWindow oluşturulur
  5. Arka planda güncelleme kontrolü başlar (MainWindow içinde)
"""
import sys, os, traceback, logging
from datetime import datetime
from pathlib import Path

# ── app_paths import (AppData klasörleri oluşturulur + migrasyon) ─────────────
# Bu import yan etki olarak:
#   - AppData\Local\OfferManagementSystem\data/ oluşturur
#   - Documents\OfferManagementSystem\backups/ oluşturur
#   - Eski exe yanındaki veriyi AppData'ya kopyalar (tek seferlik)
from app_paths import (
    ASSET_ROOT, DATA_DIR, LOG_DIR, DB_PATH, BACKUP_DIR
)

# ── Loglama ──────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_filename = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"


def _clean_old_logs(log_dir: Path, keep_days: int = 30):
    """30 günden eski log dosyalarını temizle."""
    cutoff = datetime.now().timestamp() - keep_days * 86400
    for f in log_dir.glob("app_*.log"):
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
        except Exception:
            pass


_clean_old_logs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(str(log_filename), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("main")

sys.path.insert(0, str(ASSET_ROOT))


# ── Global exception hook ─────────────────────────────────────────────────────

def exception_hook(exc_type, exc_value, exc_tb):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.critical("=== UYGULAMA HATASI ===\n%s", error_msg)
    print("\n" + "=" * 60)
    print("HATA OLUŞTU! Detaylar log dosyasında:")
    print(f"  {log_filename}")
    print("=" * 60)
    print("Devam etmek için Enter'a basın...")
    try:
        input()
    except Exception:
        pass


sys.excepthook = exception_hook


# ── Başlangıç veri kontrolü ───────────────────────────────────────────────────

def _check_data_on_startup(app) -> bool:
    """
    Veri klasörü boşsa (database.db yok) yedek klasörünü kontrol eder.
    Yedek bulunursa kullanıcıya sorar, onay gelirse geri yükler.
    True → uygulama yeniden başlatılmalı (geri yükleme yapıldı)
    """
    if DB_PATH.exists():
        return False

    # database.db yok → backup klasörünü kontrol et
    from ui.backup_manager import check_and_restore_on_startup
    restored = check_and_restore_on_startup(parent=None)
    if restored:
        # Geri yükleme sonrası yeniden başlat
        logger.info("Backup geri yüklendi, program yeniden başlatılıyor.")
        try:
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)
        except Exception as e:
            logger.warning("Yeniden başlatma başarısız: %s", e)
        return True
    return False


# ── Ana fonksiyon ─────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 50)
    logger.info("Teklif Yönetim Sistemi başlatılıyor...  (Version: v1)")
    logger.info("Python: %s", sys.version)
    logger.info("Veri klasörü: %s", DATA_DIR)
    logger.info("Yedek klasörü: %s", BACKUP_DIR)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFontDatabase

    app = QApplication(sys.argv)
    app.setApplicationName("Teklif Yönetim Sistemi")
    app.setOrganizationName("TeklifApp")

    # Başlangıç veri kontrolü
    if _check_data_on_startup(app):
        sys.exit(0)

    # Font yükleme — Inter varsa Inter, yoksa Segoe UI
    inter_path = ASSET_ROOT / "assets" / "fonts" / "Inter-Regular.ttf"
    font_family = "Segoe UI"
    if inter_path.exists():
        fid = QFontDatabase.addApplicationFont(str(inter_path))
        if fid >= 0:
            families = QFontDatabase.applicationFontFamilies(fid)
            if families:
                font_family = families[0]

    if font_family != "Segoe UI":
        os.environ["APP_FONT_FAMILY"] = font_family

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    logger.info("Ana pencere açıldı.")

    exit_code = app.exec()

    # Uygulama kapanınca DB bağlantısını düzgün kapat
    try:
        from database.db_manager import get_db
        get_db().close()
        logger.info("Veritabanı bağlantısı kapatıldı.")
    except Exception as e:
        logger.warning("DB kapatma hatası: %s", e)

    logger.info("Uygulama kapatıldı. Çıkış kodu: %d", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
