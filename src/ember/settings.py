"""Persistent application preferences and keyring-backed API credentials."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys

from PySide6.QtCore import QSettings

KEYRING_SERVICE = "Ember Desktop Companion"
KEYRING_USERNAME = "gemini-api-key"

TOOL_NAMES = (
    ("open_app", "فتح تطبيق"),
    ("open_url", "فتح رابط"),
    ("focus_window", "تفعيل نافذة"),
    ("list_windows", "عرض النوافذ"),
    ("type_text", "كتابة نص"),
    ("press_keys", "ضغط مفاتيح"),
    ("click", "النقر"),
    ("scroll", "التمرير"),
    ("take_screenshot_and_describe", "لقطة شاشة ووصفها"),
    ("set_volume", "ضبط مستوى الصوت"),
    ("open_bluetooth_settings", "إعدادات Bluetooth"),
    ("close_active_window", "إغلاق النافذة النشطة"),
    ("remember_this", "حفظ واسترجاع الذاكرة"),
    ("media_control", "التحكم بالوسائط"),
    ("read_clipboard", "قراءة الحافظة"),
    ("write_clipboard", "الكتابة إلى الحافظة"),
    ("create_file", "إنشاء ملف"),
    ("read_file", "قراءة ملف"),
    ("run_shell_command", "أمر طرفية مقيّد"),
    ("run_terminal_command", "تشغيل أمر مطلوب في Terminal"),
    ("close_ember_terminal", "إغلاق نافذة Terminal التي فتحها Ember"),
    ("open_system_settings", "فتح صفحة من إعدادات النظام"),
    ("set_bluetooth_power", "تشغيل Bluetooth أو إيقافه"),
    ("repair_microphone", "إصلاح إعداد إدخال الميكروفون"),
    ("close_window", "إغلاق نافذة محددة والتحقق من ذلك"),
)

AUTO_TOOLS = {
    "open_app",
    "open_url",
    "type_text",
    "click",
    "scroll",
    "set_volume",
    "open_bluetooth_settings",
    "run_shell_command",
    "run_terminal_command",
    "close_ember_terminal",
    "list_windows",
    "close_window",
    "open_system_settings",
    "set_bluetooth_power",
    "repair_microphone",
}
TOOL_PERMISSION_MIGRATION_VERSION = 5


def default_tool_tiers() -> dict[str, str]:
    return {
        name: "auto" if name in AUTO_TOOLS else "ask"
        for name, _label in TOOL_NAMES
    }


def default_allowed_folders() -> tuple[str, ...]:
    return tuple(
        str(path)
        for path in (
            Path.home() / "Documents",
            Path.home() / "Downloads",
        )
        if path.is_dir()
    )


@dataclass
class AppSettings:
    model: str = "gemini-3.8-flash"
    response_language: str = "auto"
    same_language: bool = True
    concise_replies: bool = True
    speak_answers: bool = True
    voice_name: str = "Kore"
    voice_volume: int = 80
    sounds_enabled: bool = True
    sound_volume: int = 65
    wake_word_enabled: bool = True
    stand_on_windows: bool = True
    walking_speed: int = 100
    display_scale: float = 0.70
    sleep_delay_minutes: int = 5
    sleep_corner: str = "top-random"
    monitor: str = "primary"
    tool_tiers: dict[str, str] = field(default_factory=default_tool_tiers)
    allowed_folders: tuple[str, ...] = field(default_factory=default_allowed_folders)
    emergency_hotkey: str = "Ctrl+Alt+S"
    push_to_talk_hotkey: str = ""
    autostart: bool = False


class SettingsStore:
    def __init__(self, settings: QSettings | None = None) -> None:
        self.settings = settings or QSettings("Ember", "Ember")

    def load(self) -> AppSettings:
        defaults = AppSettings()
        values = {
            "model": self._value("model", defaults.model, str),
            "response_language": self._value(
                "response_language", defaults.response_language, str
            ),
            "same_language": self._value(
                "same_language", defaults.same_language, bool
            ),
            "concise_replies": self._value(
                "concise_replies", defaults.concise_replies, bool
            ),
            "speak_answers": self._value(
                "speak_answers", defaults.speak_answers, bool
            ),
            "voice_name": self._value("voice_name", defaults.voice_name, str),
            "voice_volume": self._value(
                "voice_volume", defaults.voice_volume, int
            ),
            "sounds_enabled": self._value(
                "sounds_enabled", defaults.sounds_enabled, bool
            ),
            "sound_volume": self._value(
                "sound_volume", defaults.sound_volume, int
            ),
            "wake_word_enabled": self._value(
                "wake_word_enabled", defaults.wake_word_enabled, bool
            ),
            "stand_on_windows": self._value(
                "stand_on_windows", defaults.stand_on_windows, bool
            ),
            "walking_speed": self._value(
                "walking_speed", defaults.walking_speed, int
            ),
            "display_scale": self._value(
                "display_scale", defaults.display_scale, float
            ),
            "sleep_delay_minutes": self._value(
                "sleep_delay_minutes", defaults.sleep_delay_minutes, int
            ),
            "sleep_corner": "top-random",
            "monitor": self._value("monitor", defaults.monitor, str),
            "emergency_hotkey": self._value(
                "emergency_hotkey", defaults.emergency_hotkey, str
            ),
            "push_to_talk_hotkey": self._value(
                "push_to_talk_hotkey", defaults.push_to_talk_hotkey, str
            ),
            "autostart": self._value("autostart", defaults.autostart, bool),
        }
        saved_folders = self.settings.value(
            "allowed_folders", list(defaults.allowed_folders)
        )
        if isinstance(saved_folders, str):
            saved_folders = [saved_folders]
        values["allowed_folders"] = tuple(str(path) for path in saved_folders)
        tool_tiers = {
            name: self._value(f"tools/{name}", tier, str)
            for name, tier in defaults.tool_tiers.items()
        }
        migration_version = self._value(
            "tool_permission_migration_version", 0, int
        )
        if migration_version < TOOL_PERMISSION_MIGRATION_VERSION:
            for name in (
                "open_app",
                "type_text",
                "click",
                "scroll",
                "open_bluetooth_settings",
                "run_shell_command",
                "run_terminal_command",
                "close_ember_terminal",
                "list_windows",
                "close_window",
                "open_system_settings",
                "set_bluetooth_power",
                "repair_microphone",
            ):
                if tool_tiers.get(name) == "ask":
                    tool_tiers[name] = "auto"
                    self.settings.setValue(f"tools/{name}", "auto")
            self.settings.setValue(
                "tool_permission_migration_version",
                TOOL_PERMISSION_MIGRATION_VERSION,
            )
            self.settings.sync()
            if self.settings.status() != QSettings.Status.NoError:
                raise OSError("تعذر تحديث أذونات أدوات سطح المكتب.")
        values["tool_tiers"] = tool_tiers
        return AppSettings(**values)

    def save(self, value: AppSettings) -> None:
        self.settings.clear()
        for name in (
            "model",
            "response_language",
            "same_language",
            "concise_replies",
            "speak_answers",
            "voice_name",
            "voice_volume",
            "sounds_enabled",
            "sound_volume",
            "wake_word_enabled",
            "stand_on_windows",
            "walking_speed",
            "display_scale",
            "sleep_delay_minutes",
            "sleep_corner",
            "monitor",
            "emergency_hotkey",
            "push_to_talk_hotkey",
            "autostart",
        ):
            self.settings.setValue(name, getattr(value, name))
        self.settings.setValue("allowed_folders", list(value.allowed_folders))
        for name, tier in value.tool_tiers.items():
            self.settings.setValue(f"tools/{name}", tier)
        self.settings.setValue(
            "tool_permission_migration_version",
            TOOL_PERMISSION_MIGRATION_VERSION,
        )
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            raise OSError("تعذر حفظ الإعدادات المحلية.")

    def reset(self) -> None:
        self.save(AppSettings())

    def _value(self, key: str, default: object, value_type: type) -> object:
        try:
            return self.settings.value(key, default, type=value_type)
        except (TypeError, ValueError):
            return default


class SecretStorageError(RuntimeError):
    """Raised when the operating-system keyring is unavailable."""


class ApiKeyStore:
    def has_key(self) -> bool:
        return self.get_key() is not None

    def get_key(self) -> str | None:
        import keyring

        try:
            return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except Exception as exc:
            raise SecretStorageError(
                "تعذر الوصول إلى سلسلة مفاتيح النظام. تأكد من تثبيت libsecret "
                "وأن جلستك الرسومية مفتوحة."
            ) from exc

    def set_key(self, value: str) -> None:
        import keyring

        if not value.strip():
            raise SecretStorageError("لا يمكن حفظ مفتاح فارغ.")
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, value)
            if keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME) != value:
                raise SecretStorageError(
                    "لم يؤكد مخزن النظام حفظ المفتاح. أعد المحاولة بعد فتح سلسلة "
                    "مفاتيح النظام."
                )
        except SecretStorageError:
            raise
        except Exception as exc:
            raise SecretStorageError(
                "تعذر حفظ المفتاح في سلسلة مفاتيح النظام. لم يُحفظ في ملف."
            ) from exc

    def delete_key(self) -> None:
        import keyring

        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        except keyring.errors.PasswordDeleteError:
            return
        except Exception as exc:
            raise SecretStorageError(
                "تعذر حذف المفتاح من سلسلة مفاتيح النظام."
            ) from exc


def set_autostart(enabled: bool) -> None:
    autostart_file = Path.home() / ".config" / "autostart" / "ember.desktop"
    if not enabled:
        try:
            autostart_file.unlink(missing_ok=True)
        except OSError as exc:
            raise OSError("تعذر تعطيل التشغيل التلقائي.") from exc
        return

    executable = Path(sys.executable).resolve()
    escaped_executable = (
        str(executable)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("`", "\\`")
    )
    autostart_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        autostart_file.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Ember\n"
            "Comment=Your desktop companion\n"
            f'Exec="{escaped_executable}" -m ember\n'
            "Terminal=false\n"
            "X-GNOME-Autostart-enabled=true\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise OSError("تعذر تفعيل التشغيل التلقائي.") from exc
