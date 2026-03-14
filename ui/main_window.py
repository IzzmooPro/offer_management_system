"""Ana pencere — sidebar kart tasarımı, üst bar tema butonu, yedekleme servisi."""
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction, QCloseEvent, QKeySequence, QShortcut

logger = logging.getLogger("main_window")

# Sidebar menü kartları — (başlık, sayfa_idx)
NAV_CARDS = [
    ("Yeni Teklif",  4),
    ("Teklifler",    0),
    ("Müşteriler",   2),
    ("Ürünler",      1),
    ("Ayarlar",      5),
]


def _sidebar_text_color():
    from ui.theme_manager import get_theme
    t = get_theme()
    return t["text_sidebar"] if t["name"] == "light" else "white"


class NavCard(QPushButton):
    """Sidebar için navigasyon butonu."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title   = title
        self._checked = False
        self.setCheckable(True)
        self.setFixedHeight(48)
        self.setObjectName("nav_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_inner()

    def _build_inner(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 10, 0)
        layout.setSpacing(0)
        self._title_lbl = QLabel(self._title)
        self._title_lbl.setStyleSheet(
            "font-size:10pt;font-weight:600;background:transparent;")
        layout.addWidget(self._title_lbl)
        layout.addStretch()

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._checked = checked
        self._apply_state()

    def _apply_state(self):
        from ui.theme_manager import get_theme
        t = get_theme()
        if self._checked:
            color = "#ffffff"
        else:
            color = "#b0bcd0" if t["name"] == "dark" else t["text_sidebar"]
        self._title_lbl.setStyleSheet(
            f"color:{color};font-size:10pt;font-weight:600;background:transparent;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teklif Yönetim Sistemi")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._help_dialog = None   # F1 toggle için referans

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        body.addWidget(self.stack)
        root.addLayout(body)

        self._build_menubar()
        self._load_pages()
        self._start_backup_service()
        self._apply_theme()

        # Arka planda güncelleme kontrolü başlat (sessiz)
        self._start_update_check()

    # ── Kapatma olayı ────────────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent):
        """Program kapanırken otomatik yedek al."""
        try:
            self._backup_svc.trigger_now(reason="kapanma")
            logger.info("Kapanma yedeği alındı.")
        except Exception as e:
            logger.warning("Kapanma yedeği alınamadı: %s", e)
        event.accept()

    # ── Menü çubuğu ──────────────────────────────────────────────────────────

    def _build_menubar(self):
        mb = self.menuBar()
        mb.setNativeMenuBar(False)
        mb.setMouseTracking(True)

        tools_menu = mb.addMenu("Araçlar")

        act_excel = QAction("Excel'den İçe Aktar...", self)
        act_excel.triggered.connect(self._open_excel_import)
        tools_menu.addAction(act_excel)

        tools_menu.addSeparator()

        act_backup = QAction("Yedekle / Geri Yükle...\tCtrl+B", self)
        act_backup.setShortcut("Ctrl+B")
        act_backup.triggered.connect(self._open_backup)
        tools_menu.addAction(act_backup)

        tools_menu.addSeparator()

        act_theme = QAction("Tema Değiştir\tCtrl+T", self)
        act_theme.setShortcut("Ctrl+T")
        act_theme.triggered.connect(self._toggle_theme)
        tools_menu.addAction(act_theme)

        help_menu = mb.addMenu("Yardım")

        act_how = QAction("Nasıl Kullanılır?", self)
        act_how.triggered.connect(self._toggle_how_to_use)
        help_menu.addAction(act_how)

        # F1 uygulama genelinde çalışsın (dialog açıkken de tetiklensin)
        f1_shortcut = QShortcut(QKeySequence("F1"), self)
        f1_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        f1_shortcut.activated.connect(self._toggle_how_to_use)

        help_menu.addSeparator()

        act_about = QAction("Hakkında\tCtrl+H", self)
        act_about.setShortcut("Ctrl+H")
        act_about.triggered.connect(self._open_about)
        help_menu.addAction(act_about)

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Başlık
        header = QWidget()
        header.setObjectName("sidebar_header")
        h = QVBoxLayout(header)
        h.setContentsMargins(0, 16, 0, 16)
        t = QLabel("Teklif Yönetim")
        self._sidebar_title_lbl = t
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(
            f"color:{_sidebar_text_color()};font-size:11pt;"
            "font-weight:bold;background:transparent;"
        )
        h.addWidget(t)
        layout.addWidget(header)

        # Navigasyon kartları
        self._btn_map: dict[int, NavCard] = {}
        for title, idx in NAV_CARDS:
            card = NavCard(title)
            card.clicked.connect(lambda checked, i=idx: self._navigate(i))
            layout.addWidget(card)
            self._btn_map[idx] = card

        layout.addStretch()
        return sidebar

    # ── Sayfalar ─────────────────────────────────────────────────────────────

    def _load_pages(self):
        from ui.dashboard_page    import DashboardPage
        from ui.products_page     import ProductsPage
        from ui.customers_page    import CustomersPage
        from ui.create_offer_page import CreateOfferPage
        from ui.settings_page     import SettingsPage

        self.pages = {
            0: DashboardPage(),
            1: ProductsPage(),
            2: CustomersPage(),
            4: CreateOfferPage(),
            5: SettingsPage(),
        }
        self.pages[0].edit_offer_requested.connect(self._open_edit_offer)
        self.pages[4].offer_saved.connect(self._on_offer_saved)

        for page in self.pages.values():
            self.stack.addWidget(page)
        self._navigate(0)

    def _navigate(self, index: int):
        for idx, card in self._btn_map.items():
            card.setChecked(idx == index)
        if index in self.pages:
            self.stack.setCurrentWidget(self.pages[index])
            page = self.pages[index]
            if hasattr(page, "on_enter"):
                page.on_enter()

    def _open_edit_offer(self, offer_id: int):
        self.pages[4].load_offer(offer_id)
        self._navigate(4)

    def _on_offer_saved(self):
        # Teklif kaydedilince yedek al (arka planda)
        try:
            self._backup_svc.trigger_now(reason="teklif kaydı")
        except Exception as e:
            logger.debug("Teklif kaydı yedeği alınamadı: %s", e)
        self._navigate(0)

    # ── Araçlar ──────────────────────────────────────────────────────────────

    def _open_excel_import(self):
        from ui.excel_import import ExcelImportDialog
        ExcelImportDialog(self).exec()
        cur = self.stack.currentWidget()
        if hasattr(cur, "on_enter"):
            cur.on_enter()

    def _open_backup(self):
        from ui.backup_manager import BackupDialog
        dlg = BackupDialog(self)
        dlg.settings_changed.connect(self._backup_svc.reload)
        dlg.exec()

    def _toggle_how_to_use(self):
        """F1: yardım penceresi açık ise kapat, kapalı ise aç (toggle)."""
        if self._help_dialog is not None and self._help_dialog.isVisible():
            self._help_dialog.close()
            self._help_dialog = None
        else:
            from ui.help_dialogs import HowToUseDialog
            self._help_dialog = HowToUseDialog(self)
            self._help_dialog.finished.connect(lambda _: setattr(self, "_help_dialog", None))
            self._help_dialog.show()

    def _open_about(self):
        from ui.help_dialogs import AboutDialog
        AboutDialog(self).exec()

    # ── Yedekleme servisi ─────────────────────────────────────────────────────

    def _start_backup_service(self):
        from ui.backup_manager import AutoBackupService
        self._backup_svc = AutoBackupService(self)
        self._backup_svc.backup_done.connect(
            lambda p: logger.info("Otomatik yedek: %s", p))
        self._backup_svc.backup_failed.connect(
            lambda e: logger.warning("Otomatik yedek başarısız: %s", e))

    # ── Güncelleme kontrolü ──────────────────────────────────────────────────

    def _start_update_check(self):
        """Program açılınca arka planda güncelleme kontrolü başlatır."""
        try:
            from ui.updater import start_startup_check
            self._update_checker = start_startup_check(self)
        except Exception as e:
            logger.debug("Güncelleme kontrolü başlatılamadı: %s", e)

    # ── Tema ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        from ui.theme_manager import toggle_theme, get_theme
        toggle_theme()
        self._apply_theme()
        for idx, card in self._btn_map.items():
            card._apply_state()
        if hasattr(self, "_sidebar_title_lbl"):
            self._sidebar_title_lbl.setStyleSheet(
                f"color:{_sidebar_text_color()};font-size:11pt;"
                "font-weight:bold;background:transparent;"
            )
        logger.info("Tema değiştirildi: %s", get_theme()["name"])

    def _apply_theme(self):
        from ui.theme_manager import build_stylesheet, get_theme
        self.setStyleSheet(build_stylesheet(get_theme()))
