import math

from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPoint, QPointF, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget, QLabel

from .config import GameConfig, DEFAULT_CONFIG, GAME_BACKGROUND_IMAGE, GAME_FOOTER_IMAGE, BALL_IMAGES
from .layout import compute_scale_factor
from .physics import compute_trajectory
from .state import GameState
from .widgets import SweepMeter, ChestWidget, LaunchBaseWidget

import random
from pathlib import Path


class ChestGameScreen(QWidget):
    """Screen 3: the chest minigame itself. Owns Qt widgets, animation
    timers, and input wiring — actual difficulty numbers live in
    GameConfig, progress bookkeeping lives in GameState, and trajectory
    math lives in game.physics. This class is the glue between them."""

    game_finished = Signal(int, int)

    def __init__(self, config: GameConfig = DEFAULT_CONFIG, parent=None):
        super().__init__(parent)
        self.config = config
        self.state = GameState(config=config)

        self._bg = QPixmap(str(GAME_BACKGROUND_IMAGE)) if GAME_BACKGROUND_IMAGE.exists() else QPixmap()
        self._footer = QPixmap(str(GAME_FOOTER_IMAGE)) if GAME_FOOTER_IMAGE.exists() else QPixmap()

        self._angle_value = 0.0
        self._active_meter = None
        self._ball = None
        self._ball_timer = None
        self._traj_points = []
        self._traj_index = 0

        self._current_ball_image_path = self._get_random_ball_image_path()

        self.status_label = QLabel(self)
        self.status_label.setStyleSheet("color: #f4e4b8; font-size: 15px; font-weight: bold; background: transparent;")
        self.status_label.move(20, 18)

        self.flash_label = QLabel(self)
        self.flash_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.flash_label.setAlignment(Qt.AlignCenter)
        self.flash_label.setFixedSize(200, 40)
        self.flash_label.setStyleSheet("background: transparent;")
        self.flash_label.hide()

        self.footer_label = QLabel(self)
        self.footer_label.setStyleSheet("background: transparent;")

        self.chest = ChestWidget(config=self.config, parent=self)
        self.chest.show()

        self.launch_base = LaunchBaseWidget(self)
        self.launch_base.show()

        self._update_status()

        self._intro_frame = 0
        self._intro_timer = QTimer(self)
        self._intro_timer.timeout.connect(self._step_intro_pop)
        self.chest.intro_scale = 0.1
        self._intro_timer.start(16)

        self._base_tracking_timer = QTimer(self)
        self._base_tracking_timer.timeout.connect(self._update_base_tracking)
        self._base_tracking_timer.start(16)

        QTimer.singleShot(0, self._start_next_attempt)

    def _update_loaded_cannon_ball(self):
        if self._current_ball_image_path and self._current_ball_image_path.exists():
            self.launch_base.set_loaded_ball(QPixmap(str(self._current_ball_image_path)))
        else:
            self.launch_base.set_loaded_ball(QPixmap())

    def _update_base_tracking(self):
        if self._active_meter:
            tilt_max = self.config.launch_tilt_max_deg
            if self._active_meter.title == "Angle":
                tilt_deg = -tilt_max + self._active_meter._value * (2 * tilt_max)
                self.launch_base.set_angle(90 - tilt_deg)
            elif self._active_meter.title == "Power":
                tilt_deg = -tilt_max + self._angle_value * (2 * tilt_max)
                self.launch_base.set_angle(90 - tilt_deg)
        # else: no active meter — leave the barrel exactly where it was.
        # This keeps it fixed at the fired angle during flight and between
        # shots, instead of tracking the ball or snapping back to vertical.

    def _step_intro_pop(self):
        self._intro_frame += 1
        t = self._intro_frame / 35.0
        if t >= 1.0:
            self.chest.intro_scale = 1.0
            self._intro_timer.stop()
        else:
            p = 0.3
            scale = math.pow(2, -10 * t) * math.sin((t - p / 4) * (2 * math.pi) / p) + 1.0
            self.chest.intro_scale = max(0.1, scale)
        self.chest.update()

    def _get_random_ball_image_path(self) -> Path | None:
        valid_images = [f for f in BALL_IMAGES if f.exists()]
        if valid_images:
            return random.choice(valid_images)
        return None

    def _on_ball_swapped_by_player(self, chosen_path: Path):
        self._current_ball_image_path = chosen_path
        self._update_loaded_cannon_ball()

    def get_launch_point(self) -> QPoint:
        w, h = self.width(), self.height()
        if w <= 0: w = 900
        if h <= 0: h = 700
        scale_factor = compute_scale_factor(w)

        if self._active_meter:
            meter_y = self._active_meter.y()
            caption_h = SweepMeter._BASE_CAPTION_H * scale_factor
            track_line_y = meter_y + caption_h + (SweepMeter._BASE_LINE_Y * scale_factor)
            return QPoint(w // 2, int(track_line_y))
        else:
            m_h = int((SweepMeter._BASE_CAPTION_H + SweepMeter._BASE_PILL_H) * scale_factor)
            meter_y = h - m_h - 5
            return QPoint(w // 2, meter_y + int(SweepMeter._BASE_CAPTION_H * scale_factor))

    def get_derived_power_range(self):
        lp = self.get_launch_point()
        target_y = self.chest.target_rect_in_parent().center().y()
        height_needed = lp.y() - target_y
        if height_needed <= 0:
            height_needed = 300

        power_for_center = math.sqrt(2 * self.config.gravity * height_needed)
        return power_for_center * self.config.power_min_mult, power_for_center * self.config.power_max_mult

    def background_rect(self) -> QRect:
        if self._bg.isNull() or self.width() <= 0 or self.height() <= 0:
            return QRect(0, 0, self.width(), self.height())
        scaled_size = self._bg.size().scaled(self.size(), Qt.KeepAspectRatioByExpanding)
        x = (self.width() - scaled_size.width()) // 2
        y = (self.height() - scaled_size.height()) // 2
        return QRect(x, y, scaled_size.width(), scaled_size.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        scale_factor = compute_scale_factor(w)

        chest_scale = min(scale_factor, 1.25)
        new_chest_w = int(self.chest.native_width * chest_scale)
        new_chest_h = int(self.chest.native_height * chest_scale)
        self.chest.setFixedSize(new_chest_w, new_chest_h)

        cx = (w - new_chest_w) // 2
        cy = (h - new_chest_h) // 2
        self.chest.move(cx, cy)

        if not self._footer.isNull():
            scaled_footer = self._footer.scaledToWidth(w, Qt.SmoothTransformation)
            self.footer_label.setPixmap(scaled_footer)
            self.footer_label.setFixedSize(scaled_footer.size())
            self.footer_label.move(0, h - scaled_footer.height())
            self.footer_label.show()

        if self._active_meter:
            self._active_meter.update_scale(scale_factor)
            mx = (w - self._active_meter.width()) // 2

            if not self._footer.isNull() and self.footer_label.height() > 0:
                footer_y = self.footer_label.y()
                footer_h = self.footer_label.height()
                offset_down = int(15 * scale_factor)
                my = footer_y + (footer_h - self._active_meter.height()) // 2 + offset_down
            else:
                my = h - self._active_meter.height() - 5

            self._active_meter.setGeometry(mx, my, self._active_meter.width(), self._active_meter.height())

        self.launch_base.update_scale(scale_factor)

        lp = self.get_launch_point()
        # Anchor to the window's bottom edge (not to lp.y(), which moves
        # independently) so the cannon touches/overhangs the edge. The
        # overhang is *inverse* to page scale: a smaller cannon sits lower
        # (dips further past the edge) than a bigger one, which otherwise
        # looked like it was floating too high relative to its own size on
        # small windows.
        t = self.launch_base.normalized_scale
        overhang = int(35 - t * 20)  # 35px when smallest, 15px when largest
        target_y = h - self.launch_base.height() + overhang
        self.launch_base.move(lp.x() - self.launch_base.width() // 2, target_y)

        self.status_label.move(20, 18)
        self.flash_label.move(w // 2 - self.flash_label.width() // 2, cy - 50)

        self.chest.lower()
        self.footer_label.raise_()
        if self._active_meter:
            self._active_meter.raise_()
        self.launch_base.raise_()
        self.status_label.raise_()
        self.flash_label.raise_()
        if self._ball:
            self._ball.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if not self._bg.isNull():
            rect = self.background_rect()
            scaled = self._bg.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.drawPixmap(rect.topLeft(), scaled)
        else:
            painter.fillRect(self.rect(), QColor("#1c1330"))
        painter.end()
        super().paintEvent(event)

    def _update_status(self):
        self.status_label.setText(self.state.status_text())
        self.status_label.adjustSize()

    def _start_next_attempt(self):
        if not self._current_ball_image_path or not self._current_ball_image_path.exists():
            self._current_ball_image_path = self._get_random_ball_image_path()

        self._update_loaded_cannon_ball()

        self._show_meter("Angle", self.config.angle_sweep_period_ms, "#c9a24b", self._on_angle_locked)

    def _show_meter(self, title, period_ms, color, on_locked):
        if self._active_meter:
            self._active_meter.deleteLater()

        meter = SweepMeter(
            title=title,
            period_ms=period_ms,
            accent_color=color,
            selected_path=self._current_ball_image_path,
            all_available_paths=BALL_IMAGES,
            config=self.config,
            parent=self,
        )
        meter.locked.connect(on_locked)
        meter.ball_selected.connect(self._on_ball_swapped_by_player)

        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            w, h = 900, 700

        scale_factor = compute_scale_factor(w)
        meter.update_scale(scale_factor)
        mx = (w - meter.width()) // 2

        if not self._footer.isNull() and self.footer_label.height() > 0:
            footer_y = self.footer_label.y()
            footer_h = self.footer_label.height()
            offset_down = int(15 * scale_factor)
            my = footer_y + (footer_h - meter.height()) // 2 + offset_down
        else:
            my = h - meter.height() - 5

        meter.setGeometry(mx, my, meter.width(), meter.height())
        meter.show()
        meter.start()

        meter.raise_()
        self.launch_base.raise_()
        self._active_meter = meter

    def _on_angle_locked(self, value: float):
        self._angle_value = value
        self._active_meter.deleteLater()
        self._active_meter = None
        self._show_meter("Power", self.config.power_sweep_period_ms, "#8a5fb0", self._on_power_locked)

    def _on_power_locked(self, value: float):
        self._active_meter.deleteLater()
        self._active_meter = None

        tilt_max = self.config.launch_tilt_max_deg
        tilt_deg = -tilt_max + self._angle_value * (2 * tilt_max)
        angle_deg = 90 - tilt_deg

        p_min, p_max = self.get_derived_power_range()
        power = p_min + value * (p_max - p_min)

        self.state.begin_attempt()
        self._launch_ball(angle_deg, power)

    def _launch_ball(self, angle_deg: float, power: float):
        self.launch_base.set_loaded_ball(QPixmap())

        lp = self.get_launch_point()
        self._traj_points = compute_trajectory(angle_deg, power, lp.x(), lp.y(), self.config.gravity)
        self._traj_index = 0

        self._ball = QLabel(self)
        radius = self.config.flight_ball_radius
        self._ball.setFixedSize(radius * 2, radius * 2)
        self._ball.setStyleSheet("background: transparent;")

        self._current_ball_pixmap = QPixmap()
        if self._current_ball_image_path and self._current_ball_image_path.exists():
            self._current_ball_pixmap = QPixmap(str(self._current_ball_image_path))

        self._ball.show()
        self._ball.raise_()

        self._ball_timer = QTimer(self)
        self._ball_timer.timeout.connect(self._step_ball)

        # Position/paint the ball at its true first trajectory point *now*,
        # synchronously — otherwise it sits at the QLabel's default (0, 0)
        # until the timer's first tick fires, and the independent
        # _base_tracking_timer can catch that stale position in between,
        # snapping the barrel toward the corner for a frame right as we fire.
        self._step_ball()

        if self._ball_timer is not None:
            self._ball_timer.start(16)

    def _step_ball(self):
        if self._traj_index >= len(self._traj_points):
            self._finish_attempt(False)
            return

        x, y = self._traj_points[self._traj_index]

        is_going_down = False
        if self._traj_index < len(self._traj_points) - 1:
            _, next_y = self._traj_points[self._traj_index + 1]
            if next_y > y:
                is_going_down = True

        total_steps = max(1, len(self._traj_points))
        progress = self._traj_index / total_steps

        current_scale = 1.0 - (progress * (1.0 - self.config.min_ball_scale))
        current_radius = int(self.config.flight_ball_radius * current_scale)
        current_diameter = max(2, current_radius * 2)

        self._ball.setFixedSize(current_diameter, current_diameter)
        self._ball.move(int(x - current_radius), int(y - current_radius))

        if not self._current_ball_pixmap.isNull():
            self._ball.setPixmap(self._current_ball_pixmap.scaled(
                current_diameter, current_diameter,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self._ball.setStyleSheet(f"""
                background: qradialgradient(cx:0.35, cy:0.3, radius:0.9, fx:0.35, fy:0.3, stop:0 #fff3c9, stop:1 #c9a24b);
                border-radius: {current_radius}px;
                border: 2px solid rgba(255,255,255,0.6);
            """)

        if is_going_down:
            self._ball.stackUnder(self.footer_label)
        else:
            self._ball.raise_()

        target_box = self.chest.target_rect_in_parent()
        if target_box.contains(QPointF(x, y)):
            if is_going_down:
                self._finish_attempt(True)
                return

        if x < -20 or x > self.width() + 20 or y > self.height() + 100:
            self._finish_attempt(False)
            return

        self._traj_index += 1

    def _finish_attempt(self, success: bool):
        self._ball_timer.stop()
        self._ball_timer = None
        if self._ball is not None:
            self._ball.deleteLater()
            self._ball = None

        self.state.record_result(success)
        if success:
            self._show_flash("IN! ✨", "#2e7d32")
        else:
            self._show_flash("MISS", "#8e2431")

        self._update_status()

        flash_ms = self.config.flash_duration_ms
        if self.state.is_won:
            QTimer.singleShot(flash_ms + 200, self._play_win_sequence)
        else:
            QTimer.singleShot(flash_ms + 200, self._start_next_attempt)

    def _show_flash(self, text: str, color: str):
        self.flash_label.setText(text)
        self.flash_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.flash_label.show()
        self.flash_label.raise_()
        QTimer.singleShot(self.config.flash_duration_ms, self.flash_label.hide)

    def _play_win_sequence(self):
        self.status_label.setText("You unlocked the secret! ✨")

        prize = QLabel(self)
        prize.setStyleSheet("background-color: #fbeecb; border: 3px solid #c9a24b; border-radius: 10px;")
        start_rect = QRect(
            self.chest.x() + self.chest.width() // 2 - 35,
            self.chest.y() + self.chest.height() // 2 - 23,
            70, 46,
        )
        prize.setGeometry(start_rect)
        prize.show()

        end_rect = QRect(self.width() // 2 - 90, self.height() // 2 - 60, 180, 120)

        self._win_timer = QTimer(self)
        self._win_frame = 0

        def step_win():
            self._win_frame += 1
            ratio = min(1.0, self._win_frame / 45.0)
            cur_x = start_rect.x() + (end_rect.x() - start_rect.x()) * ratio
            cur_y = start_rect.y() + (end_rect.y() - start_rect.y()) * ratio
            cur_w = start_rect.width() + (end_rect.width() - start_rect.width()) * ratio
            cur_h = start_rect.height() + (end_rect.height() - start_rect.height()) * ratio
            prize.setGeometry(int(cur_x), int(cur_y), int(cur_w), int(cur_h))
            if ratio >= 1.0:
                self._win_timer.stop()
                QTimer.singleShot(600, lambda: self.game_finished.emit(self.state.balls_landed, self.state.attempts))

        self._win_timer.timeout.connect(step_win)
        self._win_timer.start(16)