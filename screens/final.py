from PySide6.QtCore import Qt, QRectF, QEasingCurve, QVariantAnimation
from PySide6.QtGui import QPixmap, QPainter

from core.config import BACKGROUND_IMAGE, FINAL_CHEST_IMAGE, FINAL_FOOTER_IMAGE, FINAL_PRODUCT_IMAGE, KEY_IMAGE
from widgets import PalaceBackdrop


class FinalScreen(PalaceBackdrop):
    """Screen 4: static reveal page after the chest is won. No buttons by
    design — the organizer resets the app for the next player (Ctrl+Shift+R).

    Built from the approved mockup as stacked layers:
      1. the palace room (BACKGROUND_IMAGE — same room the minigame stands in)
      2. the open, glowing chest + velvet table (FINAL_CHEST_IMAGE)
      3. the product box, animated rising up through the chest opening (FINAL_PRODUCT_IMAGE)
      4. the branded footer band + oil-drop flourish (FINAL_FOOTER_IMAGE)
      5. a small decorative key in the top-right corner (KEY_IMAGE)

    Layers 1 and 2 were exported at the same canvas size/aspect, so the
    chest is drawn at the exact same rect as the background — no per-layer
    alignment math needed. The footer and key are anchored to the widget's
    true edges instead (see _paint_footer/_paint_key) rather than to that
    same rect, because background_rect() can extend above/below the visible
    widget when the window's aspect forces a vertical crop — anchoring the
    footer to it could push it off the bottom of the screen entirely.
    """

    # Product box resting spot, as fractions of background_rect() — measured
    # off the mockup. Center x stays fixed for the whole animation.
    _PRODUCT_CENTER_X_FRAC = 0.5
    _PRODUCT_WIDTH_FRAC = 0.189
    _PRODUCT_END_BOTTOM_FRAC = 0.469

    # Where the box starts rising from, before it's clipped by the opening
    # (see _CHEST_OPENING_Y_FRAC below) — tune this to move the spot it
    # visually launches from.
    _PRODUCT_START_BOTTOM_FRAC = 0.75

    # The clip line: nothing is drawn below this height, so while the
    # rising box is entirely below it, it's fully invisible ("shouldn't
    # exist"); as it crosses above, only the emerged portion is drawn —
    # like it's being pulled up through the chest's opening. This must sit
    # at/just below _PRODUCT_END_BOTTOM_FRAC, or the box stays clipped even
    # once fully at rest. Tune alongside that value, not independently.
    _CHEST_OPENING_Y_FRAC = _PRODUCT_END_BOTTOM_FRAC - 0.025

    # Decorative key, top-right corner.
    _KEY_CENTER_X_FRAC = 0.918
    _KEY_TOP_MARGIN_FRAC = 0.015  # fraction of widget height, not background_rect()
    _KEY_WIDTH_FRAC = 0.156

    # Footer, bottom-anchored to the widget (see class docstring).
    _FOOTER_WIDTH_FRAC = 1.0

    _REVEAL_DURATION_MS = 1800

    def __init__(self, parent=None):
        super().__init__(background_path=BACKGROUND_IMAGE, footer_path=None, parent=parent)

        self._chest = QPixmap(str(FINAL_CHEST_IMAGE)) if FINAL_CHEST_IMAGE.exists() else QPixmap()
        self._footer_full = QPixmap(str(FINAL_FOOTER_IMAGE)) if FINAL_FOOTER_IMAGE.exists() else QPixmap()
        self._product = QPixmap(str(FINAL_PRODUCT_IMAGE)) if FINAL_PRODUCT_IMAGE.exists() else QPixmap()
        self._key = QPixmap(str(KEY_IMAGE)) if KEY_IMAGE.exists() else QPixmap()
        self._product_aspect = (self._product.width() / self._product.height()
                                 if not self._product.isNull() else 0.786)
        self._key_aspect = (self._key.width() / self._key.height()
                             if not self._key.isNull() else 2.214)
        self._footer_aspect = (self._footer_full.width() / self._footer_full.height()
                                if not self._footer_full.isNull() else 1.456)

        self._reveal_progress = 0.0
        self._reveal_anim = QVariantAnimation(self)
        self._reveal_anim.setStartValue(0.0)
        self._reveal_anim.setEndValue(1.0)
        self._reveal_anim.setDuration(self._REVEAL_DURATION_MS)
        self._reveal_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._reveal_anim.valueChanged.connect(self._on_reveal_value)

    def showEvent(self, event):
        super().showEvent(event)
        # Restart fresh every time this screen is shown, so each new winner
        # gets the same slow reveal rather than landing on a static image.
        self._reveal_progress = 0.0
        self._reveal_anim.stop()
        self._reveal_anim.start()

    def _on_reveal_value(self, value):
        self._reveal_progress = float(value)
        self.update()

    def paintEvent(self, event):
        # Base class paints the palace room (footer_path=None, so nothing
        # else happens there — we layer everything else ourselves below).
        super().paintEvent(event)

        rect = self.background_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if not self._chest.isNull():
            scaled_chest = self._chest.scaled(rect.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(rect.topLeft(), scaled_chest)

        self._paint_product(painter, rect)
        self._paint_footer(painter, rect)
        self._paint_key(painter, rect)

        painter.end()

    def _paint_product(self, painter, rect):
        if self._product.isNull():
            return

        t = self._reveal_progress

        width = rect.width() * self._PRODUCT_WIDTH_FRAC
        height = width / self._product_aspect

        bottom_frac = (self._PRODUCT_START_BOTTOM_FRAC
                        + (self._PRODUCT_END_BOTTOM_FRAC - self._PRODUCT_START_BOTTOM_FRAC) * t)
        center_x = rect.x() + rect.width() * self._PRODUCT_CENTER_X_FRAC
        bottom_y = rect.y() + rect.height() * bottom_frac

        target = QRectF(center_x - width / 2, bottom_y - height, width, height)

        # Clip everything below the chest's opening line so the box only
        # exists onscreen for the portion that's actually risen through it.
        opening_y = rect.y() + rect.height() * self._CHEST_OPENING_Y_FRAC

        painter.save()
        painter.setClipRect(QRectF(0, 0, self.width(), opening_y))
        painter.drawPixmap(target.toRect(), self._product, self._product.rect())
        painter.restore()

    def _paint_footer(self, painter, rect):
        if self._footer_full.isNull() or self.width() <= 0:
            return
        # Bottom-anchored to the actual widget, not background_rect() — see
        # class docstring for why. Horizontal position/scale still follows
        # the room's own rect so the oil-drop/footer art stays aligned with
        # the chest and floor beneath it.
        width = rect.width() * self._FOOTER_WIDTH_FRAC
        height = width / self._footer_aspect
        target = QRectF(rect.x(), self.height() - height, width, height)
        painter.drawPixmap(target.toRect(), self._footer_full, self._footer_full.rect())

    def _paint_key(self, painter, rect):
        if self._key.isNull():
            return
        width = rect.width() * self._KEY_WIDTH_FRAC
        height = width / self._key_aspect
        center_x = rect.x() + rect.width() * self._KEY_CENTER_X_FRAC
        top_y = self.height() * self._KEY_TOP_MARGIN_FRAC  # anchored to widget top, not rect
        target = QRectF(center_x - width / 2, top_y, width, height)
        painter.drawPixmap(target.toRect(), self._key, self._key.rect())