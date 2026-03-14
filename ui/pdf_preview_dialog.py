"""PDF Önizleme Dialogu — pdf2image veya fitz (PyMuPDF) ile sayfa gösterir."""
import logging, os
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui  import QPixmap

logger = logging.getLogger("pdf_preview")


def _pdf_to_images(pdf_path: str) -> list:
    """PDF sayfalarını QPixmap listesine çevirir. PyMuPDF kullanır."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        pixmaps = []
        for page in doc:
            mat = fitz.Matrix(1.8, 1.8)  # ~130 dpi × 1.8 = iyi kalite
            pix = page.get_pixmap(matrix=mat, alpha=False)
            qpix = QPixmap()
            qpix.loadFromData(pix.tobytes("png"))
            pixmaps.append(qpix)
        doc.close()
        return pixmaps
    except ImportError:
        logger.warning("PyMuPDF kurulu değil, önizleme desteklenmiyor.")
        return []


class PdfPreviewDialog(QDialog):
    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path  = pdf_path
        self.setWindowTitle(f"PDF Önizleme — {Path(pdf_path).name}")
        self.setMinimumSize(720, 880)
        self.resize(760, 920)
        self._pages: list = []
        self._cur  = 0
        self._build_ui()
        self._load_pdf()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── Üst toolbar ──────────────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setObjectName("card")
        toolbar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        toolbar.setFixedHeight(48)
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(10)

        self.prev_btn = QPushButton("Önceki")
        self.prev_btn.setObjectName("secondary")
        self.prev_btn.setFixedHeight(32)
        self.prev_btn.clicked.connect(self._prev_page)

        self.page_lbl = QLabel("Sayfa 1 / 1")
        self.page_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_lbl.setMinimumWidth(100)

        self.next_btn = QPushButton("Sonraki")
        self.next_btn.setObjectName("secondary")
        self.next_btn.setFixedHeight(32)
        self.next_btn.clicked.connect(self._next_page)

        tb.addWidget(self.prev_btn)
        tb.addWidget(self.page_lbl)
        tb.addWidget(self.next_btn)
        tb.addStretch()

        open_btn = QPushButton("Dışarıda Aç")
        open_btn.setObjectName("primary")
        open_btn.setFixedHeight(32)
        open_btn.clicked.connect(self._open_external)
        tb.addWidget(open_btn)

        close_btn = QPushButton("Kapat")
        close_btn.setObjectName("secondary")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)
        tb.addWidget(close_btn)

        lay.addWidget(toolbar)

        # ── Sayfa görüntüleme alanı ───────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #e8ecf0; }")

        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.img_lbl.setStyleSheet("background: #e8ecf0; padding: 20px;")
        self.img_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.scroll.setWidget(self.img_lbl)
        lay.addWidget(self.scroll)

    def _load_pdf(self):
        self._pages = _pdf_to_images(self.pdf_path)
        if not self._pages:
            # PyMuPDF yok — kurulum önerisi göster
            msg = QLabel(
                "PDF önizleme için PyMuPDF gereklidir.\n\n"
                "Kurmak için terminalde şunu çalıştırın:\n"
                "    pip install pymupdf\n\n"
                "Şimdilik PDF'yi dışarıdan açabilirsiniz."
            )
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setStyleSheet("font-size:10pt;color:#555;padding:40px;")
            self.scroll.setWidget(msg)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        self._cur = 0
        self._show_page()

    def _show_page(self):
        if not self._pages: return
        pix = self._pages[self._cur]
        # Scroll alanına sığdır (genişliğe göre ölçekle)
        avail = self.scroll.viewport().width() - 40
        if pix.width() > avail > 0:
            pix = pix.scaledToWidth(avail, Qt.TransformationMode.SmoothTransformation)
        self.img_lbl.setPixmap(pix)
        self.img_lbl.adjustSize()
        total = len(self._pages)
        self.page_lbl.setText(f"Sayfa {self._cur + 1} / {total}")
        self.prev_btn.setEnabled(self._cur > 0)
        self.next_btn.setEnabled(self._cur < total - 1)

    def _prev_page(self):
        if self._cur > 0:
            self._cur -= 1
            self._show_page()

    def _next_page(self):
        if self._cur < len(self._pages) - 1:
            self._cur += 1
            self._show_page()

    def _open_external(self):
        os.startfile(self.pdf_path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._pages:
            self._show_page()
