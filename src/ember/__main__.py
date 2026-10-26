"""Run the Ember character window."""

from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from .window import CharacterWindow


def _prefer_xwayland() -> None:
    if (
        sys.platform.startswith("linux")
        and os.environ.get("WAYLAND_DISPLAY")
        and os.environ.get("DISPLAY")
    ):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")


def main() -> int:
    _prefer_xwayland()
    app = QApplication(sys.argv)
    app.setApplicationName("Ember")
    window = CharacterWindow()
    window.show()
    window.start_wake_word_listener()
    app.aboutToQuit.connect(window._wake_listener.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
