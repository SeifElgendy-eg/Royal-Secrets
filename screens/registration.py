import re

from PySide6.QtCore import Qt, QRegularExpression, Signal
from PySide6.QtGui import QRegularExpressionValidator, QFont
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QLineEdit, QWidget, QPushButton, QMessageBox,
)

from core.config import EGYPT_MOBILE_REGEX, EMAIL_REGEX, EGYPT_AREAS
from core.database import insert_registration
from widgets import PalaceBackdrop, BandField, FieldCaption, SearchableComboRow


class RegistrationScreen(PalaceBackdrop):
    """Screen 1: name + mobile + area, styled as gold bands over the
    palace background, with the sponsor footer pinned to the bottom."""

    registration_complete = Signal(str)  # emits the player's name on success

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        title_label = QLabel("THE SECRET ROYALS\nKEPT FOR PERFECT HAIR")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Georgia", 22, QFont.Bold))
        title_label.setStyleSheet("color: #f4e4b8;")

        subtitle_label = QLabel("Tell us a little about yourself to begin")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setFont(QFont("Georgia", 12))
        subtitle_label.setStyleSheet("color: #d9c9a3;")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Your name")

        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("01XXXXXXXXX")
        mobile_validator = QRegularExpressionValidator(QRegularExpression(r"^\d{0,11}$"))
        self.mobile_input.setValidator(mobile_validator)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your@email.com")

        self.area_row = SearchableComboRow("Select your area", EGYPT_AREAS)

        self.name_band = BandField(self.name_input)
        self.mobile_band = BandField(self.mobile_input)
        self.email_band = BandField(self.email_input)
        self.area_band = BandField(self.area_row.combo)

        submit_button = QPushButton("SUBMIT")
        submit_button.setCursor(Qt.PointingHandCursor)
        submit_button.setFixedHeight(48)
        submit_button.setFont(QFont("Georgia", 13, QFont.Bold))
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #c9a24b;
                color: #241733;
                border-radius: 24px;
                padding: 0 40px;
                border: 2px solid #f4e4b8;
            }
            QPushButton:hover { background-color: #ddb968; }
            QPushButton:pressed { background-color: #b48d3e; }
        """)
        submit_button.clicked.connect(self._on_submit)

        form = QVBoxLayout()
        form.setSpacing(14)
        form.addWidget(FieldCaption("Name"))
        form.addSpacing(8)
        form.addWidget(self.name_band)
        form.addSpacing(4)
        form.addWidget(FieldCaption("Mobile"))
        form.addSpacing(8)
        form.addWidget(self.mobile_band)
        form.addSpacing(4)
        form.addWidget(FieldCaption("Email"))
        form.addSpacing(8)
        form.addWidget(self.email_band)
        form.addSpacing(4)
        form.addWidget(FieldCaption("Area"))
        form.addSpacing(8)
        form.addWidget(self.area_band)
        form.addSpacing(16)
        form.addWidget(submit_button, alignment=Qt.AlignCenter)

        form_wrap = QWidget()
        form_wrap.setLayout(form)
        form_wrap.setMaximumWidth(560)
        form_wrap.setStyleSheet("background: transparent;")

        outer = QVBoxLayout(self)
        outer.addSpacing(50)
        outer.addWidget(title_label)
        outer.addWidget(subtitle_label)
        outer.addSpacing(30)
        outer.addWidget(form_wrap, alignment=Qt.AlignHCenter)
        outer.addStretch()
        outer.addSpacing(140)  # keep clear of the footer art

    def _on_submit(self):
        name = self.name_input.text().strip()
        mobile = self.mobile_input.text().strip()
        email = self.email_input.text().strip()
        area = self.area_row.current_text().strip()

        if not name:
            QMessageBox.warning(self, "Missing info", "Please enter your name.")
            return

        if not re.match(EGYPT_MOBILE_REGEX, mobile):
            QMessageBox.warning(
                self, "Invalid mobile number",
                "Enter a valid Egyptian mobile number (e.g. 01012345678)."
            )
            return

        if not re.match(EMAIL_REGEX, email):
            QMessageBox.warning(
                self, "Invalid email",
                "Enter a valid email address (e.g. name@example.com)."
            )
            return

        if not area or area not in EGYPT_AREAS:
            QMessageBox.warning(self, "Invalid area", "Please select a valid area.")
            return

        success, error_message = insert_registration(name, mobile, email, area)
        if not success:
            QMessageBox.warning(self, "Registration failed", error_message)
            return

        self._clear_form()
        self.registration_complete.emit(name)

    def _clear_form(self):
        self.name_input.clear()
        self.mobile_input.clear()
        self.email_input.clear()
        self.area_row.combo.setCurrentIndex(-1)
        self.area_row.combo.clearEditText()
