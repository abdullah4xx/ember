"""Run the Ember character window."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .window import CharacterWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Ember")
    window = CharacterWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
