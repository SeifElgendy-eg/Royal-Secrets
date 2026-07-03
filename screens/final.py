from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from core.config import PRODUCT_EMOJI, PRODUCT_NAME, PRODUCT_TAGLINE


class FinalScreen(QWidget):
    """Screen 4: static reveal page after the chest is won. No buttons by
    design — the organizer resets the app for the next player (Ctrl+Shift+R).

    Sponsor content (emoji/name/tagline) lives in core.config, not here —
    swapping sponsors is a config edit, not a UI-code edit."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1c1330;")

        product_placeholder = QLabel(PRODUCT_EMOJI)
        product_placeholder.setAlignment(Qt.AlignCenter)
        product_placeholder.setFont(QFont("Arial", 72))

        headline = QLabel(PRODUCT_NAME)
        headline.setAlignment(Qt.AlignCenter)
        headline.setFont(QFont("Arial", 24, QFont.Bold))
        headline.setStyleSheet("color: #c9a24b;")

        tagline = QLabel(PRODUCT_TAGLINE)
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setFont(QFont("Arial", 13))
        tagline.setStyleSheet("color: #f4e4b8;")

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(product_placeholder, alignment=Qt.AlignCenter)
        layout.addSpacing(16)
        layout.addWidget(headline, alignment=Qt.AlignCenter)
        layout.addWidget(tagline, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.setLayout(layout)
