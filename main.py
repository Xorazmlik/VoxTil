"""
LingvaKaraoke - dasturni ishga tushirish nuqtasi.

Ishga tushirish:
    python main.py

To'liq o'rnatish yo'riqnomasi uchun README.md faylini ko'ring.
"""

import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import build_stylesheet, make_app_icon


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LingvaKaraoke")
    app.setStyleSheet(build_stylesheet())
    app.setWindowIcon(make_app_icon())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
