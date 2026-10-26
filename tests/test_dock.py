import pytest
from PySide6.QtCore import QPoint, QRect

from ember.dock import DockTargetError, chrome_dock_icon_position


def test_chrome_dock_position_uses_pinned_order_and_dock_geometry() -> None:
    screen = QRect(0, 0, 1366, 768)
    settings = {
        "favorite-apps": [
            "org.gnome.Nautilus.desktop",
            "google-chrome.desktop",
            "org.gnome.Settings.desktop",
            "org.gnome.Terminal.desktop",
        ],
        "dock-position": "LEFT",
        "dash-max-icon-size": 34,
        "show-show-apps-button": True,
        "show-apps-at-top": False,
        "show-trash": True,
        "extend-height": False,
    }

    assert chrome_dock_icon_position(screen, settings) == QPoint(25, 314)


def test_chrome_dock_position_requires_pinned_chrome() -> None:
    with pytest.raises(DockTargetError, match="ثبّت Chrome"):
        chrome_dock_icon_position(
            QRect(0, 0, 1366, 768),
            {
                "favorite-apps": ["org.gnome.Nautilus.desktop"],
                "dock-position": "LEFT",
                "dash-max-icon-size": 34,
            },
        )
