"""
Ayarlar sayfası — sekmeli düzen: Şirket | Yetkililer | Logo & İmza
"""
import shutil, logging
from pathlib import Path
from ui._section_card import make_section_card
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit,
    QFileDialog, QMessageBox, QScrollArea, QFrame,
    QTabWidget, QPlainTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

logger = logging.getLogger("settings")
from app_paths import (
    LOGO_PATH,
    SIG1_PATH,
    SIG2_PATH,
    CFG_PATH,
)


def load_company_config() -> dict:
    d = {
        "name": "", "address": "", "tel": "", "fax": "", "mail": "", "web": "",
        "offer_prefix": "SNS",
        "sales_person1_name": "", "sales_person1_title": "", "sales_person1_email": "",
        "sales_person2_name": "", "sales_person2_title": "", "sales_person2_email": "",
        # PDF sabit metinler (PDF'deki görünüm sırasına göre)
        "pdf_giris_metni": "Firmamızdan talep etmiş olduğunuz malzemeler ile ilgili teklifimizi tetkiklerinize sunar, değerli siparişlerinizi bekleriz.",
        "pdf_iskonto":     "Firmanıza iskonto uygulanmış olup, fiyatlar NET tir.",
        "pdf_teslim_yeri": "Büromuz veya Kargo bedeli karşı taraf ödemeli şartiyla Kargo şirketi ile.",
        "pdf_kur_notu":    "•Verilen döviz fiyatlar Fatura tarihindeki T.C.M.B. Efektif Satış Kuru üzerinden TL.'sına çevrilecektir.",
        "pdf_kdv_notu":    "•Fiyatlarımıza K.D.V. dahil değildir.",
        "pdf_onay_metni":  "Yukarıda teklif edilen malzemeleri belirttiğiniz özellik ve şartlarda satın almayı kabul ediyoruz.",
        "pdf_teslim_notu": "NOT : Teklifimiz de belirtilen teslim süreleri teklifin yazıldığı andaki güncel stoklara göre verilmiştir. Sipariş anında stok durumuna göre teslim süreleri değişebilir.",
        "pdf_iptal_notu":  "Siparişlerin yazılı olarak maille veya fax yoluyla geçilmesine müteakip siparişlerin iptali ve ürünlerin iadesi kabul edilmemektedir.",
    }
    if CFG_PATH.exists():
        try:
            for line in CFG_PATH.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    d[k.strip()] = v.strip()
        except Exception:
            pass
    return d


def save_company_config(data: dict):
    CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CFG_PATH.write_text("\n".join(f"{k}={v}" for k, v in data.items()), encoding="utf-8")


def _inp(ph="", tip="", w=None) -> QLineEdit:
    le = QLineEdit()
    le.setPlaceholderText(ph)
    le.setMinimumHeight(34)
    if tip: le.setToolTip(tip)
    if w:   le.setFixedWidth(w)
    return le


