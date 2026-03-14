"""
Veri yedekleme & geri yükleme sistemi.

Özellikler:
  - Manuel yedekleme (klasör sor → backup_YYYY_MM_DD_HHMMSS.zip)
  - Otomatik yedekleme (arka plan, varsayılan Documents/OfferManagementSystem/backups)
  - Program kapanışında otomatik yedek
  - Teklif kaydedilince otomatik yedek
  - Geri yükleme (.zip seç, overwrite-safe)
  - Test butonu (otomatik yedeklemeyi anında tetikle)
  - Max 20 yedek tutulur (eskiler silinir)
"""
import logging, shutil, zipfile, json
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout, QFileDialog, QMessageBox, QComboBox,
    QCheckBox, QWidget, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
logger = logging.getLogger("backup")

from app_paths import (
    DATA_DIR    as _DATA_DIR,
    DB_PATH     as _DB_PATH,
    CFG_PATH    as _CFG_PATH,
    LOGO_PATH   as _LOGO_PATH,
    SIG1_PATH   as _SIG1_PATH,
    SIG2_PATH   as _SIG2_PATH,
    BACKUP_DIR  as _DEFAULT_BACKUP_DIR,
    DATA_ROOT   as _BASE,
)

_META_PATH = _DATA_DIR / "backup_meta.json"

# Güncelleme sistemi bu yolların içine asla yazamaz (güvenlik)
_PROTECTED_DIRS = [str(_DATA_DIR), str(_DEFAULT_BACKUP_DIR)]


def _load_meta() -> dict:
    if _META_PATH.exists():
        try:
            return json.loads(_META_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "auto_backup_dir": str(_DEFAULT_BACKUP_DIR),
        "auto_interval":   30,
        "auto_enabled":    True,
        "last_backup":     "",
        "backup_count":    0,
    }


def _save_meta(meta: dict):
    try:
        _META_PATH.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        logger.warning("Meta kayıt hatası: %s", e)


def _ts() -> str:
    """backup_YYYY_MM_DD_HHMMSS formatında zaman damgası."""
    return datetime.now().strftime("backup_%Y_%m_%d_%H%M%S")


def create_backup(dest_dir: str) -> str:
    """
    ZIP yedek oluşturur.
    İçerik: database.db + company.cfg + logo/imzalar (varsa)
    Format : backup_YYYY_MM_DD_HHMMSS.zip
    """
    if not _DB_PATH.exists():
        raise FileNotFoundError(f"Veritabanı bulunamadı: {_DB_PATH}")

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / f"{_ts()}.zip"

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        # Ana veritabanı
        zf.write(str(_DB_PATH), "database.db")

        # Ayarlar dosyası
        if _CFG_PATH.exists():
            zf.write(str(_CFG_PATH), "company.cfg")

        # Kullanıcı görselleri
        for path, arcname in [
            (_LOGO_PATH, "logo.png"),
            (_SIG1_PATH, "signature1.png"),
            (_SIG2_PATH, "signature2.png"),
        ]:
            if path.exists():
                zf.write(str(path), arcname)

        # Yedek meta bilgisi
        zf.writestr("backup_info.json", json.dumps({
            "backup_date": datetime.now().isoformat(),
            "app":         "Teklif Yönetim Sistemi",
            "version":     "v1",
        }, ensure_ascii=False, indent=2))

    logger.info("Yedek oluşturuldu: %s", zip_path)
    return str(zip_path)


def restore_backup(zip_path: str) -> bool:
    """
    ZIP yedeği geri yükler.
    Hata durumunda orijinal veriyi korur (tmp dosyası mekanizması).
    """
    zp = Path(zip_path)
    if not zp.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {zip_path}")

    with zipfile.ZipFile(str(zp), "r") as zf:
        if "database.db" not in zf.namelist():
            raise ValueError("Geçersiz yedek — database.db içermiyor.")

        # Mevcut verileri geçici dosyalara yedekle
        tmp_db  = _DB_PATH.with_suffix(".db.tmp")
        tmp_cfg = _CFG_PATH.with_suffix(".cfg.tmp") if _CFG_PATH.exists() else None

        if _DB_PATH.exists():
            shutil.copy2(str(_DB_PATH), str(tmp_db))
        if _CFG_PATH.exists() and tmp_cfg:
            shutil.copy2(str(_CFG_PATH), str(tmp_cfg))

        try:
            zf.extract("database.db", str(_DB_PATH.parent))

            if "company.cfg" in zf.namelist():
                zf.extract("company.cfg", str(_CFG_PATH.parent))

            for name, dest in [
                ("logo.png",        _LOGO_PATH),
                ("signature1.png",  _SIG1_PATH),
                ("signature2.png",  _SIG2_PATH),
            ]:
                if name in zf.namelist():
                    zf.extract(name, str(dest.parent))

            # Başarılı — geçici dosyaları sil
            for tmp in [tmp_db, tmp_cfg]:
                if tmp and tmp.exists():
                    tmp.unlink()
            return True

        except Exception as e:
            # Hata — orijinal verileri geri yükle
            if tmp_db and tmp_db.exists():
                shutil.copy2(str(tmp_db), str(_DB_PATH))
                tmp_db.unlink()
            if tmp_cfg and tmp_cfg.exists():
                shutil.copy2(str(tmp_cfg), str(_CFG_PATH))
                tmp_cfg.unlink()
            raise e


