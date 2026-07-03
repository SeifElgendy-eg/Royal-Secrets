from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter
from PySide6.QtWidgets import QLabel, QComboBox, QCompleter, QPushButton

from core.config import KEY_IMAGE


class FieldCaption(QLabel):
    """Small gold uppercase caption drawn above a band, e.g. 'NAME'."""

    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFont(QFont("Georgia", 11, QFont.Bold))
        self.setStyleSheet("color: #e7c877; letter-spacing: 2px;")


class SearchableComboRow:
    """A label + QComboBox with type-to-search/autocomplete enabled."""

    def __init__(self, label_text, options):
        self.label_text = label_text
        self.combo = QComboBox()
        self.combo.setEditable(True)  # lets the user type to filter
        self.combo.addItems(options)
        self.combo.setCurrentIndex(-1)
        self.combo.lineEdit().setPlaceholderText(label_text)

        # Autocomplete/search behavior
        self.combo.setInsertPolicy(QComboBox.NoInsert)  # don't add typed text as new item
        completer = QCompleter(options, self.combo)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)  # matches anywhere in the string, not just prefix
        self.combo.setCompleter(completer)

    def current_text(self):
        return self.combo.currentText()


class KeyButton(QPushButton):
    """The ornate key (key0001.png), drawn at its native aspect ratio.
    Whoever positions this widget (see RoyalRoomScreen) is responsible for
    keeping the geometry it's given at that same aspect ratio — paintEvent
    then just maps the full pixmap into self.rect(), which scales both
    axes by one identical factor. Never stretched."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap(str(KEY_IMAGE)) if KEY_IMAGE.exists() else QPixmap()
        self.aspect = (self._pixmap.width() / self._pixmap.height()) if not self._pixmap.isNull() else 2.214
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click the key to unlock the chest")
        self.setFlat(True)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(), self._pixmap, self._pixmap.rect())
        painter.end()
