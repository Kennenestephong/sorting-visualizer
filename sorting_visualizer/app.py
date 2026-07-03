from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def build_window() -> MainWindow:
    return MainWindow()


def main() -> int:
    app = QApplication(sys.argv)
    window = build_window()
    window.resize(1000, 700)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
