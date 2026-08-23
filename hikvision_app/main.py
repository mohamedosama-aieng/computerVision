from __future__ import annotations

import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .ui import MainWindow, apply_dark_palette


def main() -> int:
    QCoreApplication.setOrganizationName("OctoBotSolutions")
    QCoreApplication.setApplicationName("HikvisionSecureViewer")
    app = QApplication(sys.argv)
    apply_dark_palette(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
