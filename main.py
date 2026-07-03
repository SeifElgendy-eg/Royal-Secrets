"""Entry point. All actual app wiring lives in app.MainWindow — this file
just boots Qt. Run from the project root: python main.py"""

from PySide6.QtWidgets import QApplication

from app import MainWindow


def main():
    app = QApplication([])
    window = MainWindow()
    window.resize(720, 900)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
