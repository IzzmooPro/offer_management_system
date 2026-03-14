"""
Excel'den veri içe aktarma.

Desteklenen türler:
  - Müşteri listesi
  - Ürün kataloğu

Şablon sütun isimleri esnek eşleşir (Türkçe/İngilizce, büyük-küçük harf).
openpyxl veya csv kütüphanesi ile çalışır, xlrd gerekmez.
"""
import logging, csv, io
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QProgressBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

logger = logging.getLogger("excel_import")

# Sütun eşleştirme haritaları (olası başlık → alan adı)
CUSTOMER_MAP = {
    "firma adı": "company_name",  "firma": "company_name",
    "şirket adı": "company_name", "şirket": "company_name",
    "company": "company_name",    "company name": "company_name",
    "ilgili kişi": "contact_person", "ilgili": "contact_person",
    "kişi": "contact_person",     "contact": "contact_person",
    "adres": "address",           "address": "address",
    "telefon": "phone",           "tel": "phone",
    "phone": "phone",             "gsm": "phone",
    "e-posta": "email",           "eposta": "email",
    "email": "email",             "mail": "email",
}
PRODUCT_MAP = {
    "ürün kodu": "product_code",  "kod": "product_code",
    "code": "product_code",       "product code": "product_code",
    "ürün adı": "product_name",   "ürün": "product_name",
    "ad": "product_name",         "name": "product_name",
    "açıklama": "description",    "aciklama": "description",
    "description": "description", "detay": "description",
    "fiyat": "price",             "price": "price",
    "birim fiyat": "price",       "unit price": "price",
    "para birimi": "currency",    "currency": "currency",
    "döviz": "currency",
    "stok": "stock",              "stock": "stock",
    "miktar": "stock",            "quantity": "stock",
    "birim": "unit",              "unit": "unit",
}


def _norm(s: str) -> str:
    return s.strip().lower().replace("_", " ")


