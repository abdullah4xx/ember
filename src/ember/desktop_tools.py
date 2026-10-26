"""Permission-gated desktop actions for Ember."""

from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import time
from threading import Event
from typing import Callable
from urllib.parse import urlsplit
import uuid

from PySide6.QtCore import (
    QEventLoop,
    QObject,
    QProcess,
    QThread,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage
from PySide6.QtGui import QCursor, QDesktopServices, QGuiApplication, QImage

_LOGGER = logging.getLogger(__name__)


class DesktopToolError(RuntimeError):
    pass


class ReadOnlyCommandWorker(QThread):
    result_ready = Signal(str, object)

    def __init__(self, request_id: str, command: str) -> None:
        super().__init__()
        self.request_id = request_id
        self.command = command

    def run(self) -> None:
        try:
            output = DesktopToolExecutor._run_read_only_command(self.command)
            result: dict[str, object] = {"text": output}
        except (DesktopToolError, OSError, ValueError) as error:
            result = {"text": f"تعذر تنفيذ الإجراء: {error}"}
        self.result_ready.emit(self.request_id, result)


class DesktopToolWorker(QThread):
    result_ready = Signal(str, object)

    def __init__(
        self,
        request_id: str,
        executor: DesktopToolExecutor,
        name: str,
        arguments: dict[str, object],
    ) -> None:
        super().__init__()
        self.request_id = request_id
        self.executor = executor
        self.name = name
        self.arguments = arguments

    def run(self) -> None:
        try:
            result = self.executor.execute(self.name, self.arguments)
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            result = {"text": f"تعذر تنفيذ الإجراء: {error}"}
        except Exception as error:
            _LOGGER.exception("Desktop action %s failed", self.name)
            result = {"text": f"حدث خطأ أثناء تنفيذ الإجراء: {error}"}
        self.result_ready.emit(self.request_id, result)


class _PortalResponse(QObject):
    received = Signal(int, dict)

    @Slot("uint", "QVariantMap")
    def on_response(self, code: int, results: dict) -> None:
        self.received.emit(code, results)


class PortalRemoteInput:
    SERVICE = "org.freedesktop.portal.Desktop"
    PATH = "/org/freedesktop/portal/desktop"
    REMOTE_DESKTOP = "org.freedesktop.portal.RemoteDesktop"
    REQUEST = "org.freedesktop.portal.Request"
    SESSION = "org.freedesktop.portal.Session"

    def __init__(self) -> None:
        self._bus = QDBusConnection.sessionBus()
        self._remote = QDBusInterface(
            self.SERVICE, self.PATH, self.REMOTE_DESKTOP, self._bus
        )
        self._session_handle: str | None = None

    def _interface(self, path: str, interface: str) -> QDBusInterface:
        result = QDBusInterface(self.SERVICE, path, interface, self._bus)
        if not result.isValid():
            raise DesktopToolError("تعذر الاتصال بخدمة التحكم الآمن في سطح المكتب.")
        return result

    @staticmethod
    def _check_reply(reply: QDBusMessage) -> list[object]:
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise DesktopToolError(reply.errorMessage())
        return reply.arguments()

    def _request(
        self,
        interface: QDBusInterface,
        method: str,
        args: tuple[object, ...],
        cancel_event: Event | None = None,
    ) -> dict:
        reply = self._check_reply(interface.call(method, *args))
        if not reply:
            raise DesktopToolError(f"لم تُرجع خدمة سطح المكتب طلب {method}.")
        request_path = str(reply[0])
        receiver = _PortalResponse()
        loop = QEventLoop()
        response: list[tuple[int, dict]] = []
        receiver.received.connect(
            lambda code, values: (response.append((code, values)), loop.quit())
        )
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        cancel_timer: QTimer | None = None
        if cancel_event is not None:
            cancel_timer = QTimer()

            def cancel_request() -> None:
                if not cancel_event.is_set():
                    return
                QDBusInterface(
                    self.SERVICE,
                    request_path,
                    self.REQUEST,
                    self._bus,
                ).call("Close")
                loop.quit()

            cancel_timer.setInterval(100)
            cancel_timer.timeout.connect(cancel_request)
        connected = self._bus.connect(
            self.SERVICE,
            request_path,
            self.REQUEST,
            "Response",
            receiver,
            "1_on_response(uint,QVariantMap)",
        )
        if not connected:
            raise DesktopToolError("تعذر استقبال موافقة نظام سطح المكتب.")
        if cancel_timer is not None:
            cancel_timer.start()
        timer.start(120_000)
        loop.exec()
        if cancel_timer is not None:
            cancel_timer.stop()
        self._bus.disconnect(
            self.SERVICE,
            request_path,
            self.REQUEST,
            "Response",
            receiver,
            "1_on_response(uint,QVariantMap)",
        )
        if cancel_event is not None and cancel_event.is_set():
            raise DesktopToolError("أُوقفت مشاهدة الشاشة.")
        if not response:
            raise DesktopToolError("انتهت مهلة انتظار موافقة نظام سطح المكتب.")
        code, values = response[0]
        if code != 0:
            raise DesktopToolError("لم تتم الموافقة على طلب سطح المكتب.")
        return values

    def _ensure_session(self) -> str:
        if self._session_handle is not None:
            return self._session_handle
        token = uuid.uuid4().hex
        create = self._interface(self.PATH, self.REMOTE_DESKTOP)
        created = self._request(
            create,
            "CreateSession",
            (
                {
                    "handle_token": f"ember_{token}",
                    "session_handle_token": f"ember_session_{token}",
                },
            ),
        )
        session_handle = str(created.get("session_handle", ""))
        if not session_handle:
            raise DesktopToolError("لم تُنشأ جلسة تحكم آمنة.")
        self._request(
            create,
            "SelectDevices",
            (
                session_handle,
                {"handle_token": f"ember_devices_{token}", "types": 3},
            ),
        )
        self._request(
            create,
            "Start",
            (
                session_handle,
                "",
                {"handle_token": f"ember_start_{token}"},
            ),
        )
        self._session_handle = session_handle
        return session_handle

    def _notify(self, method: str, *args: object) -> None:
        session = self._ensure_session()
        self._check_reply(self._remote.call(method, session, {}, *args))

    def click(self, x: int, y: int) -> None:
        pointer = QCursor.pos()
        self._notify("NotifyPointerMotion", float(x - pointer.x()), float(y - pointer.y()))
        self._notify("NotifyPointerButton", 0x110, 1)
        self._notify("NotifyPointerButton", 0x110, 0)

    def type_text(self, text: str) -> None:
        for character in text:
            codepoint = ord(character)
            if character == "\n":
                keysym = 0xFF0D
            elif character == "\t":
                keysym = 0xFF09
            elif codepoint < 0x100:
                keysym = codepoint
            else:
                keysym = 0x01000000 | codepoint
            self._notify("NotifyKeyboardKeysym", keysym, 1)
            self._notify("NotifyKeyboardKeysym", keysym, 0)

    def press_keys(self, *keysyms: int) -> None:
        if not keysyms:
            return
        self._ensure_session()
        pressed: list[int] = []
        try:
            for keysym in keysyms:
                self._notify("NotifyKeyboardKeysym", keysym, 1)
                pressed.append(keysym)
        finally:
            for keysym in reversed(pressed):
                self._notify("NotifyKeyboardKeysym", keysym, 0)

    def scroll(self, x: int, y: int, direction: str, amount: int) -> None:
        pointer = QCursor.pos()
        self._notify("NotifyPointerMotion", float(x - pointer.x()), float(y - pointer.y()))
        steps = amount if direction == "down" else -amount
        self._notify("NotifyPointerAxisDiscrete", 0, steps)


class DesktopToolExecutor:
    READ_ONLY_COMMANDS = {
        "pwd": ["pwd"],
        "ls": ["ls", "-la"],
        "git status": ["git", "status", "--short"],
        "git diff --stat": ["git", "diff", "--stat"],
        "df -h": ["df", "-h"],
        "uname -a": ["uname", "-a"],
    }
    BLOCKED_TERMINAL_COMMANDS = {
        "apt",
        "apt-get",
        "chmod",
        "chown",
        "dd",
        "fdisk",
        "kill",
        "killall",
        "mkfs",
        "mount",
        "mv",
        "pacman",
        "pkexec",
        "pkill",
        "poweroff",
        "python",
        "python3",
        "reboot",
        "rm",
        "rmdir",
        "ruby",
        "sh",
        "shutdown",
        "sudo",
        "su",
        "systemctl",
        "bash",
        "dash",
        "node",
        "umount",
        "yum",
    }
    APP_ALIASES = {
        "terminal": "terminal",
        "gnome terminal": "terminal",
        "ubuntu terminal": "terminal",
        "console": "terminal",
        "chrome": "google chrome",
        "google chrome": "google chrome",
        "جوجل كروم": "google chrome",
        "كروم": "google chrome",
        "firefox": "firefox",
        "فايرفوكس": "firefox",
    }
    TERMINAL_APP_NAMES = {
        "terminal",
        "gnome terminal",
        "ubuntu terminal",
        "console",
        "gnome console",
        "kgx",
        "xterm",
        "konsole",
    }
    SYSTEM_SETTINGS_PAGES = {
        "bluetooth": ["bluetooth"],
        "display": ["display"],
        "keyboard": ["keyboard"],
        "mouse": ["mouse"],
        "network": ["wifi"],
        "power": ["power"],
        "sound": ["sound"],
    }

    def __init__(
        self,
        application_dirs: tuple[Path, ...] | None = None,
        launcher: Callable[[str, list[str]], object] | None = None,
        open_url: Callable[[QUrl], bool] | None = None,
        remote_input: PortalRemoteInput | None = None,
        terminal_lookup: Callable[[str], str | None] | None = None,
        terminal_process_factory: Callable[[], QProcess] = QProcess,
    ) -> None:
        self.application_dirs = application_dirs or self._application_dirs()
        self._launcher = launcher or QProcess.startDetached
        self._open_url = open_url or QDesktopServices.openUrl
        self._remote_input = remote_input or PortalRemoteInput()
        self._terminal_lookup = terminal_lookup or shutil.which
        self._terminal_process_factory = terminal_process_factory
        self._terminal_processes: list[QProcess] = []

    @staticmethod
    def _application_dirs() -> tuple[Path, ...]:
        data_home = Path(
            os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        )
        data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
        paths = [
            data_home / "applications",
            *(Path(path) / "applications" for path in data_dirs.split(":") if path),
            Path.home() / ".local/share/flatpak/exports/share/applications",
            Path("/var/lib/flatpak/exports/share/applications"),
        ]
        return tuple(path for path in paths if path.is_dir())

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", value.casefold()).strip()

    def _find_application(self, app_name: str) -> str | None:
        requested = self._normalize(app_name)
        requested = self.APP_ALIASES.get(requested, requested)
        for directory in self.application_dirs:
            for desktop_file in sorted(directory.rglob("*.desktop")):
                parser = configparser.ConfigParser(interpolation=None)
                parser.optionxform = str
                try:
                    parser.read(desktop_file, encoding="utf-8")
                    entry = parser["Desktop Entry"]
                except (OSError, KeyError, configparser.Error):
                    continue
                if entry.get("Hidden", "false").casefold() == "true":
                    continue
                if entry.get("NoDisplay", "false").casefold() == "true":
                    continue
                names = {
                    self._normalize(desktop_file.stem.replace("-", " ")),
                }
                names.update(
                    self._normalize(value)
                    for key, value in entry.items()
                    if key == "Name" or key.startswith("Name[")
                )
                if requested not in names:
                    if (
                        requested != "terminal"
                        or not names.intersection(self.TERMINAL_APP_NAMES)
                    ):
                        continue
                return desktop_file.relative_to(directory).as_posix().replace(
                    "/", "-"
                ).removesuffix(".desktop")
        return None

    def _open_application(self, app_name: object) -> str:
        if not isinstance(app_name, str) or not app_name.strip() or len(app_name) > 128:
            raise DesktopToolError("اسم التطبيق غير صالح.")
        desktop_id = self._find_application(app_name)
        if desktop_id is None:
            raise DesktopToolError(f"لم أجد تطبيقًا مثبتًا باسم «{app_name}».")
        result = self._launcher("gtk-launch", [desktop_id])
        started = result[0] if isinstance(result, tuple) else bool(result)
        if not started:
            raise DesktopToolError(f"تعذر فتح التطبيق «{app_name}».")
        return f"تم فتح {app_name}."

    def _open_web_url(self, value: object) -> str:
        if not isinstance(value, str) or len(value) > 2048:
            raise DesktopToolError("الرابط غير صالح.")
        parsed = urlsplit(value.strip())
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(ord(char) < 32 for char in value)
        ):
            raise DesktopToolError("يمكن فتح روابط http أو https فقط.")
        if not self._open_url(QUrl(value.strip())):
            raise DesktopToolError("تعذر فتح الرابط في المتصفح.")
        return "تم فتح الرابط."

    def focus_address_bar(self) -> None:
        self._remote_input.press_keys(0xFFE3, ord("l"))

    @staticmethod
    def _run_read_only_command(command: object) -> str:
        if (
            not isinstance(command, str)
            or command not in DesktopToolExecutor.READ_ONLY_COMMANDS
        ):
            raise DesktopToolError("هذا الأمر غير موجود في قائمة أوامر القراءة فقط.")
        try:
            result = subprocess.run(
                DesktopToolExecutor.READ_ONLY_COMMANDS[command],
                cwd=Path.cwd(),
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError as error:
            raise DesktopToolError("الأمر المطلوب غير مثبت على هذا الجهاز.") from error
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError("انتهت مهلة أمر الطرفية.") from error
        output = (result.stdout or result.stderr).strip()
        if result.returncode:
            raise DesktopToolError(output or "فشل أمر الطرفية.")
        return output[:4000] or "اكتمل الأمر دون مخرجات."

    def _run_terminal_command(self, command: object) -> str:
        if (
            not isinstance(command, str)
            or not command.strip()
            or len(command) > 400
            or any(ord(char) < 32 for char in command)
        ):
            raise DesktopToolError("أمر الطرفية فارغ أو غير صالح.")
        try:
            arguments = shlex.split(command)
        except ValueError as error:
            raise DesktopToolError("تعذر تحليل أمر الطرفية.") from error
        if any(argument in {";", "&&", "||", "|", "&", ">", "<"} for argument in arguments):
            raise DesktopToolError("شغّل أمرًا واحدًا فقط دون ربط أوامر أخرى.")
        if not arguments or "/" in arguments[0]:
            raise DesktopToolError("اكتب اسم أمر مثبتًا، وليس مسارًا تنفيذيًا.")
        executable = arguments[0].casefold()
        if executable in self.BLOCKED_TERMINAL_COMMANDS:
            raise DesktopToolError("هذا الأمر قد يغيّر النظام أو يحذف ملفات.")
        program_path = self._terminal_lookup(arguments[0])
        if program_path is None:
            raise DesktopToolError(
                f"الأمر «{arguments[0]}» غير مثبت أو غير موجود في PATH."
            )
        ptyxis_path = self._terminal_lookup("ptyxis")
        gnome_terminal_path = self._terminal_lookup("gnome-terminal")
        xterm_path = self._terminal_lookup("xterm")
        if ptyxis_path:
            terminal_path = ptyxis_path
            terminal_args = [
                "--standalone",
                "--new-window",
                "--title=Ember CLI",
                "--",
            ]
        elif gnome_terminal_path:
            terminal_path = gnome_terminal_path
            terminal_args = ["--wait", "--window", "--title=Ember CLI", "--"]
        elif xterm_path:
            terminal_path = xterm_path
            terminal_args = ["-T", "Ember CLI", "-e"]
        else:
            raise DesktopToolError(
                "لم يتم العثور على Terminal يمكن لـEmber إدارته بأمان."
            )
        script = (
            'printf "$ %s\\n" "$*"; '
            '"$@"; status=$?; '
            'printf "\\n[exit code: %s]\\n" "$status"; '
            'exec "${SHELL:-/bin/bash}"'
        )
        process = self._terminal_process_factory()
        process.setProgram(terminal_path)
        process.setArguments(
            [
                *terminal_args,
                "bash",
                "-lc",
                script,
                "ember-terminal",
                *arguments,
            ]
        )
        process.start()
        if not process.waitForStarted(5000):
            raise DesktopToolError(
                process.errorString() or "تعذر فتح Terminal لتشغيل الأمر."
            )
        self._terminal_processes.append(process)
        return "فُتحت نافذة Terminal وشُغّل الأمر الذي طلبته."

    def _close_ember_terminal(self) -> str:
        while self._terminal_processes:
            process = self._terminal_processes.pop()
            if process.state() == QProcess.ProcessState.NotRunning:
                process.deleteLater()
                continue
            process.terminate()
            if not process.waitForFinished(3000):
                raise DesktopToolError(
                    "أُرسل طلب الإغلاق، لكن Terminal لم يغلق نفسه بعد."
                )
            process.deleteLater()
            return "أُغلقت نافذة Terminal التي فتحها Ember."
        raise DesktopToolError(
            "لا توجد نافذة Terminal مفتوحة أنشأها Ember لإغلاقها."
        )

    @staticmethod
    def _window_list() -> list[tuple[str, str]]:
        wmctrl = shutil.which("wmctrl")
        if wmctrl is None:
            raise DesktopToolError(
                "تعذر تعداد النوافذ بأمان؛ أداة wmctrl غير متاحة."
            )
        try:
            result = subprocess.run(
                [wmctrl, "-l", "-p"],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError(
                "انتهت مهلة تعداد النوافذ."
            ) from error
        if result.returncode:
            raise DesktopToolError(
                result.stderr.strip() or "تعذر تعداد النوافذ."
            )
        windows = []
        for line in result.stdout.splitlines():
            fields = line.split(maxsplit=4)
            if len(fields) != 5:
                continue
            try:
                process_id = int(fields[2])
            except ValueError:
                continue
            if process_id != os.getpid():
                windows.append((fields[0], fields[4]))
        return windows

    def _list_windows(self) -> str:
        windows = self._window_list()
        if not windows:
            return "لم يتم العثور على نوافذ مفتوحة يمكن إدارتها."
        return "\n".join(
            f"{window_id}\t{title}" for window_id, title in windows
        )

    def _close_window(self, title: object) -> str:
        if not isinstance(title, str) or not title.strip() or len(title) > 200:
            raise DesktopToolError("عنوان النافذة غير صالح.")
        requested_title = title.strip().casefold()
        windows = self._window_list()
        matches = [
            (window_id, window_title)
            for window_id, window_title in windows
            if window_title.casefold() == requested_title
        ]
        if not matches:
            matches = [
                (window_id, window_title)
                for window_id, window_title in windows
                if requested_title in window_title.casefold()
            ]
        if not matches:
            raise DesktopToolError(
                f"لم أجد نافذة متاحة تطابق «{title.strip()}» في مدير النوافذ."
            )
        if len(matches) > 1:
            raise DesktopToolError(
                "يوجد أكثر من نافذة بهذا العنوان؛ لم أغلق أي نافذة."
            )
        window_id, window_title = matches[0]
        wmctrl = shutil.which("wmctrl")
        if wmctrl is None:
            raise DesktopToolError(
                "تعذر إغلاق النافذة بأمان؛ أداة wmctrl غير متاحة."
            )
        try:
            result = subprocess.run(
                [wmctrl, "-ic", window_id],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError(
                "انتهت مهلة إرسال طلب إغلاق النافذة."
            ) from error
        if result.returncode:
            raise DesktopToolError(
                result.stderr.strip() or "تعذر إرسال طلب إغلاق النافذة."
            )
        for _attempt in range(10):
            if all(
                current_id != window_id
                for current_id, _current_title in self._window_list()
            ):
                return f"أُغلقت نافذة «{window_title}» وتحققت من اختفائها."
            time.sleep(0.1)
        raise DesktopToolError(
            f"أُرسل طلب الإغلاق إلى «{window_title}»، لكنها ما زالت مفتوحة."
        )

    @staticmethod
    def _set_system_volume(level: object) -> str:
        if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 100:
            raise DesktopToolError("مستوى الصوت يجب أن يكون بين 0 و100.")
        try:
            result = subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except FileNotFoundError as error:
            raise DesktopToolError("أداة التحكم بالصوت غير متاحة.") from error
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError("انتهت مهلة ضبط مستوى الصوت.") from error
        if result.returncode:
            raise DesktopToolError(
                result.stderr.strip() or "تعذر ضبط مستوى الصوت."
            )
        return f"تم ضبط مستوى الصوت على {level}%."

    def _open_bluetooth_settings(self) -> str:
        return self._open_system_settings("bluetooth")

    def _open_system_settings(self, page: object) -> str:
        if not isinstance(page, str) or page not in self.SYSTEM_SETTINGS_PAGES:
            raise DesktopToolError("صفحة إعدادات النظام غير مدعومة.")
        control_center = shutil.which("gnome-control-center")
        if control_center is None:
            raise DesktopToolError(
                "تعذر العثور على مركز إعدادات GNOME."
            )
        try:
            result = self._launcher(
                control_center, self.SYSTEM_SETTINGS_PAGES[page]
            )
        except OSError as error:
            raise DesktopToolError(
                "تعذر فتح صفحة إعدادات النظام."
            ) from error
        started = result[0] if isinstance(result, tuple) else bool(result)
        if not started:
            raise DesktopToolError("تعذر فتح صفحة إعدادات النظام.")
        return f"تم فتح صفحة {page} في إعدادات النظام."

    @staticmethod
    def _run_pactl(*arguments: str) -> str:
        try:
            result = subprocess.run(
                ["pactl", *arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except FileNotFoundError as error:
            raise DesktopToolError(
                "أداة PipeWire/PulseAudio (pactl) غير متاحة."
            ) from error
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError(
                "انتهت مهلة فحص إعدادات الصوت."
            ) from error
        output = (result.stdout or result.stderr).strip()
        if result.returncode:
            raise DesktopToolError(
                output or "تعذر قراءة إعدادات الصوت."
            )
        return output

    def _repair_microphone(self) -> str:
        sources = self._run_pactl("list", "short", "sources")
        source_names = [
            line.split()[1]
            for line in sources.splitlines()
            if len(line.split()) > 1
            and ".monitor" not in line.split()[1]
        ]
        if not source_names:
            raise DesktopToolError(
                "لم يتم العثور على مدخل ميكروفون فعلي."
            )

        default_source = self._run_pactl("get-default-source").strip()
        changes = []
        if default_source not in source_names:
            default_source = next(
                (
                    name
                    for name in source_names
                    if name.startswith(("alsa_input.", "bluez_input."))
                ),
                source_names[0],
            )
            self._run_pactl("set-default-source", default_source)
            changes.append("اخترت مدخل الميكروفون المتاح")

        mute_status = self._run_pactl(
            "get-source-mute", default_source
        ).casefold()
        if "yes" in mute_status:
            self._run_pactl("set-source-mute", default_source, "0")
            changes.append("ألغيت كتم الميكروفون")
        elif "no" not in mute_status:
            raise DesktopToolError(
                "لم أتمكن من التحقق من حالة كتم الميكروفون."
            )

        volume_status = self._run_pactl(
            "get-source-volume", default_source
        )
        levels = [
            float(value)
            for value in re.findall(r"(\d+(?:\.\d+)?)%", volume_status)
        ]
        if not levels:
            raise DesktopToolError(
                "تعذر قراءة مستوى إدخال الميكروفون."
            )
        if max(levels) < 1:
            self._run_pactl(
                "set-source-volume", default_source, "75%"
            )
            changes.append("رفعت مستوى الإدخال الصامت إلى 75٪")

        verified_default = self._run_pactl("get-default-source").strip()
        verified_mute = self._run_pactl(
            "get-source-mute", verified_default
        ).casefold()
        verified_volume = self._run_pactl(
            "get-source-volume", verified_default
        )
        verified_levels = [
            float(value)
            for value in re.findall(r"(\d+(?:\.\d+)?)%", verified_volume)
        ]
        if verified_default != default_source or "no" not in verified_mute:
            raise DesktopToolError(
                "تغيّرت الإعدادات لكن تعذر التحقق من المدخل النشط."
            )
        if not verified_levels or max(verified_levels) < 1:
            raise DesktopToolError(
                "تعذر التحقق من مستوى إدخال الميكروفون بعد الإصلاح."
            )
        detail = (
            "، ".join(changes)
            if changes
            else "الإدخال الافتراضي غير مكتوم ومستواه ليس صفرًا"
        )
        return (
            f"{detail}. تحقق النظام من أن المدخل النشط هو "
            f"{default_source}. لم أختبر تسجيلًا صوتيًا، وقد تظل أذونات "
            "الخصوصية أو عطل الميكروفون بحاجة إلى تدخل يدوي."
        )

    @staticmethod
    def _set_bluetooth_power(enabled: object) -> str:
        if not isinstance(enabled, bool):
            raise DesktopToolError(
                "حالة Bluetooth المطلوبة يجب أن تكون تشغيلًا أو إيقافًا."
            )
        state = "on" if enabled else "off"
        try:
            result = subprocess.run(
                ["bluetoothctl", "power", state],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError as error:
            raise DesktopToolError(
                "أداة bluetoothctl غير متاحة."
            ) from error
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError(
                "انتهت مهلة تغيير حالة Bluetooth."
            ) from error
        output = (result.stdout or result.stderr).strip()
        if result.returncode:
            raise DesktopToolError(
                output or "تعذر تغيير حالة Bluetooth."
            )
        try:
            status = subprocess.run(
                ["bluetoothctl", "show"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except FileNotFoundError as error:
            raise DesktopToolError(
                "أداة bluetoothctl غير متاحة."
            ) from error
        except subprocess.TimeoutExpired as error:
            raise DesktopToolError(
                "انتهت مهلة التحقق من حالة Bluetooth."
            ) from error
        expected = f"Powered: {'yes' if enabled else 'no'}"
        if status.returncode or expected not in status.stdout:
            raise DesktopToolError(
                "أُرسل طلب Bluetooth لكن تعذر التحقق من الحالة المطلوبة."
            )
        return (
            "تم تشغيل Bluetooth والتحقق من حالته."
            if enabled
            else "تم إيقاف Bluetooth والتحقق من حالته."
        )

    @staticmethod
    def _coordinate(value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise DesktopToolError("إحداثيات النقر يجب أن تكون أرقامًا صحيحة.")
        return value

    @staticmethod
    def _virtual_geometry():
        screens = QGuiApplication.screens()
        if not screens:
            raise DesktopToolError("لا توجد شاشة متاحة للتحكم.")
        bounds = screens[0].geometry()
        for screen in screens[1:]:
            bounds = bounds.united(screen.geometry())
        return bounds

    def _move_coordinates(self, args: dict[str, object]) -> tuple[int, int]:
        x = self._coordinate(args.get("x"))
        y = self._coordinate(args.get("y"))
        bounds = self._virtual_geometry()
        if not bounds.contains(x, y):
            raise DesktopToolError("الإحداثيات خارج حدود الشاشات.")
        return x, y

    def execute(self, name: str, args: dict[str, object]) -> dict[str, object]:
        if name == "open_app":
            return {"text": self._open_application(args.get("app_name"))}
        if name == "open_url":
            return {"text": self._open_web_url(args.get("url"))}
        if name == "run_shell_command":
            return {
                "text": self._run_read_only_command(args.get("command"))
            }
        if name == "run_terminal_command":
            return {
                "text": self._run_terminal_command(args.get("command"))
            }
        if name == "close_ember_terminal":
            return {"text": self._close_ember_terminal()}
        if name == "list_windows":
            return {"text": self._list_windows()}
        if name == "close_window":
            return {"text": self._close_window(args.get("title"))}
        if name == "open_system_settings":
            return {
                "text": self._open_system_settings(args.get("page"))
            }
        if name == "repair_microphone":
            return {"text": self._repair_microphone()}
        if name == "set_bluetooth_power":
            return {
                "text": self._set_bluetooth_power(args.get("enabled"))
            }
        if name == "set_volume":
            return {"text": self._set_system_volume(args.get("level"))}
        if name == "open_bluetooth_settings":
            return {"text": self._open_bluetooth_settings()}
        if name == "close_active_window":
            self._remote_input.press_keys(0xFFE9, 0xFFC1)
            return {
                "text": (
                    "أُرسل اختصار الإغلاق للنافذة النشطة، لكن تعذر التحقق "
                    "من إغلاقها."
                )
            }
        if name == "take_screenshot_and_describe":
            return self._capture_screenshot()
        if name == "click":
            x, y = self._move_coordinates(args)
            self._remote_input.click(x, y)
            return {"text": f"تم النقر عند ({x}, {y})."}
        if name == "type_text":
            text = args.get("text")
            if (
                not isinstance(text, str)
                or not text
                or len(text) > 400
                or any(ord(char) < 32 and char not in "\n\t\r" for char in text)
            ):
                raise DesktopToolError("النص فارغ أو أطول من الحد المسموح.")
            self._remote_input.type_text(text)
            return {"text": "تمت كتابة النص."}
        if name == "scroll":
            x, y = self._move_coordinates(args)
            direction = args.get("direction")
            amount = args.get("amount")
            if direction not in {"up", "down"}:
                raise DesktopToolError("اتجاه التمرير يجب أن يكون up أو down.")
            if isinstance(amount, bool) or not isinstance(amount, int) or not 1 <= amount <= 10:
                raise DesktopToolError("كمية التمرير يجب أن تكون بين 1 و10.")
            self._remote_input.scroll(x, y, direction, amount)
            return {"text": f"تم التمرير {direction} بمقدار {amount}."}
        raise DesktopToolError(f"الأداة {name} غير متاحة.")

    def _capture_screenshot(
        self,
        cancel_event: Event | None = None,
        screen_geometry: tuple[int, int, int, int] | None = None,
    ) -> dict[str, object]:
        interface = QDBusInterface(
            PortalRemoteInput.SERVICE,
            PortalRemoteInput.PATH,
            "org.freedesktop.portal.Screenshot",
            QDBusConnection.sessionBus(),
        )
        token = uuid.uuid4().hex
        values = PortalRemoteInput()._request(
            interface,
            "Screenshot",
            ("", {"handle_token": f"ember_screenshot_{token}", "interactive": False}),
            cancel_event=cancel_event,
        )
        uri = values.get("uri")
        if not isinstance(uri, str):
            raise DesktopToolError("لم تُرجع خدمة الشاشة صورة.")
        path = QUrl(uri).toLocalFile()
        try:
            image_data = Path(path).read_bytes()
        except OSError as error:
            raise DesktopToolError("تعذر قراءة لقطة الشاشة.") from error
        finally:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError as error:
                _LOGGER.warning("Could not remove temporary screenshot %s: %s", path, error)
        image = QImage.fromData(image_data)
        if image.isNull():
            raise DesktopToolError("لقطة الشاشة غير صالحة.")
        if screen_geometry is None:
            screen = QGuiApplication.primaryScreen()
            geometry = screen.geometry() if screen is not None else image.rect()
            screen_x, screen_y = geometry.x(), geometry.y()
        else:
            screen_x, screen_y, _width, _height = screen_geometry
        return {
            "text": (
                f"تم التقاط الشاشة بدقة {image.width()}×{image.height()}. "
                f"إحداثياتها على سطح المكتب تبدأ من ({screen_x}, {screen_y}) "
                "وتُرسل هذه الصورة إلى Gemini للإجابة عن طلبك."
            ),
            "image": image_data,
        }
