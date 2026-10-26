"""Locate pinned applications in the GNOME desktop dock."""

from __future__ import annotations

import ast
from collections.abc import Mapping
import subprocess

from PySide6.QtCore import QPoint, QRect


class DockTargetError(RuntimeError):
    """Raised when the real desktop dock cannot be located."""


def _parse_gvariant(value: str) -> object:
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError) as error:
        raise DockTargetError("تعذر قراءة إعدادات Dock النظام.") from error


def _read_gnome_dock_settings() -> dict[str, object]:
    try:
        dock_result = subprocess.run(
            [
                "gsettings",
                "list-recursively",
                "org.gnome.shell.extensions.dash-to-dock",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        favorites_result = subprocess.run(
            ["gsettings", "get", "org.gnome.shell", "favorite-apps"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except FileNotFoundError as error:
        raise DockTargetError("تعذر الوصول إلى إعدادات Dock النظام.") from error
    except subprocess.TimeoutExpired as error:
        raise DockTargetError("انتهت مهلة قراءة Dock النظام.") from error
    except subprocess.CalledProcessError as error:
        details = error.stderr.strip() or "إعدادات GNOME Dock غير متاحة."
        raise DockTargetError(details) from error

    relevant_keys = {
        "dash-max-icon-size",
        "dock-position",
        "extend-height",
        "show-apps-at-top",
        "show-favorites",
        "show-show-apps-button",
        "show-trash",
    }
    settings: dict[str, object] = {}
    for line in dock_result.stdout.splitlines():
        fields = line.split(maxsplit=2)
        if len(fields) == 3 and fields[1] in relevant_keys:
            settings[fields[1]] = _parse_gvariant(fields[2])
    settings["favorite-apps"] = _parse_gvariant(favorites_result.stdout)
    return settings


def chrome_dock_icon_position(
    screen_geometry: QRect,
    settings: Mapping[str, object] | None = None,
) -> QPoint:
    """Estimate the center of Chrome's pinned icon from GNOME dock settings."""
    dock = dict(settings) if settings is not None else _read_gnome_dock_settings()
    favorites = dock.get("favorite-apps")
    if not isinstance(favorites, list) or not all(
        isinstance(item, str) for item in favorites
    ):
        raise DockTargetError("تعذر قراءة التطبيقات المثبتة في Dock النظام.")
    chrome_index = next(
        (
            index
            for index, app_id in enumerate(favorites)
            if app_id.casefold().startswith(
                ("google-chrome", "com.google.chrome")
            )
        ),
        None,
    )
    if chrome_index is None or not dock.get("show-favorites", True):
        raise DockTargetError("ثبّت Chrome في Dock النظام أولًا.")

    try:
        icon_size = int(dock["dash-max-icon-size"])
    except (KeyError, TypeError, ValueError) as error:
        raise DockTargetError("تعذر تحديد حجم أيقونات Dock النظام.") from error
    if not 16 <= icon_size <= 128:
        raise DockTargetError("حجم أيقونات Dock النظام غير صالح.")

    position = str(dock.get("dock-position", "LEFT")).upper()
    if position not in {"LEFT", "RIGHT", "TOP", "BOTTOM"}:
        raise DockTargetError("موضع Dock النظام غير معروف.")

    show_apps = bool(dock.get("show-show-apps-button", True))
    show_trash = bool(dock.get("show-trash", False))
    show_apps_at_top = bool(dock.get("show-apps-at-top", False))
    leading_items = int(show_apps and show_apps_at_top)
    cell_size = icon_size + 12
    item_count = len(favorites) + int(show_apps) + int(show_trash)
    item_offset = (chrome_index + leading_items) * cell_size + cell_size // 2

    if position in {"LEFT", "RIGHT"}:
        x = (
            screen_geometry.left() + icon_size // 2 + 8
            if position == "LEFT"
            else screen_geometry.right() - icon_size // 2 - 8
        )
        if dock.get("extend-height", False):
            y = screen_geometry.top() + item_offset
        else:
            y = screen_geometry.center().y() - item_count * cell_size // 2 + item_offset
        return QPoint(x, y)

    y = (
        screen_geometry.top() + icon_size // 2 + 8
        if position == "TOP"
        else screen_geometry.bottom() - icon_size // 2 - 8
    )
    x = screen_geometry.center().x() - item_count * cell_size // 2 + item_offset
    return QPoint(x, y)
