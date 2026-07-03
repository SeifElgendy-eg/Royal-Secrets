from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QFileDialog

from core.database import init_db, export_to_csv, registration_count
from screens import RegistrationScreen, RoyalRoomScreen, FinalScreen
from game import ChestGameScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Royal Secrets")

        init_db()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.registration_screen = RegistrationScreen()
        self.royal_room_screen = RoyalRoomScreen()
        self.final_screen = FinalScreen()

        self.stack.addWidget(self.registration_screen)  # index 0
        self.stack.addWidget(self.royal_room_screen)     # index 1
        self.stack.addWidget(self.final_screen)           # index 2
        # The chest game is created fresh every time the key is clicked, so
        # each player gets a clean, unplayed round.
        self.chest_game_screen = None

        self.registration_screen.registration_complete.connect(self._on_registration_complete)
        self.royal_room_screen.key_clicked.connect(self._on_key_clicked)

        # Organizer-only shortcuts (deliberately hidden — no visible buttons):
        #   Ctrl+Shift+E -> export all registrations to CSV
        #   Ctrl+Shift+R -> reset the app back to Registration for the next player
        #   Ctrl+Shift+F -> jump straight to the Final screen (dev/preview only)
        QShortcut(QKeySequence("Ctrl+Shift+E"), self).activated.connect(self._on_export_csv)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self).activated.connect(self._reset_to_registration)
        QShortcut(QKeySequence("Ctrl+Shift+F"), self).activated.connect(self._jump_to_final)

    def _on_registration_complete(self, name: str):
        self.royal_room_screen.set_player_name(name)
        self.stack.setCurrentWidget(self.royal_room_screen)

    def _on_key_clicked(self):
        if self.chest_game_screen is not None:
            self.stack.removeWidget(self.chest_game_screen)
            self.chest_game_screen.deleteLater()

        self.chest_game_screen = ChestGameScreen()
        self.chest_game_screen.game_finished.connect(self._on_game_finished)
        self.stack.addWidget(self.chest_game_screen)
        self.stack.setCurrentWidget(self.chest_game_screen)

    def _on_game_finished(self, balls_landed: int, attempts: int):
        # Static final page — no popup, no buttons, per spec.
        self.stack.setCurrentWidget(self.final_screen)

    def _reset_to_registration(self):
        self.stack.setCurrentWidget(self.registration_screen)

    def _jump_to_final(self):
        """Dev/preview only — lets you see the final reveal without playing
        through registration and the minigame first."""
        self.stack.setCurrentWidget(self.final_screen)

    def _on_export_csv(self):
        """Ctrl+Shift+E — dump every registration collected so far to a CSV
        the organizer picks. Meant to be run once the event is over."""
        count = registration_count()
        if count == 0:
            QMessageBox.information(self, "Nothing to export", "No registrations recorded yet.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Registrations to CSV", "registrations.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        success, result = export_to_csv(path)
        if success:
            QMessageBox.information(
                self, "Export complete", f"Exported {count} registrations to:\n{result}"
            )
        else:
            QMessageBox.warning(self, "Export failed", result)