def check_and_restore_on_startup(parent=None) -> bool:
    """
    Veri klasörü boşsa (database.db yok) yedek klasörünü kontrol eder.
    Yedek bulunursa kullanıcıya sorar; onay gelirse geri yükler.
    True döner → geri yükleme yapıldı, False → yapılmadı.
    """
    if _DB_PATH.exists():
        return False

    # Yedek klasöründe backup_*.zip ara
    backups = sorted(_DEFAULT_BACKUP_DIR.glob("backup_*.zip"), reverse=True)
    if not backups:
        return False

    latest = backups[0]
    from PySide6.QtWidgets import QMessageBox
    reply = QMessageBox.question(
        parent,
        "Yedek Bulundu",
        f"Önceden oluşturulmuş bir yedek bulundu.\n"
        f"Dosya: {latest.name}\n\n"
        "Verileri geri yüklemek ister misiniz?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if reply != QMessageBox.StandardButton.Yes:
        return False

    try:
        restore_backup(str(latest))
        QMessageBox.information(
            parent, "Geri Yükleme Tamamlandı",
            "Veriler başarıyla geri yüklendi.\n"
            "Program yeniden başlatılıyor..."
        )
        return True
    except Exception as e:
        QMessageBox.critical(
            parent, "Geri Yükleme Hatası",
            f"Geri yükleme başarısız:\n{e}"
        )
        return False


# ── Otomatik Yedekleme Servisi ───────────────────────────────────────────────

class AutoBackupService(QObject):
    backup_done   = Signal(str)
    backup_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._run)
        self._meta = _load_meta()
        self._apply()

    def _apply(self):
        self._timer.stop()
        m = self._meta
        if m.get("auto_enabled"):
            d = m.get("auto_backup_dir", str(_DEFAULT_BACKUP_DIR))
            if d:
                ms = int(m.get("auto_interval", 30)) * 60 * 1000
                self._timer.start(ms)
                logger.info("Otomatik yedekleme: her %ddk → %s",
                            m.get("auto_interval", 30), d)

    def reload(self):
        self._meta = _load_meta()
        self._apply()

    def trigger_now(self, reason: str = ""):
        """Anında yedek al (kapatma, kaydetme veya test için)."""
        self._run(reason)

    def _run(self, reason: str = ""):
        d = self._meta.get("auto_backup_dir", str(_DEFAULT_BACKUP_DIR))
        if not d:
            d = str(_DEFAULT_BACKUP_DIR)
        try:
            p = create_backup(d)
            self._meta["last_backup"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            self._meta["backup_count"] = self._meta.get("backup_count", 0) + 1
            _save_meta(self._meta)
            self.backup_done.emit(p)
            self._cleanup(d)
            if reason:
                logger.info("Yedek alındı (%s): %s", reason, p)
        except Exception as e:
            self.backup_failed.emit(str(e))
            logger.error("Otomatik yedek hatası: %s", e)

    def _cleanup(self, d: str, keep: int = 20):
        """En fazla `keep` adet yedek tut, eskilerini sil."""
        try:
            bkps = sorted(Path(d).glob("backup_*.zip"))
            for old in bkps[:-keep]:
                old.unlink()
        except Exception:
            pass


# ── Dialog ───────────────────────────────────────────────────────────────────

class BackupDialog(QDialog):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Veri Yedekleme & Geri Yükleme")
        self.setMinimumSize(580, 520)
        self._meta = _load_meta()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel("Veri Yedekleme ve Geri Yükleme")
        title.setStyleSheet("font-size:10pt;font-weight:700;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        layout.addWidget(tabs, 1)

        tabs.addTab(self._tab_backup(),  "Yedekleme")
        tabs.addTab(self._tab_restore(), "Geri Yükleme")

        row = QHBoxLayout()
        row.addStretch()
        btn_close = QPushButton("Kapat")
        btn_close.setObjectName("secondary")
        btn_close.clicked.connect(self.accept)
        row.addWidget(btn_close)
        layout.addLayout(row)

    # ── Sekme 1: Yedekleme ───────────────────────────────────────────────────

    def _tab_backup(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(14)

        # Manuel yedekleme
        man = QGroupBox("Manuel Yedekleme")
        ml = QVBoxLayout(man)
        ml.setContentsMargins(14, 12, 14, 12)
        ml.setSpacing(8)
        ml.addWidget(QLabel(
            "Hemen bir yedek almak için klasör seçin.\n"
            "Dosya adı otomatik oluşturulur: backup_YYYY_MM_DD_HHMMSS.zip\n"
            "İçerik: veritabanı, şirket ayarları, logo ve imzalar."
        ))
        last = self._meta.get("last_backup", "")
        self.lbl_last = QLabel(f"Son yedek: {last or 'Henüz alınmadı'}")
        self.lbl_last.setStyleSheet("color:#888;font-size:8pt;")
        ml.addWidget(self.lbl_last)
        r = QHBoxLayout()
        btn = QPushButton("Klasör Seç ve Yedekle")
        btn.setObjectName("secondary")
        btn.setMinimumHeight(36)
        btn.clicked.connect(self._manual)
        r.addWidget(btn)
        r.addStretch()
        ml.addLayout(r)
        layout.addWidget(man)

        # Otomatik yedekleme
        aut = QGroupBox("Otomatik Yedekleme")
        ag = QGridLayout(aut)
        ag.setContentsMargins(14, 12, 14, 12)
        ag.setSpacing(10)
        ag.setColumnStretch(1, 1)

        self.chk_auto = QCheckBox("Otomatik yedeklemeyi etkinleştir")
        self.chk_auto.setChecked(self._meta.get("auto_enabled", True))
        self.chk_auto.stateChanged.connect(self._auto_toggle)
        ag.addWidget(self.chk_auto, 0, 0, 1, 3)

        ag.addWidget(QLabel("Aralık:"), 1, 0)
        self.iv_combo = QComboBox()
        self.iv_combo.addItems(["15 Dakika", "30 Dakika", "1 Saat", "2 Saat"])
        iv_map = {15: 0, 30: 1, 60: 2, 120: 3}
        self.iv_combo.setCurrentIndex(
            iv_map.get(self._meta.get("auto_interval", 30), 1)
        )
        ag.addWidget(self.iv_combo, 1, 1)

        ag.addWidget(QLabel("Yedek Klasörü:"), 2, 0)
        dir_val = self._meta.get("auto_backup_dir", str(_DEFAULT_BACKUP_DIR))
        self.lbl_dir = QLabel(dir_val or str(_DEFAULT_BACKUP_DIR))
        self.lbl_dir.setStyleSheet("color:#0055aa;font-size:8pt;")
        self.lbl_dir.setWordWrap(True)
        ag.addWidget(self.lbl_dir, 2, 1)

        btn_dir = QPushButton("Değiştir")
        btn_dir.setObjectName("secondary")
        btn_dir.setMinimumHeight(34)
        btn_dir.clicked.connect(self._pick_dir)
        ag.addWidget(btn_dir, 2, 2)

        info = QLabel(
            "💡 Sessizce arka planda çalışır · En fazla 20 yedek tutulur (eskiler silinir)\n"
            f"   Varsayılan klasör: {_DEFAULT_BACKUP_DIR}"
        )
        info.setStyleSheet("color:#666;font-size:8pt;")
        ag.addWidget(info, 3, 0, 1, 3)

        r2 = QHBoxLayout()
        btn_sv = QPushButton("Kaydet")
        btn_sv.setObjectName("secondary")
        btn_sv.setMinimumHeight(34)
        btn_sv.clicked.connect(self._save_auto)
        btn_test = QPushButton("Şimdi Test Et")
        btn_test.setObjectName("secondary")
        btn_test.setMinimumHeight(34)
        btn_test.clicked.connect(self._test_backup)
        btn_test.setToolTip("Otomatik yedeklemeyi şimdi tetikle")
        r2.addWidget(btn_sv)
        r2.addWidget(btn_test)
        r2.addStretch()
        ag.addLayout(r2, 4, 0, 1, 3)

        layout.addWidget(aut)
        layout.addStretch()
        return w

    # ── Sekme 2: Geri Yükleme ────────────────────────────────────────────────

    def _tab_restore(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(14)

        warn = QLabel(
            "⚠️  GERİ YÜKLEME İŞLEMİ MEVCUT TÜM VERİLERİN ÜZERİNE YAZAR!\n\n"
            "Bu işlemi yapmadan önce güncel bir yedek almanızı kesinlikle öneririz.\n"
            "Yedekten geri yükleme sırasında hata oluşursa orijinal veriler korunur."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(
            "background:#fff3cd;border:1px solid #ffc107;border-radius:6px;"
            "padding:12px;color:#856404;font-size:9pt;"
        )
        layout.addWidget(warn)

        info_box = QGroupBox("Yedek Dosyası Seç")
        il = QVBoxLayout(info_box)
        il.setContentsMargins(14, 12, 14, 12)
        il.setSpacing(8)
        il.addWidget(QLabel(
            "Daha önce oluşturduğunuz .zip yedek dosyasını seçin.\n"
            "Program otomatik olarak geri yükleme yapacaktır.\n\n"
            "Desteklenen format: backup_YYYY_MM_DD_HHMMSS.zip"
        ))
        r = QHBoxLayout()
        btn_rest = QPushButton("Yedek Seç ve Geri Yükle")
        btn_rest.setObjectName("secondary")
        btn_rest.setMinimumHeight(38)
        btn_rest.clicked.connect(self._restore)
        r.addWidget(btn_rest)
        r.addStretch()
        il.addLayout(r)
        layout.addWidget(info_box)

        layout.addStretch()
        return w

    # ── İşlemler ─────────────────────────────────────────────────────────────

    def _manual(self):
        d = QFileDialog.getExistingDirectory(
            self, "Yedek Klasörü Seç", str(_DEFAULT_BACKUP_DIR)
        )
        if not d:
            return
        try:
            p = create_backup(d)
            self._meta["last_backup"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            _save_meta(self._meta)
            self.lbl_last.setText(f"Son yedek: {self._meta['last_backup']}")
            QMessageBox.information(
                self, "✅ Yedekleme Tamamlandı",
                f"Yedek oluşturuldu:\n{p}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yedekleme başarısız:\n{e}")

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Otomatik Yedek Klasörü", str(_DEFAULT_BACKUP_DIR)
        )
        if d:
            self._meta["auto_backup_dir"] = d
            self.lbl_dir.setText(d)

    def _auto_toggle(self, state):
        enabled = bool(state)
        if enabled and not self._meta.get("auto_backup_dir"):
            d = QFileDialog.getExistingDirectory(
                self, "Otomatik Yedek Klasörü", str(_DEFAULT_BACKUP_DIR)
            )
            if d:
                self._meta["auto_backup_dir"] = d
                self.lbl_dir.setText(d)
            else:
                self.chk_auto.setChecked(False)

    def _save_auto(self):
        iv_map = {0: 15, 1: 30, 2: 60, 3: 120}
        self._meta["auto_enabled"]  = self.chk_auto.isChecked()
        self._meta["auto_interval"] = iv_map.get(self.iv_combo.currentIndex(), 30)
        if not self._meta.get("auto_backup_dir"):
            self._meta["auto_backup_dir"] = str(_DEFAULT_BACKUP_DIR)
            self.lbl_dir.setText(str(_DEFAULT_BACKUP_DIR))
        _save_meta(self._meta)
        self.settings_changed.emit()
        QMessageBox.information(
            self, "Kaydedildi",
            f"✅ Otomatik yedekleme ayarlandı\n"
            f"Aralık: {self.iv_combo.currentText()}\n"
            f"Klasör: {self._meta.get('auto_backup_dir', '—')}"
        )

    def _test_backup(self):
        d = self._meta.get("auto_backup_dir", str(_DEFAULT_BACKUP_DIR))
        if not d:
            d = str(_DEFAULT_BACKUP_DIR)
        try:
            p = create_backup(d)
            self._meta["last_backup"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            _save_meta(self._meta)
            self.lbl_last.setText(f"Son yedek: {self._meta['last_backup']}")
            QMessageBox.information(
                self, "✅ Test Başarılı",
                f"Otomatik yedekleme çalışıyor!\nOluşturulan dosya:\n{p}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Test Başarısız", f"❌ Hata:\n{e}")

    def _restore(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Yedek Dosyası Seç", str(_DEFAULT_BACKUP_DIR),
            "Yedek Dosyaları (backup_*.zip);;ZIP (*.zip)"
        )
        if not path:
            return
        c = QMessageBox.warning(
            self, "⚠️ Onay Gerekli",
            f"Bu işlem mevcut verilerin üzerine yazacaktır. Devam etmek istiyor musunuz?\n\n"
            f"Yedek: {Path(path).name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if c != QMessageBox.StandardButton.Yes:
            return
        try:
            restore_backup(path)
            QMessageBox.information(
                self, "✅ Geri Yükleme Tamamlandı",
                "Veriler başarıyla geri yüklendi.\nProgramı yeniden başlatmanızı öneririz."
            )
        except Exception as e:
            QMessageBox.critical(self, "❌ Geri Yükleme Hatası", f"Başarısız:\n{e}")
