from PySide6.QtCore import Qt, QRectF, QEasingCurve, QVariantAnimation, QTimer
from PySide6.QtGui import QCursor, QPixmap, QPainter
from PySide6.QtWidgets import QPushButton

from core.config import (
    BACKGROUND_IMAGE, FINAL_CHEST_IMAGE, FINAL_FOOTER_IMAGE, FINAL_PRODUCT_IMAGE,
    FINAL_LIFESTYLE_IMAGE, KEY_IMAGE,
)
from widgets import PalaceBackdrop


class FinalScreen(PalaceBackdrop):
    """Screen 4: the win reveal, in two phases. No buttons besides Skip by
    design — the organizer resets the app for the next player
    (Ctrl+Shift+R).

    Phase 1 — built from the approved mockup as stacked layers:
      1. the palace room (BACKGROUND_IMAGE — same room the minigame stands in)
      2. the open, glowing chest + velvet table (FINAL_CHEST_IMAGE)
      3. the product box, animated rising up through the chest opening (FINAL_PRODUCT_IMAGE)
      4. the branded footer band + oil-drop flourish (FINAL_FOOTER_IMAGE)
      5. a small decorative key in the top-right corner (KEY_IMAGE)

    Phase 2 — once the reveal has held for _HOLD_MS (or Skip is tapped),
    the backdrop crossfades to a lifestyle shot (FINAL_LIFESTYLE_IMAGE)
    with the chest/product/key/tagline already baked into the art, so
    everything from phase 1 except the footer just fades out along with
    the room behind it. The footer is the one constant across both phases.

    Layers 1, 2, and the phase-2 lifestyle shot were all exported at the
    same canvas size/aspect, so each is drawn at the exact same rect as
    the background — no per-layer alignment math needed. The footer and
    key are anchored to the widget's true edges instead (see
    _paint_footer/_paint_key) rather than to that same rect, because
    background_rect() can extend above/below the visible widget when the
    window's aspect forces a vertical crop — anchoring the footer to it
    could push it off the bottom of the screen entirely.

    This screen is created once and reused for every player (see
    MainWindow), so everything resets in showEvent rather than __init__:
    every time it becomes the current widget, it starts fresh at phase 1.
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

    # Decorative key, top-right corner (phase 1 only).
    _KEY_CENTER_X_FRAC = 0.918
    _KEY_TOP_MARGIN_FRAC = 0.015  # fraction of widget height, not background_rect()
    _KEY_WIDTH_FRAC = 0.156

    # Footer, bottom-anchored to the widget (see class docstring).
    _FOOTER_WIDTH_FRAC = 1.0

    _REVEAL_DURATION_MS = 1800

    # Phase 2 timing: how long phase 1 holds once the reveal animation
    # finishes before auto-advancing, and how long the crossfade itself
    # takes. Skip bypasses the hold (not the crossfade).
    _HOLD_MS = 5000
    _CROSSFADE_MS = 900

    _SKIP_MARGIN_FRAC = 0.02  # fraction of widget size, anchored to the corner

    def __init__(self, parent=None):
        super().__init__(background_path=BACKGROUND_IMAGE, footer_path=None, parent=parent)

        self._chest = QPixmap(str(FINAL_CHEST_IMAGE)) if FINAL_CHEST_IMAGE.exists() else QPixmap()
        self._footer_full = QPixmap(str(FINAL_FOOTER_IMAGE)) if FINAL_FOOTER_IMAGE.exists() else QPixmap()
        self._product = QPixmap(str(FINAL_PRODUCT_IMAGE)) if FINAL_PRODUCT_IMAGE.exists() else QPixmap()
        self._lifestyle = QPixmap(str(FINAL_LIFESTYLE_IMAGE)) if FINAL_LIFESTYLE_IMAGE.exists() else QPixmap()
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
        self._reveal_anim.finished.connect(self._on_reveal_finished)

        # 0 -> phase 1 (chest reveal) fully visible, 1 -> phase 2
        # (lifestyle shot) fully visible.
        self._phase2_mix = 0.0
        self._phase2_anim = QVariantAnimation(self)
        self._phase2_anim.setStartValue(0.0)
        self._phase2_anim.setEndValue(1.0)
        self._phase2_anim.setDuration(self._CROSSFADE_MS)
        self._phase2_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._phase2_anim.valueChanged.connect(self._on_phase2_value)

        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._start_phase_two)

        self.skip_button = QPushButton("Skip  ›", self)
        self.skip_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.skip_button.setStyleSheet("""
            QPushButton {
                color: #f4e4b8;
                background-color: rgba(20, 12, 34, 140);
                border: 1px solid rgba(201, 162, 75, 160);
                border-radius: 16px;
                padding: 8px 18px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(40, 24, 64, 180);
                border-color: #c9a24b;
            }
        """)
        self.skip_button.clicked.connect(self._start_phase_two)
        self._position_skip_button()

    # --- phase control ------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        # Restart fresh every time this screen is shown, so each new
        # winner gets the full phase-1-then-phase-2 sequence rather than
        # landing wherever the previous player's session left off.
        self._hold_timer.stop()
        self._phase2_anim.stop()
        self._phase2_mix = 0.0
        self._reveal_progress = 0.0

        # Skip only ever shortcuts the *hold* — it's hidden until the box
        # has fully risen out of the chest, so the lifestyle background
        # can never appear before that reveal has actually played out.
        self.skip_button.hide()

        self._reveal_anim.stop()
        self._reveal_anim.start()
        self.update()

    def _on_reveal_value(self, value):
        self._reveal_progress = float(value)
        self.update()

    def _on_reveal_finished(self):
        self.skip_button.show()
        self.skip_button.raise_()
        self._hold_timer.start(self._HOLD_MS)

    def _start_phase_two(self):
        if self._reveal_progress < 0.999:
            return  # reveal hasn't finished yet — nothing to skip to
        if self._phase2_mix >= 1.0 or self._phase2_anim.state() == QVariantAnimation.Running:
            return  # already there, or already on the way
        self._hold_timer.stop()
        self.skip_button.hide()
        self._phase2_anim.stop()
        self._phase2_anim.start()

    def _on_phase2_value(self, value):
        self._phase2_mix = float(value)
        self.update()

    # --- layout ---------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_skip_button()

    def _position_skip_button(self):
        self.skip_button.adjustSize()
        margin = round(min(self.width(), self.height()) * self._SKIP_MARGIN_FRAC)
        self.skip_button.move(
            self.width() - self.skip_button.width() - margin,
            self.height() - self.skip_button.height() - margin,
        )

    # --- painting ---------------------------------------------------------

    def paintEvent(self, event):
        # Deliberately NOT calling super().paintEvent() — the base class
        # only knows how to draw one background layer, and phase 2 needs
        # two crossfading into each other, so we do the whole room/
        # lifestyle blend ourselves here instead.
        rect = self.background_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        mix = self._phase2_mix

        if not self._bg.isNull():
            painter.setOpacity(1.0 - mix)
            scaled_room = self._bg.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(rect.topLeft(), scaled_room)

        if mix > 0.0 and not self._lifestyle.isNull():
            painter.setOpacity(mix)
            scaled_life = self._lifestyle.scaled(rect.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(rect.topLeft(), scaled_life)

        if mix < 1.0:
            painter.setOpacity(1.0 - mix)
            if not self._chest.isNull():
                scaled_chest = self._chest.scaled(rect.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                painter.drawPixmap(rect.topLeft(), scaled_chest)
            self._paint_product(painter, rect)
            self._paint_key(painter, rect)

        painter.setOpacity(1.0)
        self._paint_footer(painter, rect)

        painter.end()
        # Deliberately not calling super().paintEvent(event) here either —
        # see the note at the top of this method.

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
        # Bottom-anchored AND width-anchored to the actual widget, not
        # background_rect(). rect.width() only equals self.width() while
        # the window is wider than the background's aspect ratio (the
        # landscape case this app targets) — once the window gets
        # narrower/taller than that, background_rect() overflows
        # horizontally to cover the extra height, and tying the footer's
        # scale to that overflowing width blew the footer up far past the
        # widget (pushing its top edge above y=0). Scaling to self.width()
        # instead — same approach the base PalaceBackdrop footer uses —
        # keeps the footer correctly sized at every window shape; it's
        # only pixel-identical to the old rect-based alignment in the
        # landscape case anyway, so normal usage is unaffected.
        width = self.width() * self._FOOTER_WIDTH_FRAC
        height = width / self._footer_aspect
        target = QRectF(0, self.height() - height, width, height)
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