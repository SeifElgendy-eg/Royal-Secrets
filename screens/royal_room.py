from PySide6.QtCore import Signal

from core.config import ROYAL_ROOM_BACKGROUND, FOOTER_IMAGE
from widgets import PalaceBackdrop, KeyButton


class RoyalRoomScreen(PalaceBackdrop):
    """Screen 2: the palace room. The chest, gold frame, and title/tagline
    are all baked into background0002.png itself — this class only adds
    the personalized welcome line and a clickable key overlay that starts
    the chest game."""

    key_clicked = Signal()

    # Where the key sits on background0002.png, as fractions of the
    # image's own width/height (measured off the approved mockup). Using
    # fractions of the *image* — via background_rect() — rather than the
    # window means the key stays pinned to the velvet cloth in the art at
    # any window size, instead of drifting once the image gets cropped.
    _KEY_CENTER_X_FRAC = 0.523
    _KEY_CENTER_Y_FRAC = 0.748
    _KEY_WIDTH_FRAC = 0.26

    def __init__(self, parent=None):
        super().__init__(background_path=ROYAL_ROOM_BACKGROUND, footer_path=FOOTER_IMAGE, parent=parent)

        # Positioned by absolute geometry (see _position_key_button), not
        # by a layout — it needs to track a fixed spot on the artwork,
        # not flow with the rest of the widgets.
        self.key_button = KeyButton(self)
        self.key_button.clicked.connect(self.key_clicked.emit)
        self._position_key_button()

    def set_player_name(self, name: str):
        # No on-screen display for now (removed — collided with the frame
        # art at wider window sizes). Kept as a no-op entry point so
        # MainWindow's existing call site keeps working if this becomes
        # relevant again later (e.g. personalizing the chest game).
        self.player_name = name

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_key_button()

    def _position_key_button(self):
        rect = self.background_rect()
        if rect.width() <= 0 or rect.height() <= 0:
            return
        width = round(rect.width() * self._KEY_WIDTH_FRAC)
        height = round(width / self.key_button.aspect)
        center_x = rect.x() + rect.width() * self._KEY_CENTER_X_FRAC
        center_y = rect.y() + rect.height() * self._KEY_CENTER_Y_FRAC
        self.key_button.setGeometry(
            round(center_x - width / 2), round(center_y - height / 2), width, height
        )
