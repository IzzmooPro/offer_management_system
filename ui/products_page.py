"""Ürün yönetim sayfası."""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidgetItem, QLineEdit, QDialog,
    QFormLayout, QComboBox, QDoubleSpinBox, QMessageBox,
    QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QTimer
from services.product_service import ProductService
from models.product import Product
from ui._resizable_table import ResizableTable

logger = logging.getLogger("products")


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.setWindowTitle("Ürün Ekle" if not product else "Ürün Düzenle")
        self.setMinimumWidth(480)
        self.product  = product          # None = yeni ürün
        self._svc     = ProductService()
        self._build_ui()
        if product:
            self._fill(product)

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(22, 20, 22, 20)

        title = QLabel(self.windowTitle())
        title.setStyleSheet("font-size:11pt;font-weight:700;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # ── Ürün Kodu ──
        self.code = QLineEdit(); self.code.setMinimumHeight(34)
        self.code.setPlaceholderText("örn. MTR-001")

        # Duplicate uyarısı — kod alanının altında
        self.code_warn = QLabel("")
        self.code_warn.setStyleSheet(
            "color: #e94560; font-size: 8pt; padding: 2px 0; background: transparent;")
        self.code_warn.setVisible(False)

        code_col = QVBoxLayout(); code_col.setSpacing(2)
        code_col.addWidget(self.code)
        code_col.addWidget(self.code_warn)

        code_wrap = QWidget(); code_wrap.setLayout(code_col)
        form.addRow("Ürün Kodu *:", code_wrap)

        # Gerçek zamanlı duplicate kontrolü — 400ms debounce
        self._check_timer = QTimer(self)
        self._check_timer.setSingleShot(True)
        self._check_timer.timeout.connect(self._check_duplicate)
        self.code.textChanged.connect(lambda: self._check_timer.start(400))

        # ── Diğer alanlar ──
        self.name = QLineEdit(); self.name.setMinimumHeight(34)
        self.desc = QTextEdit(); self.desc.setMaximumHeight(70)
        form.addRow("Ürün Adı *:", self.name)
        form.addRow("Açıklama:", self.desc)

        # ── Fiyat ──
        self.price = QDoubleSpinBox()
        self.price.setMaximum(9_999_999)
        self.price.setDecimals(2)
        self.price.setMinimumHeight(36)
        self.price.setGroupSeparatorShown(True)
        self.price.setStepType(QDoubleSpinBox.StepType.AdaptiveDecimalStepType)
        form.addRow("Fiyat:", self.price)

        # ── Para Birimi ──
        self.currency = QComboBox()
        self.currency.addItems(["EUR", "USD", "TL"])
        self.currency.setMinimumHeight(34)
        form.addRow("Para Birimi:", self.currency)

        # ── Stok — tam sayıysa ondalık gösterme ──
        self.stock = QDoubleSpinBox()
        self.stock.setMaximum(999_999)
        self.stock.setMinimumHeight(36)
        self.stock.setDecimals(0)          # ← ondalık basamak kaldırıldı
        self.stock.setSingleStep(1)
        self.stock.setStepType(QDoubleSpinBox.StepType.DefaultStepType)
        form.addRow("Stok:", self.stock)

        # ── Birim ──
        self.unit = QComboBox()
        self.unit.addItems(["Adet","Kg","Metre","Litre","Paket","Kutu","Set","Takım"])
        self.unit.setEditable(True)
        self.unit.setMinimumHeight(34)
        self.unit.setMinimumWidth(120)
        form.addRow("Birim:", self.unit)

        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Kaydet");  ok.setObjectName("primary");   ok.clicked.connect(self._save)
        no = QPushButton("İptal");   no.setObjectName("secondary"); no.clicked.connect(self.reject)
        btns.addWidget(no); btns.addWidget(ok)
        layout.addLayout(btns)

    # ── Doldur ───────────────────────────────────────────────────────────────

    def _fill(self, p):
        self.code.setText(p.product_code)
        self.name.setText(p.product_name)
        self.desc.setPlainText(p.description or "")
        self.price.setValue(p.price)
        idx = self.currency.findText(p.currency)
        if idx >= 0: self.currency.setCurrentIndex(idx)
        self.stock.setValue(int(p.stock) if p.stock == int(p.stock) else p.stock)
        u = self.unit.findText(p.unit)
        if u >= 0: self.unit.setCurrentIndex(u)
        else: self.unit.setCurrentText(p.unit)

    # ── Duplicate kontrolü ───────────────────────────────────────────────────

    def _check_duplicate(self):
        code = self.code.text().strip().upper()
        if not code:
            self._hide_warn(); return

        # Düzenleme modunda kendi kodunu kontrol etme
        if self.product and self.product.product_code.upper() == code:
            self._hide_warn(); return

        try:
            existing = self._svc.get_by_code(code)
            if existing:
                self.code_warn.setText(
                    f"⚠️  '{existing.product_code}' kodu zaten kayıtlı: {existing.product_name}")
                self.code_warn.setVisible(True)
                # Kod alanını kırmızı border ile işaretle
                self.code.setStyleSheet(
                    "QLineEdit { border: 1.5px solid #e94560; border-radius: 6px; "
                    "padding: 7px 10px; }")
            else:
                self._hide_warn()
        except Exception:
            self._hide_warn()

    def _hide_warn(self):
        self.code_warn.setVisible(False)
        self.code.setStyleSheet("")  # Temaya bırak

    # ── Kaydet ───────────────────────────────────────────────────────────────

    def _save(self):
        if not self.code.text().strip() or not self.name.text().strip():
            QMessageBox.warning(self, "Hata", "Ürün kodu ve adı zorunludur."); return

        # Duplicate son kontrol — hız farkı olabilir
        code = self.code.text().strip().upper()
        if not (self.product and self.product.product_code.upper() == code):
            try:
                existing = self._svc.get_by_code(code)
                if existing:
                    ans = QMessageBox.warning(
                        self, "Aynı Kod Mevcut",
                        f"'{existing.product_code}' kodu zaten kayıtlı:\n"
                        f"Ürün: {existing.product_name}\n\n"
                        f"Yine de kaydetmek istiyor musunuz?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No)
                    if ans != QMessageBox.StandardButton.Yes:
                        return
            except Exception:
                pass

        self.accept()

    def get_product(self) -> Product:
        p = self.product or Product()
        p.product_code = self.code.text().strip()
        p.product_name = self.name.text().strip()
        p.description  = self.desc.toPlainText().strip()
        p.price        = self.price.value()
        p.currency     = self.currency.currentText()
        p.stock        = self.stock.value()
        p.unit         = self.unit.currentText()
        return p


# ── Sayfa ─────────────────────────────────────────────────────────────────────

class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.service   = ProductService()
        self._products = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Ürün Yönetimi")
        title.setStyleSheet("font-size:14pt;font-weight:700;")
        header.addWidget(title); header.addStretch()
        add_btn = QPushButton("+ Yeni Ürün")
        add_btn.setObjectName("primary"); add_btn.clicked.connect(self._add)
        header.addWidget(add_btn)
        layout.addLayout(header)

        toolbar = QFrame(); toolbar.setObjectName("toolbar")
        t = QHBoxLayout(toolbar); t.setContentsMargins(8, 4, 8, 4)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Ürün kodu veya adıyla ara...")
        self.search.textChanged.connect(lambda txt: self._load(txt))
        t.addWidget(self.search)
        for lbl, slot in [("Düzenle", self._edit), ("Sil", self._delete)]:
            b = QPushButton(lbl); b.setObjectName("action_btn")
            b.setMinimumHeight(32); b.clicked.connect(slot)
            t.addWidget(b)
        layout.addWidget(toolbar)

        self.table = ResizableTable()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Ürün Kodu","Ürün Adı","Fiyat","Para Birimi","Stok","Birim","Açıklama"])
        self.table.setup_columns([
            ('interactive', 120),
            ('stretch',     None),
            ('interactive', 130),
            ('interactive', 105),
            ('interactive',  75),
            ('interactive',  85),
            ('stretch',     None),
        ])
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._edit)
        self.table.on_edit   = self._edit
        self.table.on_delete = self._delete
        layout.addWidget(self.table)
        self._load()

    def _load(self, keyword=""):
        logger.debug("Ürünler yükleniyor, anahtar='%s'", keyword)
        try:
            self._products = self.service.search(keyword) if keyword else self.service.get_all()
            self.table.setRowCount(len(self._products))
            for row, p in enumerate(self._products):
                self.table.setItem(row, 0, QTableWidgetItem(p.product_code))
                self.table.setItem(row, 1, QTableWidgetItem(p.product_name))
                pi = QTableWidgetItem(f"{p.price:,.2f}")
                pi.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 2, pi)
                self.table.setItem(row, 3, QTableWidgetItem(p.currency))
                # Stok: tam sayıysa ondalık gösterme
                stock_val = int(p.stock) if p.stock == int(p.stock) else p.stock
                si = QTableWidgetItem(str(stock_val))
                si.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, si)
                self.table.setItem(row, 5, QTableWidgetItem(p.unit))
                self.table.setItem(row, 6, QTableWidgetItem(p.description or ""))
            self.table.resizeColumnToContents(2)
            self.table.resizeColumnToContents(0)
        except Exception as e:
            logger.error("Ürün yükleme hatası: %s", e, exc_info=True)

    def _selected(self):
        row = self.table.currentRow()
        return self._products[row] if 0 <= row < len(self._products) else None

    def _add(self):
        dlg = ProductDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self.service.add(dlg.get_product())
                self._load()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Ürün eklenemedi:\n{e}")

    def _edit(self):
        p = self._selected()
        if not p:
            QMessageBox.information(self, "Bilgi", "Lütfen bir ürün seçin."); return
        dlg = ProductDialog(self, p)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self.service.update(dlg.get_product())
                self._load()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Ürün güncellenemedi:\n{e}")

    def _delete(self):
        p = self._selected()
        if not p:
            QMessageBox.information(self, "Bilgi", "Lütfen bir ürün seçin."); return
        if QMessageBox.question(self, "Onay", f"'{p.product_name}' silinsin mi?",
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
           == QMessageBox.StandardButton.Yes:
            try:
                self.service.delete(p.id)
                self._load()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Ürün silinemedi:\n{e}")

    def on_enter(self):
        self._load(self.search.text())
