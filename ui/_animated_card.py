"""Hover'da yukarı kayan animasyonlu kart bileşeni."""
from PySide6.QtWidgets import QFrame
from PySide6.QtCore    import QPropertyAnimation, QEasingCurve, QPoint, Qt


class AnimatedCard(QFrame):
    """
    QFrame#card ile aynı objectName — hover'da 4px yukarı kayar.
    (QGraphicsDropShadowEffect Windows'ta binlerce QFont uyarısı ürettiğinden
     gölge efekti CSS box-shadow yerine bırakıldı.)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # ── Pozisyon animasyonu ───────────────────────────────────────────
        self._anim_pos = QPropertyAnimation(self, b"pos")
        self._anim_pos.setDuration(160)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._base_pos = None

    def showEvent(self, event):
        super().showEvent(event)
        # Layout henüz tamamlanmamış olabilir — bir sonraki event loop turunda kaydet
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._capture_base_pos)

    def _capture_base_pos(self):
        """Layout yerleşimi tamamlandıktan sonra referans pozisyonu kaydet."""
        self._base_pos = self.pos()

    def enterEvent(self, event):
        if self._base_pos is None:
            self._base_pos = self.pos()
        target = self._base_pos - QPoint(0, 4)
        if self.pos() == target:
            super().enterEvent(event)
            return
        self._anim_pos.stop()
        self._anim_pos.setStartValue(self.pos())
        self._anim_pos.setEndValue(target)
        self._anim_pos.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._base_pos is None:
            super().leaveEvent(event)
            return
        self._anim_pos.stop()
        self._anim_pos.setStartValue(self.pos())
        self._anim_pos.setEndValue(self._base_pos)
        self._anim_pos.start()
        super().leaveEvent(event)
