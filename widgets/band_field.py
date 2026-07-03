from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSizePolicy

from core.config import BAND_IMAGE


class BandField(QWidget):
    """One gold 'band' frame (band.png) with a real input widget (QLineEdit
    or an editable QComboBox) sitting inside it, styled transparent so the
    band art shows through as the field's background.

    The widget is always sized to band.png's exact native aspect ratio
    (width fixed, height derived from it), so painting the pixmap into the
    full widget rect scales both axes by the identical factor — the art is
    never stretched, only uniformly scaled up or down."""

    # Measured off the source band.png (1842x241): the white interior spans
    # roughly this fraction in from each edge. Left margin is extra-wide so
    # placeholder/typed text always sits clear of the gold frame instead of
    # starting right at its inner edge.
    _LEFT_FRAC, _RIGHT_FRAC = 0.06, 0.035
    _TOP_FRAC, _BOTTOM_FRAC = 0.13, 0.13

    def __init__(self, input_widget: QWidget, width: int = 480, parent=None):
        super().__init__(parent)
        self._band = QPixmap(str(BAND_IMAGE)) if BAND_IMAGE.exists() else QPixmap()
        aspect = (self._band.width() / self._band.height()) if not self._band.isNull() else 7.64

        self.setFixedWidth(width)
        self.setFixedHeight(round(width / aspect))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        input_widget.setParent(self)
        input_widget.setStyleSheet(input_widget.styleSheet() + """
            background: transparent;
            border: none;
            color: #4a2f10;
            font-size: 15px;
            font-weight: 600;
            selection-background-color: #c9a24b;
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            round(self.width() * self._LEFT_FRAC),
            round(self.height() * self._TOP_FRAC),
            round(self.width() * self._RIGHT_FRAC),
            round(self.height() * self._BOTTOM_FRAC),
        )
        layout.addWidget(input_widget)
        self.input_widget = input_widget

    def paintEvent(self, event):
        if self._band.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        # self.rect() has the same aspect ratio as self._band by
        # construction, so this scales uniformly — never stretched.
        painter.drawPixmap(self.rect(), self._band, self._band.rect())
        painter.end()