def _lbl(text: str) -> QLabel:
    l = QLabel(text)
    l.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    l.setMinimumWidth(90)
    return l


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._loaded_prefix = "SNS"
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Başlık çubuğu ─────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setObjectName("toolbar")
        hdr.setFixedHeight(64)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(24, 12, 32, 12)
        t = QLabel("Ayarlar")
        hl.addWidget(t); hl.addStretch()
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.setObjectName("primary")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setToolTip("Şirket bilgilerini ve teklif önekini kaydeder.\nLogo ve imza görselleri yüklenince otomatik kaydedilir.")
        self.save_btn.clicked.connect(self._save)
        hl.addWidget(self.save_btn)
        root.addWidget(hdr)

        # ── Sekmeler ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs)

        # Sekme sırası: Şirket → Yetkililer → Logo & İmza → PDF Ayarları
        self.tabs.addTab(self._tab_company(),   "Şirket")
        self.tabs.addTab(self._tab_persons(),   "Yetkililer")
        self.tabs.addTab(self._tab_visuals(),   "Logo ve İmza")
        self.tabs.addTab(self._tab_pdf_texts(), "PDF Ayarları")

    # ══════════════════════════════════════════════════════════════════════
    # SEKME 1 — Şirket Bilgileri
    # ══════════════════════════════════════════════════════════════════════
    def _tab_company(self) -> QWidget:
        page, lay = self._scrolled_page()

        box, g = make_section_card("Şirket Bilgileri")
        g.setColumnStretch(1, 1); g.setColumnStretch(3, 1)

        self.f_name    = _inp("Şirketin tam unvanı")
        self.f_address = _inp("Açık adres")
        self.f_tel     = _inp("0 xxx xxx xx xx")
        self.f_fax     = _inp("0 xxx xxx xx xx")
        self.f_mail    = _inp("info@sirket.com.tr")
        self.f_web     = _inp("www.sirket.com.tr")

        g.addWidget(_lbl("Şirket Adı:"),  0, 0); g.addWidget(self.f_name,    0, 1, 1, 3)
        g.addWidget(_lbl("Adres:"),        1, 0); g.addWidget(self.f_address,  1, 1, 1, 3)
        g.addWidget(_lbl("Tel:"),          2, 0); g.addWidget(self.f_tel,      2, 1)
        g.addWidget(_lbl("Fax:"),          2, 2); g.addWidget(self.f_fax,      2, 3)
        g.addWidget(_lbl("E-Posta:"),      3, 0); g.addWidget(self.f_mail,     3, 1)
        g.addWidget(_lbl("Web:"),          3, 2); g.addWidget(self.f_web,      3, 3)
        lay.addWidget(box)

        no_box, ng = make_section_card("Teklif Numarası")
        self.f_prefix = _inp("SNS",
            "Teklif numarası başı — Örnek: SNS → SNS-000001", w=160)
        note = QLabel("Format:  PREFIX-000001")
        note.setStyleSheet("color:#888;")
        ng.addWidget(_lbl("Prefix:"), 0, 0)
        ng.addWidget(self.f_prefix,   0, 1)
        ng.addWidget(note,            1, 1)
        lay.addWidget(no_box)
        lay.addStretch()
        return page

    # ══════════════════════════════════════════════════════════════════════
    # SEKME 2 — Yetkili Bilgileri
    # ══════════════════════════════════════════════════════════════════════
    def _tab_persons(self) -> QWidget:
        page, lay = self._scrolled_page()

        for attrs, title in [
            (("f_s1_name", "f_s1_title", "f_s1_email"), "1. Yetkili"),
            (("f_s2_name", "f_s2_title", "f_s2_email"), "2. Yetkili"),
        ]:
            box, g = make_section_card(title)
            g.setColumnStretch(1, 1); g.setColumnStretch(3, 1)
            name_f  = _inp("Ad Soyad")
            title_f = _inp("Unvan / Görev")
            email_f = _inp("ad.soyad@sirket.com.tr")
            setattr(self, attrs[0], name_f)
            setattr(self, attrs[1], title_f)
            setattr(self, attrs[2], email_f)
            g.addWidget(_lbl("Ad Soyad:"), 0, 0); g.addWidget(name_f,  0, 1)
            g.addWidget(_lbl("Unvan:"),    0, 2); g.addWidget(title_f, 0, 3)
            g.addWidget(_lbl("E-Posta:"),  1, 0); g.addWidget(email_f, 1, 1, 1, 3)
            lay.addWidget(box)

        note = QLabel("Bu bilgiler PDF teklifin imza alanında görünür.")
        note.setStyleSheet("color:#888;")
        lay.addWidget(note)
        lay.addStretch()
        return page

    # ══════════════════════════════════════════════════════════════════════
    # SEKME 3 — Logo & İmza Görselleri
    # ══════════════════════════════════════════════════════════════════════
    def _tab_visuals(self) -> QWidget:
        page, lay = self._scrolled_page()

        # ── LOGO KARTI ────────────────────────────────────────────────────
        logo_card = QFrame()
        logo_card.setObjectName("section_card")
        logo_vbox = QVBoxLayout(logo_card)
        logo_vbox.setContentsMargins(0, 0, 0, 0)
        logo_vbox.setSpacing(0)

        logo_hdr = QFrame(logo_card)
        logo_hdr.setFixedHeight(44)
        logo_hdr.setStyleSheet("background:transparent;")
        logo_hl = QHBoxLayout(logo_hdr)
        logo_hl.setContentsMargins(16, 0, 16, 0)
        logo_title = QLabel("Logo  (PDF sol üst köşe)")
        logo_title.setObjectName("section_card_title")
        logo_title.setStyleSheet("font-size:10pt;font-weight:700;background:transparent;")
        logo_hl.addWidget(logo_title)
        logo_hl.addStretch()
        logo_vbox.addWidget(logo_hdr)

        logo_sep = QFrame(logo_card)
        logo_sep.setObjectName("section_divider")
        logo_sep.setFrameShape(QFrame.Shape.HLine)
        logo_sep.setFixedHeight(2)
        logo_vbox.addWidget(logo_sep)

        logo_body = QFrame(logo_card)
        logo_body.setStyleSheet("background:transparent;")
        logo_row = QHBoxLayout(logo_body)
        logo_row.setContentsMargins(16, 16, 16, 16)
        logo_row.setSpacing(24)

        self.logo_preview = self._make_preview("Logo Yok\n(Yükleyin)", 240, 110)
        logo_row.addWidget(self.logo_preview)

        logo_btn_frame = QFrame(logo_body)
        logo_btn_frame.setStyleSheet("background:transparent;")
        logo_btn_col = QVBoxLayout(logo_btn_frame)
        logo_btn_col.setContentsMargins(0, 0, 0, 0)
        logo_btn_col.setSpacing(8)
        logo_btn_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b_logo = QPushButton(logo_btn_frame)
        self.b_logo.setObjectName("secondary")
        self.b_logo.setFixedSize(120, 34)
        self._sync_img_btn(self.b_logo, LOGO_PATH)
        logo_hint = QLabel("PNG / JPG\nÖnerilen: 230 × 50 px", logo_btn_frame)
        logo_hint.setStyleSheet("color:#999;font-size:9pt;")

        logo_btn_col.addWidget(self.b_logo)
        logo_btn_col.addSpacing(4)
        logo_btn_col.addWidget(logo_hint)

        self.b_logo.clicked.connect(lambda: self._toggle_img(
            LOGO_PATH, self.logo_preview, "Logo Yok\n(Yükleyin)", self.b_logo))

        logo_row.addWidget(logo_btn_frame)
        logo_row.addStretch()
        logo_vbox.addWidget(logo_body)
        lay.addWidget(logo_card)

        # ── İMZA KARTI ────────────────────────────────────────────────────
        sig_card = QFrame()
        sig_card.setObjectName("section_card")
        sig_vbox = QVBoxLayout(sig_card)
        sig_vbox.setContentsMargins(0, 0, 0, 0)
        sig_vbox.setSpacing(0)

        sig_hdr = QFrame(sig_card)
        sig_hdr.setFixedHeight(44)
        sig_hdr.setStyleSheet("background:transparent;")
        sig_hl = QHBoxLayout(sig_hdr)
        sig_hl.setContentsMargins(16, 0, 16, 0)
        sig_title = QLabel("İmza Görselleri  (PDF imza alanı, önerilen: 200 × 80 px)")
        sig_title.setObjectName("section_card_title")
        sig_title.setStyleSheet("font-size:10pt;font-weight:700;background:transparent;")
        sig_hl.addWidget(sig_title)
        sig_hl.addStretch()
        sig_vbox.addWidget(sig_hdr)

        sig_sep = QFrame(sig_card)
        sig_sep.setObjectName("section_divider")
        sig_sep.setFrameShape(QFrame.Shape.HLine)
        sig_sep.setFixedHeight(2)
        sig_vbox.addWidget(sig_sep)

        sig_body = QFrame(sig_card)
        sig_body.setStyleSheet("background:transparent;")
        sig_row = QHBoxLayout(sig_body)
        sig_row.setContentsMargins(16, 16, 16, 16)
        sig_row.setSpacing(40)

        for path, attr, btn_attr, placeholder in [
            (SIG1_PATH, "sig1_preview", "b_sig1", "İmza 1 Yok"),
            (SIG2_PATH, "sig2_preview", "b_sig2", "İmza 2 Yok"),
        ]:
            cell_frame = QFrame(sig_body)
            cell_frame.setStyleSheet("background:transparent;")
            cell_col = QVBoxLayout(cell_frame)
            cell_col.setContentsMargins(0, 0, 0, 0)
            cell_col.setSpacing(8)

            prev = self._make_preview(placeholder, 240, 110)
            setattr(self, attr, prev)
            cell_col.addWidget(prev)

            btn_frame = QFrame(cell_frame)
            btn_frame.setStyleSheet("background:transparent;")
            btn_row = QHBoxLayout(btn_frame)
            btn_row.setContentsMargins(0, 0, 0, 0)
            btn_row.setSpacing(8)

            b = QPushButton(btn_frame)
            b.setObjectName("secondary")
            b.setFixedSize(120, 34)
            self._sync_img_btn(b, path)
            setattr(self, btn_attr, b)
            b.clicked.connect(lambda _, p=path, pv=prev, d=placeholder, bt=b:
                              self._toggle_img(p, pv, d, bt))
            btn_row.addWidget(b)
            btn_row.addStretch()

            cell_col.addWidget(btn_frame)
            sig_row.addWidget(cell_frame)

        sig_row.addStretch()
        sig_vbox.addWidget(sig_body)
        lay.addWidget(sig_card)

        lay.addStretch()
        return page

    # ══════════════════════════════════════════════════════════════════════
    # SEKME 4 — PDF Ayarları (sabit metinler)
    # ══════════════════════════════════════════════════════════════════════
    def _tab_pdf_texts(self) -> QWidget:
        page, lay = self._scrolled_page()

        # PDF'deki görünüm sırasına göre: yukarıdan aşağıya
        fields = [
            ("pdf_giris_metni",  "① Giriş Metni",
             "Müşteri bilgilerinden hemen sonra görünen açılış paragrafı."),
            ("pdf_iskonto",      "② İskonto  (Şartlar tablosu)",
             "Ürün tablosunun üstündeki şartlar bölümü — iskonto satırı."),
            ("pdf_teslim_yeri",  "③ Teslim Yeri  (Şartlar tablosu)",
             "Ürün tablosunun üstündeki şartlar bölümü — teslim yeri satırı."),
            ("pdf_kur_notu",     "④ Döviz Kur Notu  (İmza alanı üstü)",
             "İmza alanı üstünde, döviz kuruna dair uyarı metni."),
            ("pdf_kdv_notu",     "⑤ KDV Notu  (İmza alanı üstü)",
             "İmza alanı üstünde, KDV'ye dair uyarı metni."),
            ("pdf_onay_metni",   "⑥ Müşteri Onay Metni  (İmza alanı altı)",
             "İmza alanı altında, müşterinin onayladığını belirten metin."),
            ("pdf_teslim_notu",  "⑦ Teslim Süresi Notu  (Alt bilgi — kırmızı)",
             "PDF'nin en altındaki kırmızı uyarı notu."),
            ("pdf_iptal_notu",   "⑧ İptal / İade Notu  (Alt bilgi)",
             "PDF'nin en altındaki iptal/iade koşulu metni."),
        ]

        for attr, title, hint in fields:
            box, g = make_section_card(title)
            g.setColumnStretch(0, 1)

            te = QPlainTextEdit()
            te.setMinimumHeight(48)
            te.setMaximumHeight(62)
            te.setPlaceholderText(hint)
            te.setToolTip(hint)
            setattr(self, attr, te)

            hint_lbl = QLabel(hint)
            hint_lbl.setStyleSheet("color:#999;font-size:8pt;")
            hint_lbl.setWordWrap(True)

            g.addWidget(te,       0, 0)
            g.addWidget(hint_lbl, 1, 0)
            lay.addWidget(box)

        note = QLabel("Bu metinler PDF teklifin ilgili bölümlerinde otomatik görünür.\nDeğişiklikler kaydedilince sonraki PDF'lere yansır.")
        note.setStyleSheet("color:#888;font-size:9pt;")
        note.setWordWrap(True)
        lay.addWidget(note)
        lay.addStretch()
        return page

    # ── Yardımcılar ──────────────────────────────────────────────────────

    def _scrolled_page(self):
        """Scroll içine sarılmış sayfa + içerik layout'u döner."""
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)
        w = QWidget(); scroll.setWidget(w)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 20, 16, 16); lay.setSpacing(20)
        return page, lay

    def _make_preview(self, text, w, h) -> QLabel:
        lbl = QLabel(text)
        lbl.setFixedSize(w, h)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "border:1px dashed #bbb;border-radius:6px;"
            "color:#999;background:#fafafa;")
        return lbl

    def _upload(self, dest: Path, preview: QLabel, placeholder: str):
        path, _ = QFileDialog.getOpenFileName(
            self, "Görsel Seç", "", "Resim (*.png *.jpg *.jpeg *.bmp)")
        if not path: return
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, str(dest))
            self._set_preview(preview, dest)
            QMessageBox.information(self, "Yüklendi", "Görsel başarıyla yüklendi.")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Yüklenemedi:\n{e}")

    def _remove(self, dest: Path, preview: QLabel, placeholder: str):
        try:
            if dest.exists():
                dest.unlink()
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Görsel kaldırılamadı:\n{e}")
            return
        preview.setPixmap(QPixmap())
        preview.setText(placeholder)
        QMessageBox.information(self, "Kaldırıldı", "Görsel kaldırıldı.")

    def _toggle_img(self, dest: Path, preview: QLabel, placeholder: str, btn: QPushButton):
        """Dosya varsa kaldır, yoksa yükle; ardından butonu güncelle."""
        if dest.exists():
            self._remove(dest, preview, placeholder)
        else:
            self._upload(dest, preview, placeholder)
        self._sync_img_btn(btn, dest)

    def _sync_img_btn(self, btn: QPushButton, dest: Path):
        """Dosya durumuna göre buton metnini günceller."""
        btn.setText("Kaldır" if dest.exists() else "Yükle")

    def _set_preview(self, lbl: QLabel, path: Path):
        if path.exists():
            pix = QPixmap(str(path))
            lbl.setPixmap(pix.scaled(
                lbl.width() - 4, lbl.height() - 4,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
            lbl.setText("")
        else:
            lbl.setPixmap(QPixmap())

    def _refresh_previews(self):
        self._set_preview(self.logo_preview, LOGO_PATH)
        self._set_preview(self.sig1_preview, SIG1_PATH)
        self._set_preview(self.sig2_preview, SIG2_PATH)
        if not LOGO_PATH.exists(): self.logo_preview.setText("Logo Yok\n(Yükleyin)")
        if not SIG1_PATH.exists(): self.sig1_preview.setText("İmza 1 Yok")
        if not SIG2_PATH.exists(): self.sig2_preview.setText("İmza 2 Yok")
        self._sync_img_btn(self.b_logo, LOGO_PATH)
        self._sync_img_btn(self.b_sig1, SIG1_PATH)
        self._sync_img_btn(self.b_sig2, SIG2_PATH)

    # ── Veri ─────────────────────────────────────────────────────────────

    def _load(self):
        cfg = load_company_config()
        self._loaded_prefix = cfg.get("offer_prefix", "SNS")
        self.f_name.setText(cfg.get("name", ""))
        self.f_address.setText(cfg.get("address", ""))
        self.f_tel.setText(cfg.get("tel", ""))
        self.f_fax.setText(cfg.get("fax", ""))
        self.f_mail.setText(cfg.get("mail", ""))
        self.f_web.setText(cfg.get("web", ""))
        self.f_prefix.setText(cfg.get("offer_prefix", "SNS"))
        self.f_s1_name.setText(cfg.get("sales_person1_name", ""))
        self.f_s1_title.setText(cfg.get("sales_person1_title", ""))
        self.f_s1_email.setText(cfg.get("sales_person1_email", ""))
        self.f_s2_name.setText(cfg.get("sales_person2_name", ""))
        self.f_s2_title.setText(cfg.get("sales_person2_title", ""))
        self.f_s2_email.setText(cfg.get("sales_person2_email", ""))
        # PDF metinleri (PDF sırasına göre)
        for key in ("pdf_giris_metni", "pdf_iskonto", "pdf_teslim_yeri",
                    "pdf_kur_notu", "pdf_kdv_notu", "pdf_onay_metni",
                    "pdf_teslim_notu", "pdf_iptal_notu"):
            getattr(self, key).setPlainText(cfg.get(key, ""))
        self._refresh_previews()

    def _save(self):
        new_prefix = self.f_prefix.text().strip() or "SNS"
        save_company_config({
            "name":    self.f_name.text().strip(),
            "address": self.f_address.text().strip(),
            "tel":     self.f_tel.text().strip(),
            "fax":     self.f_fax.text().strip(),
            "mail":    self.f_mail.text().strip(),
            "web":     self.f_web.text().strip(),
            "offer_prefix": new_prefix,
            "sales_person1_name":  self.f_s1_name.text().strip(),
            "sales_person1_title": self.f_s1_title.text().strip(),
            "sales_person1_email": self.f_s1_email.text().strip(),
            "sales_person2_name":  self.f_s2_name.text().strip(),
            "sales_person2_title": self.f_s2_title.text().strip(),
            "sales_person2_email": self.f_s2_email.text().strip(),
            # PDF sabit metinler (PDF sırasına göre)
            "pdf_giris_metni": self.pdf_giris_metni.toPlainText().strip(),
            "pdf_iskonto":     self.pdf_iskonto.toPlainText().strip(),
            "pdf_teslim_yeri": self.pdf_teslim_yeri.toPlainText().strip(),
            "pdf_kur_notu":    self.pdf_kur_notu.toPlainText().strip(),
            "pdf_kdv_notu":    self.pdf_kdv_notu.toPlainText().strip(),
            "pdf_onay_metni":  self.pdf_onay_metni.toPlainText().strip(),
            "pdf_teslim_notu": self.pdf_teslim_notu.toPlainText().strip(),
            "pdf_iptal_notu":  self.pdf_iptal_notu.toPlainText().strip(),
        })
        msg = "Ayarlar kaydedildi.\nBundan sonra oluşturulan PDF tekliflere yansır."
        if self._loaded_prefix and self._loaded_prefix != new_prefix:
            msg += (f"\n\n⚠️  Teklif Öneki '{self._loaded_prefix}' → '{new_prefix}' olarak değiştirildi."
                    "\nMevcut tekliflerin numaraları değişmez, yalnızca yeni tekliflere uygulanır.")
        self._loaded_prefix = new_prefix
        QMessageBox.information(self, "Kaydedildi", msg)

    def on_enter(self):
        # Sadece görselleri yenile — yazılan ama kaydedilmemiş alanları sıfırlama
        self._refresh_previews()