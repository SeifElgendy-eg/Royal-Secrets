import math
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QLinearGradient, QPixmap
from PySide6.QtWidgets import QWidget

from .config import GameConfig, DEFAULT_CONFIG, CHEST_ART_IMAGE, METER_PILL_IMAGE
from .physics import triangle_wave


class SweepMeter(QWidget):
    """A back-and-forth sweep bar (angle or power) with a ball-rack picker
    below it. Purely presentational + input handling — it reports locked
    values via signals and lets ChestGameScreen decide what they mean."""

    locked = Signal(float)
    ball_selected = Signal(Path)

    _BASE_CAPTION_H = 24
    _BASE_PILL_W = 880
    _BASE_PILL_H = 80

    _BASE_TEXT_Y = 450
    _BASE_LINE_Y = 501.5
    _BASE_TRACK_PADDING_X = 220

    _BASE_RACK_Y = 530
    _BASE_RACK_SPACING = 55
    _BASE_RACK_OFFSET_Y = 40
    _BASE_CANNON_GAP = 140

    def __init__(self, title: str, period_ms: int, accent_color: str,
                 selected_path: Path, all_available_paths: list,
                 config: GameConfig = DEFAULT_CONFIG, parent=None):
        super().__init__(parent)
        self.title = title
        self.period_ms = period_ms
        self.accent_color = accent_color
        self.config = config
        self.setCursor(Qt.PointingHandCursor)

        self.selected_path = selected_path
        self.all_paths = [p for p in all_available_paths if p.exists()]

        self._ball_pixmaps = {p: QPixmap(str(p)) for p in self.all_paths}
        self._raw_pill = QPixmap(str(METER_PILL_IMAGE)) if METER_PILL_IMAGE.exists() else QPixmap()

        if not self._raw_pill.isNull():
            aspect_ratio = self._raw_pill.width() / max(1, self._raw_pill.height())
            self.native_width = self._BASE_PILL_W
            self.native_height = int(self._BASE_PILL_W / aspect_ratio)
        else:
            self.native_width = self._BASE_PILL_W
            self.native_height = self._BASE_PILL_H

        self.scale_factor = 1.0
        self._value = 0.0
        self._running = False
        self._clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

        self._rack_hitboxes = []
        self.update_scale(1.0)

    def update_scale(self, factor: float):
        self.scale_factor = max(0.4, min(factor, 2.0))
        new_w = int(self.native_width * self.scale_factor)
        new_h = int((self._BASE_CAPTION_H + self.native_height) * self.scale_factor)
        self.setFixedSize(new_w, new_h)
        self._recalculate_hitboxes()
        self.update()

    def _recalculate_hitboxes(self):
        self._rack_hitboxes.clear()
        if not self.all_paths:
            return

        caption_h = self._BASE_CAPTION_H * self.scale_factor
        pill_top = caption_h
        rack_y = pill_top + ((self._BASE_RACK_Y + self._BASE_RACK_OFFSET_Y) * self.scale_factor)
        spacing = self._BASE_RACK_SPACING * self.scale_factor
        ball_radius = max(5, int(self.config.meter_ball_radius * self.scale_factor))

        gap = self._BASE_CANNON_GAP * self.scale_factor
        half_count = math.ceil(len(self.all_paths) / 2.0)

        total_width = (len(self.all_paths) - 1) * spacing + gap
        start_x = (self.width() - total_width) / 2

        for i, path in enumerate(self.all_paths):
            extra_offset = gap if i >= half_count else 0
            cx = start_x + (i * spacing) + extra_offset

            rect = QRectF(cx - ball_radius - 5, rack_y - ball_radius - 5,
                          (ball_radius + 5) * 2, (ball_radius + 5) * 2)
            self._rack_hitboxes.append((rect, path))

    def start(self):
        self._running = True
        self._clock.start()
        self._timer.start(16)

    def _tick(self):
        self._value = triangle_wave(self._clock.elapsed(), self.period_ms)
        self.update()

    def mousePressEvent(self, event):
        pos = event.position()

        for hitbox, path in self._rack_hitboxes:
            if hitbox.contains(pos):
                self.selected_path = path
                self.ball_selected.emit(path)
                self.update()
                return

        if not self._running or event.button() != Qt.LeftButton:
            return
        self._running = False
        self._timer.stop()
        self.locked.emit(self._value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        caption_h = self._BASE_CAPTION_H * self.scale_factor
        pill_h = self.native_height * self.scale_factor
        pill_rect = QRectF(0, caption_h, self.width(), pill_h)

        if not self._raw_pill.isNull():
            painter.drawPixmap(pill_rect.toRect(), self._raw_pill, self._raw_pill.rect())
        else:
            gradient = QLinearGradient(pill_rect.topLeft(), pill_rect.bottomLeft())
            gradient.setColorAt(0, QColor("#3a2663"))
            gradient.setColorAt(1, QColor("#1c0f34"))
            painter.setPen(QPen(QColor("#c9a24b"), max(1.5, 3 * self.scale_factor)))
            painter.setBrush(gradient)
            painter.drawRoundedRect(pill_rect.adjusted(1, 1, -1, -1), pill_rect.height() / 2, pill_rect.height() / 2)

        painter.setPen(QColor("#f4e4b8"))
        font_size = max(8, int(11 * self.scale_factor))
        painter.setFont(QFont("Georgia", font_size, QFont.Bold))
        text_y = pill_rect.top() + (self._BASE_TEXT_Y * self.scale_factor)
        painter.drawText(QRectF(0, text_y, self.width(), caption_h), Qt.AlignCenter, self.title.upper())

        padding_x = self._BASE_TRACK_PADDING_X * self.scale_factor
        track_left = pill_rect.left() + padding_x
        track_width = pill_rect.width() - (2 * padding_x)
        track_center_y = pill_rect.top() + (self._BASE_LINE_Y * self.scale_factor)

        groove_thickness = max(2, int(4 * self.scale_factor))
        painter.setPen(QPen(QColor(255, 255, 255, 40), groove_thickness, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(track_left, track_center_y), QPointF(track_left + track_width, track_center_y))

        marker_x = track_left + (self._value * track_width)
        ball_radius = max(5, int(self.config.meter_ball_radius * self.scale_factor))

        active_pixmap = self._ball_pixmaps.get(self.selected_path, QPixmap())
        if not active_pixmap.isNull():
            dest = QRectF(marker_x - ball_radius, track_center_y - ball_radius, ball_radius * 2, ball_radius * 2)
            painter.drawPixmap(dest.toRect(), active_pixmap, active_pixmap.rect())
        else:
            painter.setPen(QPen(QColor("#f4e4b8"), max(1.0, 1.5 * self.scale_factor)))
            painter.setBrush(QColor(self.accent_color))
            painter.drawEllipse(QPointF(marker_x, track_center_y), ball_radius, ball_radius)

        for hitbox, path in self._rack_hitboxes:
            px = self._ball_pixmaps.get(path, QPixmap())

            if path == self.selected_path:
                painter.setPen(QPen(QColor("#c9a24b"), max(2.0, 3.0 * self.scale_factor)))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(hitbox.center(), ball_radius + 4, ball_radius + 4)

            if not px.isNull():
                dest = QRectF(hitbox.center().x() - ball_radius, hitbox.center().y() - ball_radius,
                              ball_radius * 2, ball_radius * 2)
                painter.drawPixmap(dest.toRect(), px, px.rect())
            else:
                painter.setPen(QPen(QColor("#ffffff"), 1))
                painter.setBrush(QColor("#777777"))
                painter.drawEllipse(hitbox.center(), ball_radius, ball_radius)

        painter.end()


class ChestWidget(QWidget):
    """The chest art plus its (config-driven) opening hitbox. The hitbox
    fractions are the main difficulty lever, so they come from GameConfig
    instead of being baked in here."""

    def __init__(self, config: GameConfig = DEFAULT_CONFIG, parent=None):
        super().__init__(parent)
        self.config = config
        self._art = QPixmap(str(CHEST_ART_IMAGE)) if CHEST_ART_IMAGE.exists() else QPixmap()

        if not self._art.isNull():
            self.native_width = self._art.width()
            self.native_height = self._art.height()
        else:
            self.native_width = 300
            self.native_height = round(300 / (966 / 717))

        self.intro_scale = 1.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def target_rect_in_parent(self) -> QRectF:
        w, h = self.width(), self.height()
        c = self.config
        local = QRectF(
            w * (0.5 - c.chest_opening_width_frac / 2),
            h * c.chest_opening_top_frac,
            w * c.chest_opening_width_frac,
            h * c.chest_opening_height_frac,
        )
        return local.translated(self.pos())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.intro_scale != 1.0:
            painter.translate(self.width() / 2, self.height() / 2)
            painter.scale(self.intro_scale, self.intro_scale)
            painter.translate(-self.width() / 2, -self.height() / 2)

        rect = QRectF(0, 0, self.width(), self.height())

        if not self._art.isNull():
            painter.drawPixmap(rect.toRect(), self._art, self._art.rect())
        else:
            base = rect.adjusted(rect.width() * 0.04, rect.height() * 0.30, -rect.width() * 0.04, 0)
            gradient = QLinearGradient(base.topLeft(), base.bottomRight())
            gradient.setColorAt(0, QColor("#f0c869"))
            gradient.setColorAt(1, QColor("#8a6420"))
            painter.setPen(QPen(QColor("#5c4013"), 3))
            painter.setBrush(gradient)
            painter.drawRoundedRect(base, 14, 14)
            lid = rect.adjusted(rect.width() * 0.06, 0, -rect.width() * 0.06, -rect.height() * 0.62)
            painter.setBrush(QColor("#f7d98a"))
            painter.drawRoundedRect(lid, 10, 10)
        painter.end()


class LaunchBaseWidget(QWidget):
    """Pure cannon art — angle-rotated barrel + loaded-ball display. No
    difficulty-relevant numbers live here, only drawing geometry.

    All the drawing coordinates below (base stand, barrel, pivot, loaded
    ball) were designed for a 180x180 widget. `update_scale()` applies the
    page's own responsive scale_factor — same pattern as
    SweepMeter.update_scale() — so the cannon grows and shrinks along with
    everything else on resize instead of staying pinned to a fixed pixel
    size.

    The art multiplier itself isn't flat: it interpolates from
    `_ART_SCALE_MIN` at the smallest page scale up to `_ART_SCALE_MAX` at
    the largest, so small windows get the old, more modest cannon size
    while large windows get today's bigger one — rather than shifting the
    whole range up or down uniformly.
    """

    _BASE_SIZE = 180
    _PAGE_SCALE_MIN = 0.4
    _PAGE_SCALE_MAX = 1.5
    _ART_SCALE_MIN = 0.6   # size at the smallest window (matches the old, smaller cannon)
    _ART_SCALE_MAX = 0.9   # size at the largest window (matches the current bigger cannon)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.page_scale = 1.0
        self._apply_size()
        self.angle_deg = 90.0
        self.loaded_ball_pixmap = QPixmap()
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    @property
    def normalized_scale(self) -> float:
        """0.0 at the smallest page scale, 1.0 at the largest — lets callers
        (like ChestGameScreen's positioning logic) key off how big the
        cannon currently is without reaching into private constants."""
        span = self._PAGE_SCALE_MAX - self._PAGE_SCALE_MIN
        t = (self.page_scale - self._PAGE_SCALE_MIN) / span if span else 0.0
        return max(0.0, min(t, 1.0))

    @property
    def scale(self) -> float:
        t = self.normalized_scale
        art_scale = self._ART_SCALE_MIN + t * (self._ART_SCALE_MAX - self._ART_SCALE_MIN)
        return art_scale * self.page_scale

    def _apply_size(self):
        size = int(self._BASE_SIZE * self.scale)
        self.setFixedSize(size, size)

    def update_scale(self, page_scale_factor: float):
        self.page_scale = max(self._PAGE_SCALE_MIN, min(page_scale_factor, self._PAGE_SCALE_MAX))
        self._apply_size()
        self.update()


    def set_angle(self, angle):
        self.angle_deg = angle
        self.update()

    def set_loaded_ball(self, pixmap: QPixmap):
        self.loaded_ball_pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 + 30 * self.scale

        painter.translate(cx, cy)
        painter.scale(self.scale, self.scale)

        # 1. Base Stand
        painter.setPen(QPen(QColor("#1a1025"), 3))
        painter.setBrush(QColor("#3a2663"))
        painter.drawRoundedRect(-60, -5, 120, 35, 10, 10)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#543a8e"))
        painter.drawRoundedRect(-45, 0, 90, 8, 4, 4)

        # 2. Barrel (rotates)
        painter.save()
        painter.rotate(90 - self.angle_deg)
        painter.setPen(QPen(QColor("#4a320f"), 3))
        painter.setBrush(QColor("#c9a24b"))
        painter.drawRect(-24, -65, 48, 65)

        painter.setBrush(QColor("#f4e4b8"))
        painter.drawRoundedRect(-32, -75, 64, 20, 6, 6)
        painter.setBrush(QColor("#222222"))
        painter.drawEllipse(QPointF(0, -70), 18, 6)
        painter.restore()

        # 3. Pivot base & loading chamber
        painter.setBrush(QColor("#8a6420"))
        painter.setPen(QPen(QColor("#4a320f"), 3))
        painter.drawEllipse(QPointF(0, 0), 36, 36)

        # 4. Loaded ball inside the chamber
        if not self.loaded_ball_pixmap.isNull():
            ball_radius = 24
            dest = QRectF(-ball_radius, -ball_radius, ball_radius * 2, ball_radius * 2)
            painter.drawPixmap(dest.toRect(), self.loaded_ball_pixmap, self.loaded_ball_pixmap.rect())
        else:
            painter.setBrush(QColor("#1a1025"))
            painter.setPen(QPen(QColor("#111111"), 3))
            painter.drawEllipse(QPointF(0, 0), 22, 22)

        painter.end()
        
class ProductBoxWidget(QWidget):
    """A widget that holds the prize product image, supporting smooth
    opacity changes and rotation during the win animation sequence."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap()
        self.opacity = 1.0
        self.rotation_deg = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()

    def setPixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap
        self.update()

    def setOpacity(self, opacity: float):
        self.opacity = max(0.0, min(1.0, opacity))
        self.update()

    def paintEvent(self, event):
        if self.pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Apply opacity level
        painter.setOpacity(self.opacity)
        
        # Move origin to center, rotate, and draw cleanly
        painter.translate(self.width() / 2.0, self.height() / 2.0)
        painter.rotate(self.rotation_deg)
        
        # Scale image to fit inside the animated widget borders
        scaled = self.pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        painter.drawPixmap(
            round(-scaled.width() / 2.0),
            round(-scaled.height() / 2.0),
            scaled
        )