def _read_file(path: str) -> tuple[list, str]:
    """Dosyayı okur, (rows, error) döndürür. rows = list of dicts."""
    p = Path(path)
    ext = p.suffix.lower()
    rows = []
    try:
        if ext in (".xlsx", ".xls", ".xlsm"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                ws = wb.active
                all_rows = list(ws.iter_rows(values_only=True))
                if not all_rows: return [], "Dosya boş."
                headers = [str(c or "").strip() for c in all_rows[0]]
                for row in all_rows[1:]:
                    if all(c is None for c in row): continue
                    rows.append({headers[i]: (str(v) if v is not None else "") 
                                 for i, v in enumerate(row) if i < len(headers)})
                wb.close()
            except ImportError:
                return [], ("openpyxl kütüphanesi bulunamadı.\n"
                            "Lütfen dosyayı CSV olarak kaydedin veya\n"
                            "komut satırında: pip install openpyxl")
        elif ext == ".csv":
            # BOM ve encoding denemesi
            for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
                try:
                    text = p.read_text(encoding=enc)
                    dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t")
                    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
                    rows = [dict(r) for r in reader]
                    break
                except Exception:
                    continue
        else:
            return [], f"Desteklenmeyen dosya türü: {ext}\nDesteklenen: .xlsx, .csv"
    except Exception as e:
        return [], str(e)
    return rows, ""


def _map_row(row: dict, col_map: dict) -> dict:
    """Ham satırı alan adlarına çevirir."""
    result = {}
    for raw_key, value in row.items():
        norm_key = _norm(raw_key)
        field = col_map.get(norm_key)
        if field:
            result[field] = value.strip() if isinstance(value, str) else (value or "")
    return result


class ExcelImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Excel / CSV'den İçe Aktar")
        self.setMinimumSize(760, 580)
        self._raw_rows = []
        self._mapped_rows = []
        self._import_type = "customers"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        title = QLabel("Excel / CSV'den İçe Aktar")
        title.setStyleSheet("font-size:11pt;font-weight:700;")
        layout.addWidget(title)

        # Sekme: Müşteriler / Ürünler
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_customer_tab(), "Müşteriler")
        self.tabs.addTab(self._build_product_tab(),  "Ürünler")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # Butonlar
        btn_row = QHBoxLayout()
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#888;font-size:8pt;")
        btn_row.addWidget(self.lbl_status)
        btn_row.addStretch()
        cancel = QPushButton("Kapat"); cancel.setObjectName("secondary")
        cancel.clicked.connect(self.reject)
        self.btn_import = QPushButton("İçe Aktar")
        self.btn_import.setObjectName("secondary")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._do_import)
        btn_row.addWidget(cancel); btn_row.addWidget(self.btn_import)
        layout.addLayout(btn_row)

    # ── Müşteri sekmesi ──────────────────────────────────────────────────────

    def _build_customer_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        info = QLabel(
            "<b>Beklenen sütunlar:</b> Firma Adı, İlgili Kişi, Adres, Telefon, E-posta<br>"
            "Sütun sırası ve tam yazımı önemli değil — otomatik eşleştirilir.<br>"
            "<i>Sadece 'Firma Adı' zorunludur, diğerleri opsiyoneldir.</i>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#eaf4fb;border:1px solid #bee3f8;border-radius:6px;"
            "padding:10px;font-size:8pt;"
        )
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_open = QPushButton("Dosya Seç (.xlsx veya .csv)")
        btn_open.setObjectName("secondary")
        btn_open.clicked.connect(lambda: self._open_file("customers"))
        btn_tmpl = QPushButton("Şablon İndir")
        btn_tmpl.setObjectName("secondary")
        btn_tmpl.clicked.connect(lambda: self._download_template("customers"))
        btn_row.addWidget(btn_open); btn_row.addWidget(btn_tmpl); btn_row.addStretch()
        layout.addLayout(btn_row)

        self.customer_preview = self._make_preview_table(
            ["Firma Adı", "İlgili Kişi", "Adres", "Telefon", "E-posta"])
        layout.addWidget(self.customer_preview)
        return w

    # ── Ürün sekmesi ─────────────────────────────────────────────────────────

    def _build_product_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)

        info = QLabel(
            "<b>Beklenen sütunlar:</b> Ürün Kodu, Ürün Adı, Açıklama, Fiyat, Para Birimi, Stok, Birim<br>"
            "Sütun sırası ve tam yazımı önemli değil — otomatik eşleştirilir.<br>"
            "<i>'Ürün Kodu' ve 'Ürün Adı' zorunludur. Duplicate kodlar atlanır.</i>"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#eaf4fb;border:1px solid #bee3f8;border-radius:6px;"
            "padding:10px;font-size:8pt;"
        )
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_open = QPushButton("Dosya Seç (.xlsx veya .csv)")
        btn_open.setObjectName("secondary")
        btn_open.clicked.connect(lambda: self._open_file("products"))
        btn_tmpl = QPushButton("Şablon İndir")
        btn_tmpl.setObjectName("secondary")
        btn_tmpl.clicked.connect(lambda: self._download_template("products"))
        btn_row.addWidget(btn_open); btn_row.addWidget(btn_tmpl); btn_row.addStretch()
        layout.addLayout(btn_row)

        self.product_preview = self._make_preview_table(
            ["Ürün Kodu", "Ürün Adı", "Fiyat", "Para Birimi", "Stok", "Birim", "Açıklama"])
        layout.addWidget(self.product_preview)
        return w

    def _make_preview_table(self, headers: list) -> QTableWidget:
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        if len(headers) > 1:
            t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setMinimumHeight(200)
        return t

    # ── Dosya açma / önizleme ────────────────────────────────────────────────

    def _on_tab_changed(self, idx):
        self._import_type = "customers" if idx == 0 else "products"
        self.btn_import.setEnabled(False)
        self.lbl_status.setText("")

    def _open_file(self, import_type: str):
        path, _ = QFileDialog.getOpenFileName(
            self, "Dosya Seç", "",
            "Excel & CSV (*.xlsx *.xls *.xlsm *.csv);;Tüm Dosyalar (*)")
        if not path: return

        self._import_type = import_type
        self.lbl_status.setText("Dosya okunuyor...")
        self.progress.setVisible(True); self.progress.setRange(0,0)

        raw_rows, err = _read_file(path)
        self.progress.setRange(0,1); self.progress.setValue(1)
        self.progress.setVisible(False)

        if err:
            QMessageBox.warning(self, "Dosya Hatası", err)
            self.lbl_status.setText("Hata — dosya okunamadı.")
            return
        if not raw_rows:
            QMessageBox.warning(self, "Boş Dosya", "Dosyada veri bulunamadı.")
            return

        col_map = CUSTOMER_MAP if import_type == "customers" else PRODUCT_MAP
        self._mapped_rows = [_map_row(r, col_map) for r in raw_rows]
        # Zorunlu alanı olmayan satırları filtrele
        req = "company_name" if import_type == "customers" else "product_code"
        valid = [r for r in self._mapped_rows if r.get(req,"").strip()]

        self._mapped_rows = valid
        self._show_preview(import_type, valid)
        count = len(valid)
        skip  = len(raw_rows) - count
        self.lbl_status.setText(
            f"✅  {count} satır hazır" + (f"  ({skip} satır zorunlu alan eksik — atlandı)" if skip else ""))
        self.btn_import.setEnabled(count > 0)

    def _show_preview(self, import_type: str, rows: list):
        if import_type == "customers":
            t = self.customer_preview
            keys = ["company_name","contact_person","address","phone","email"]
        else:
            t = self.product_preview
            keys = ["product_code","product_name","price","currency","stock","unit","description"]

        t.setRowCount(min(len(rows), 200))  # max 200 satır önizleme
        for r, row in enumerate(rows[:200]):
            for c, k in enumerate(keys):
                val = str(row.get(k,""))
                item = QTableWidgetItem(val)
                if not val:
                    item.setForeground(QColor("#aaa"))
                    item.setText("—")
                t.setItem(r, c, item)

    # ── İçe aktarma ──────────────────────────────────────────────────────────

    def _do_import(self):
        from database.db_manager import get_db
        db = get_db()
        added = skipped = 0

        self.progress.setVisible(True)
        self.progress.setRange(0, len(self._mapped_rows))

        if self._import_type == "customers":
            for i, row in enumerate(self._mapped_rows):
                self.progress.setValue(i)
                company = row.get("company_name","").strip()
                if not company: continue
                try:
                    db.execute(
                        "INSERT INTO customers (company_name,contact_person,address,phone,email)"
                        " VALUES (?,?,?,?,?)",
                        (company, row.get("contact_person",""), row.get("address",""),
                         row.get("phone",""), row.get("email",""))
                    )
                    added += 1
                except Exception:
                    skipped += 1
        else:
            for i, row in enumerate(self._mapped_rows):
                self.progress.setValue(i)
                code = row.get("product_code","").strip()
                name = row.get("product_name","").strip()
                if not code or not name: continue
                try:
                    price = float(str(row.get("price","0")).replace(",",".") or 0)
                except ValueError:
                    price = 0.0
                try:
                    stock = float(str(row.get("stock","0")).replace(",",".") or 0)
                except ValueError:
                    stock = 0.0
                currency = (row.get("currency","EUR") or "EUR").strip().upper()
                if currency not in ("EUR","USD","TL"): currency = "EUR"
                unit = row.get("unit","Adet") or "Adet"
                try:
                    db.execute(
                        "INSERT INTO products (product_code,product_name,description,"
                        "price,currency,stock,unit) VALUES (?,?,?,?,?,?,?)",
                        (code, name, row.get("description",""), price, currency, stock, unit)
                    )
                    added += 1
                except Exception:
                    skipped += 1

        self.progress.setValue(len(self._mapped_rows))
        self.progress.setVisible(False)

        typ = "müşteri" if self._import_type == "customers" else "ürün"
        msg = f"✅  {added} {typ} başarıyla eklendi."
        if skipped:
            msg += f"\n⚠️  {skipped} satır atlandı (duplicate veya hatalı veri)."
        QMessageBox.information(self, "İçe Aktarma Tamamlandı", msg)
        logger.info("Excel import tamamlandı: type=%s added=%d skipped=%d",
                    self._import_type, added, skipped)
        self.accept()

    # ── Şablon indirme ───────────────────────────────────────────────────────

    def _download_template(self, import_type: str):
        """CSV şablon dosyası oluşturup kaydet."""
        if import_type == "customers":
            filename = "musteri_sablonu.csv"
            header   = "Firma Adı,İlgili Kişi,Adres,Telefon,E-posta"
            sample   = "Örnek Firma A.Ş.,Ali Yılmaz,Ankara OSB No:1,0312 111 22 33,ali@ornek.com"
        else:
            filename = "urun_sablonu.csv"
            header   = "Ürün Kodu,Ürün Adı,Açıklama,Fiyat,Para Birimi,Stok,Birim"
            sample   = "PMP-001,Santrifüj Pompa,2.2kW paslanmaz,1250.00,EUR,10,Adet"

        path, _ = QFileDialog.getSaveFileName(
            self, "Şablon Kaydet", filename, "CSV (*.csv)")
        if not path: return
        try:
            Path(path).write_text(header + "\n" + sample + "\n", encoding="utf-8-sig")
            QMessageBox.information(self, "Şablon Kaydedildi",
                f"Şablon kaydedildi:\n{path}\n\n"
                "Excel'de açıp verilerinizi doldurun, CSV veya XLSX olarak kaydedin.")
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Şablon kaydedilemedi:\n{e}")
