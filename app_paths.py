r"""
Merkezi path yönetimi -- normal ve PyInstaller --onefile modunda calisir.

Veri Mimarisi (v1):
    ASSET_ROOT  -> Program dosyalari (assets/, schema.sql, fonts)
                   EXE modunda: sys._MEIPASS  |  Normal: proje koku
    DATA_DIR    -> %LOCALAPPDATA%\OfferManagementSystem\data
                   Musteri/teklif/urun verisi, logo, imzalar, config
    BACKUP_DIR  -> %USERPROFILE%\Documents\OfferManagementSystem\backups
                   Otomatik ve manuel ZIP yedekler

Kullanim:
    from app_paths import ASSET_ROOT, DATA_DIR, DB_PATH, BACKUP_DIR
"""
import sys, os, shutil
from pathlib import Path

# ── Program kökü (asset'ler) ──────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    # PyInstaller --onefile: gömülü dosyalar geçici _MEIPASS'ta
    ASSET_ROOT = Path(sys._MEIPASS)
    _EXE_DIR   = Path(sys.executable).parent
else:
    ASSET_ROOT = Path(__file__).parent
    _EXE_DIR   = Path(__file__).parent

# Program asset dizinleri (salt okunur — program ile birlikte gelir)
ASSETS_DIR  = ASSET_ROOT / "assets"
SCHEMA_PATH = ASSET_ROOT / "database" / "schema.sql"

# ── Kullanıcı verisi → AppData\Local\OfferManagementSystem\data ──────────────
_localappdata = Path(os.environ.get("LOCALAPPDATA", "")) \
                if os.environ.get("LOCALAPPDATA") \
                else (Path.home() / "AppData" / "Local")

DATA_DIR = _localappdata / "OfferManagementSystem" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH  = DATA_DIR / "database.db"
PDF_DIR  = DATA_DIR / "offers_pdf"
LOG_DIR  = DATA_DIR / "logs"

# Kullanıcıya özgü varlıklar (program verisi — AppData'da)
CFG_PATH  = DATA_DIR / "company.cfg"
LOGO_PATH = DATA_DIR / "logo.png"
SIG1_PATH = DATA_DIR / "signature1.png"
SIG2_PATH = DATA_DIR / "signature2.png"

# ── Yedekler → Documents\OfferManagementSystem\backups ───────────────────────
BACKUP_DIR = Path.home() / "Documents" / "OfferManagementSystem" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ── Backward compatibility ────────────────────────────────────────────────────
# Eski sürümler DATA_ROOT kullanıyordu — AppData üst klasörüne işaret eder
DATA_ROOT = DATA_DIR.parent   # AppData\Local\OfferManagementSystem


# ── İlk çalıştırma: eski konumdaki verileri AppData'ya taşı ──────────────────
def _migrate_old_data():
    """
    Eski sürümden geçiş (tek seferlik):
    exe yanındaki data/ ve assets/ klasöründen AppData'ya kopyalar.
    Migrasyon tamamlandıktan sonra .migrated marker bırakır.
    Güncelleme sistemi AppData/Documents'a dokunmaz.
    """
    marker = DATA_DIR / ".migrated"
    if marker.exists():
        return

    migrations = [
        (_EXE_DIR / "data"   / "database.db",    DB_PATH),
        (_EXE_DIR / "assets" / "company.cfg",     CFG_PATH),
        (_EXE_DIR / "assets" / "logo.png",        LOGO_PATH),
        (_EXE_DIR / "assets" / "signature1.png",  SIG1_PATH),
        (_EXE_DIR / "assets" / "signature2.png",  SIG2_PATH),
    ]

    for src, dst in migrations:
        if src.exists() and not dst.exists():
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
            except Exception:
                pass   # Sessizce geç — kritik değil

    try:
        marker.touch()
    except Exception:
        pass


# Migrasyon otomatik çalıştır (import sırasında)
_migrate_old_data()
