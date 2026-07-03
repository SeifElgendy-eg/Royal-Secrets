from pathlib import Path

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QWidget

from core.config import BACKGROUND_IMAGE, FOOTER_IMAGE


class PalaceBackdrop(QWidget):
    """Base widget that paints a full-bleed background image (cropped to
    cover, never stretched) with an optional footer banner pinned to the
    bottom edge, full width, at its native aspect ratio. Subclass/embed
    content on top of this — it only paints, it never lays out children
    itself.

    background_path/footer_path default to the page-1 palace + sponsor
    art, but any screen can pass its own pair (see RoyalRoomScreen)."""

    def __init__(self, background_path: Path = BACKGROUND_IMAGE,
                 footer_path: Path | None = FOOTER_IMAGE, parent=None):
        super().__init__(parent)
        self._bg = QPixmap(str(background_path)) if background_path and background_path.exists() else QPixmap()
        self._footer = QPixmap(str(footer_path)) if footer_path and footer_path.exists() else QPixmap()

    def background_rect(self) -> QRect:
        """Where the background image is currently drawn (post crop/scale),
        in this widget's own coordinates. Subclasses use this to pin
        overlay widgets to a spot on the artwork instead of the raw window
        size, so overlays track the image through resizes instead of
        drifting off the art they're meant to sit on."""
        if self._bg.isNull() or self.width() <= 0 or self.height() <= 0:
            return QRect(0, 0, self.width(), self.height())
        # Same math as KeepAspectRatioByExpanding below, done on the size
        # alone (no pixmap data touched) so it's cheap to call on resize.
        scaled_size = self._bg.size().scaled(self.size(), Qt.KeepAspectRatioByExpanding)
        x = (self.width() - scaled_size.width()) // 2
        y = (self.height() - scaled_size.height()) // 2
        return QRect(x, y, scaled_size.width(), scaled_size.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if not self._bg.isNull():
            # KeepAspectRatioByExpanding uses ONE scale factor for both axes
            # (never stretches), then crops whatever overflows — so the
            # image always covers the widget with its true proportions.
            rect = self.background_rect()
            scaled = self._bg.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(rect.topLeft(), scaled)
        else:
            painter.fillRect(self.rect(), Qt.black)

        if not self._footer.isNull() and self.width() > 0:
            # Uniform scale to fill the width edge-to-edge — same factor
            # applied to height, so the banner's proportions never distort.
            scaled_footer = self._footer.scaledToWidth(self.width(), Qt.SmoothTransformation)
            painter.drawPixmap(0, self.height() - scaled_footer.height(), scaled_footer)

        painter.end()
        super().paintEvent(event)
