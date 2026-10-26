from pathlib import Path

from PySide6.QtCore import QProcess
import pytest

from ember.desktop_tools import (
    DesktopToolError,
    DesktopToolExecutor,
    PortalRemoteInput,
    ReadOnlyCommandWorker,
)


class FakeRemoteInput:
    def __init__(self) -> None:
        self.calls = []

    def click(self, x: int, y: int) -> None:
        self.calls.append(("click", x, y))

    def type_text(self, text: str) -> None:
        self.calls.append(("type_text", text))

    def press_keys(self, *keysyms: int) -> None:
        self.calls.append(("press_keys", *keysyms))

    def scroll(self, x: int, y: int, direction: str, amount: int) -> None:
        self.calls.append(("scroll", x, y, direction, amount))


def test_open_app_matches_chrome_alias_without_shell_execution(
    tmp_path: Path,
) -> None:
    desktop_file = tmp_path / "google-chrome.desktop"
    desktop_file.write_text(
        "[Desktop Entry]\nType=Application\nName=Google Chrome\n",
        encoding="utf-8",
    )
    launched = []
    executor = DesktopToolExecutor(
        application_dirs=(tmp_path,),
        launcher=lambda program, args: launched.append((program, args))
        or (True, 0),
        remote_input=FakeRemoteInput(),
    )

    result = executor.execute("open_app", {"app_name": "Chrome"})

    assert result == {"text": "تم فتح Chrome."}
    assert launched == [("gtk-launch", ["google-chrome"])]


def test_open_terminal_matches_gnome_console_name(tmp_path: Path) -> None:
    desktop_file = tmp_path / "org.gnome.Console.desktop"
    desktop_file.write_text(
        "[Desktop Entry]\nType=Application\nName=GNOME Console\n",
        encoding="utf-8",
    )
    launched = []
    executor = DesktopToolExecutor(
        application_dirs=(tmp_path,),
        launcher=lambda program, args: launched.append((program, args))
        or (True, 0),
        remote_input=FakeRemoteInput(),
    )

    executor.execute("open_app", {"app_name": "Terminal"})

    assert launched == [("gtk-launch", ["org.gnome.Console"])]


def test_open_url_restricts_requests_to_http_and_https() -> None:
    opened = []
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        open_url=lambda url: opened.append(url.toString()) or True,
        remote_input=FakeRemoteInput(),
    )

    result = executor.execute("open_url", {"url": "https://example.com/path"})
    assert result == {"text": "تم فتح الرابط."}
    assert opened == ["https://example.com/path"]

    with pytest.raises(DesktopToolError, match="http أو https"):
        executor.execute("open_url", {"url": "file:///etc/passwd"})


def test_desktop_input_validates_text_and_coordinates() -> None:
    remote_input = FakeRemoteInput()
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=remote_input,
    )

    with pytest.raises(DesktopToolError, match="النص فارغ"):
        executor.execute("type_text", {"text": ""})
    with pytest.raises(DesktopToolError, match="أرقامًا صحيحة"):
        executor.execute("click", {"x": True, "y": 20})


def test_terminal_commands_are_a_fixed_read_only_allowlist(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "ember.desktop_tools.subprocess.run",
        lambda args, **kwargs: calls.append((args, kwargs))
        or type("Result", (), {"stdout": "ok", "stderr": "", "returncode": 0})(),
    )
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    assert executor.execute("run_shell_command", {"command": "git status"}) == {
        "text": "ok"
    }
    assert calls[0][0] == ["git", "status", "--short"]
    assert calls[0][1]["timeout"] == 5
    assert calls[0][1]["capture_output"]
    with pytest.raises(DesktopToolError, match="قائمة أوامر القراءة فقط"):
        executor.execute("run_shell_command", {"command": "ls /"})
    with pytest.raises(DesktopToolError):
        executor.execute("run_shell_command", {"command": "git status; id"})


def test_explicit_terminal_command_opens_visible_terminal() -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.program = ""
            self.arguments = []
            self.current_state = QProcess.ProcessState.NotRunning

        def setProgram(self, program):
            self.program = program

        def setArguments(self, arguments):
            self.arguments = arguments

        def start(self):
            self.current_state = QProcess.ProcessState.Running

        def waitForStarted(self, _timeout):
            return True

        def state(self):
            return self.current_state

        def terminate(self):
            self.current_state = QProcess.ProcessState.NotRunning

        def waitForFinished(self, _timeout):
            return True

        def deleteLater(self):
            pass

    process = FakeProcess()
    paths = {
        "local-cli": "/usr/local/bin/local-cli",
        "ptyxis": "/usr/bin/ptyxis",
    }
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
        terminal_lookup=paths.get,
        terminal_process_factory=lambda: process,
    )

    result = executor.execute(
        "run_terminal_command", {"command": "local-cli --help"}
    )

    assert result == {"text": "فُتحت نافذة Terminal وشُغّل الأمر الذي طلبته."}
    assert process.program == "/usr/bin/ptyxis"
    assert process.arguments[:4] == [
        "--standalone",
        "--new-window",
        "--title=Ember CLI",
        "--",
    ]
    assert process.arguments[-3:] == ["ember-terminal", "local-cli", "--help"]

    assert executor.execute("close_ember_terminal", {}) == {
        "text": "أُغلقت نافذة Terminal التي فتحها Ember."
    }
    assert process.state() == QProcess.ProcessState.NotRunning


def test_explicit_terminal_command_rejects_missing_and_system_modifying_commands() -> None:
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
        terminal_lookup=lambda name: (
            "/usr/bin/" + name
            if name in {"ptyxis", "local-cli"}
            else None
        ),
    )

    with pytest.raises(DesktopToolError, match="غير مثبت"):
        executor.execute("run_terminal_command", {"command": "missing-cli"})
    with pytest.raises(DesktopToolError, match="يغيّر النظام"):
        executor.execute("run_terminal_command", {"command": "sudo apt install package"})
    with pytest.raises(DesktopToolError, match="غير صالح"):
        executor.execute(
            "run_terminal_command", {"command": "local-cli\nrm -rf /"}
        )
    with pytest.raises(DesktopToolError, match="يغيّر النظام"):
        executor.execute(
            "run_terminal_command", {"command": "killall local-cli"}
        )
    with pytest.raises(DesktopToolError, match="لا توجد نافذة"):
        executor.execute("close_ember_terminal", {})


def test_volume_is_constrained_to_integer_percentages(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(
        "ember.desktop_tools.subprocess.run",
        lambda args, **kwargs: calls.append((args, kwargs))
        or type("Result", (), {"stdout": "", "stderr": "", "returncode": 0})(),
    )
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    executor.execute("set_volume", {"level": 65})

    assert calls[0][0] == [
        "pactl",
        "set-sink-volume",
        "@DEFAULT_SINK@",
        "65%",
    ]
    for level in (-1, 101, True, "65"):
        with pytest.raises(DesktopToolError):
            executor.execute("set_volume", {"level": level})


def test_open_settings_page_uses_only_supported_gnome_pages(monkeypatch) -> None:
    launches = []
    monkeypatch.setattr(
        "ember.desktop_tools.shutil.which",
        lambda name: "/usr/bin/gnome-control-center"
        if name == "gnome-control-center"
        else None,
    )
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda program, args: launches.append((program, args))
        or (True, 123),
        remote_input=FakeRemoteInput(),
    )

    assert executor.execute(
        "open_system_settings", {"page": "sound"}
    ) == {"text": "تم فتح صفحة sound في إعدادات النظام."}
    assert launches == [
        ("/usr/bin/gnome-control-center", ["sound"])
    ]
    with pytest.raises(DesktopToolError, match="غير مدعومة"):
        executor.execute("open_system_settings", {"page": "privacy"})


def test_microphone_repair_selects_unmutes_and_restores_silent_input(
    monkeypatch,
) -> None:
    state = {
        "default": "alsa_output.test.monitor",
        "muted": True,
        "volume": 0,
    }
    calls = []

    def fake_run(arguments, **_kwargs):
        calls.append(arguments)
        output = ""
        if arguments == ["pactl", "list", "short", "sources"]:
            output = (
                "0\talsa_output.test.monitor\tmodule\tSUSPENDED\n"
                "1\talsa_input.test\tmodule\tRUNNING\n"
            )
        elif arguments == ["pactl", "get-default-source"]:
            output = state["default"]
        elif arguments == ["pactl", "set-default-source", "alsa_input.test"]:
            state["default"] = "alsa_input.test"
        elif arguments == ["pactl", "get-source-mute", "alsa_input.test"]:
            output = f"Mute: {'yes' if state['muted'] else 'no'}"
        elif arguments == ["pactl", "set-source-mute", "alsa_input.test", "0"]:
            state["muted"] = False
        elif arguments == [
            "pactl",
            "get-source-volume",
            "alsa_input.test",
        ]:
            output = f"Volume: front-left: {state['volume']}%"
        elif arguments == [
            "pactl",
            "set-source-volume",
            "alsa_input.test",
            "75%",
        ]:
            state["volume"] = 75
        else:
            pytest.fail(f"Unexpected pactl command: {arguments}")
        return type(
            "Result",
            (),
            {"stdout": output, "stderr": "", "returncode": 0},
        )()

    monkeypatch.setattr("ember.desktop_tools.subprocess.run", fake_run)
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    result = executor.execute("repair_microphone", {})

    assert state == {
        "default": "alsa_input.test",
        "muted": False,
        "volume": 75,
    }
    assert "تحقق النظام" in result["text"]
    assert "لم أختبر تسجيلًا صوتيًا" in result["text"]
    assert len(calls) == 10


def test_microphone_repair_reports_missing_hardware_input(monkeypatch) -> None:
    monkeypatch.setattr(
        "ember.desktop_tools.subprocess.run",
        lambda *_args, **_kwargs: type(
            "Result",
            (),
            {
                "stdout": "0\talsa_output.test.monitor\tmodule\tRUNNING",
                "stderr": "",
                "returncode": 0,
            },
        )(),
    )
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    with pytest.raises(DesktopToolError, match="ميكروفون فعلي"):
        executor.execute("repair_microphone", {})


def test_bluetooth_power_change_is_verified(monkeypatch) -> None:
    commands = []
    monkeypatch.setattr(
        "ember.desktop_tools.subprocess.run",
        lambda arguments, **_kwargs: commands.append(arguments)
        or type(
            "Result",
            (),
            {
                "stdout": (
                    "Changing power on succeeded"
                    if arguments[-1] == "on"
                    else "Controller XX:XX:XX:XX:XX:XX\nPowered: yes"
                ),
                "stderr": "",
                "returncode": 0,
            },
        )(),
    )
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    assert executor.execute(
        "set_bluetooth_power", {"enabled": True}
    ) == {"text": "تم تشغيل Bluetooth والتحقق من حالته."}
    assert commands == [
        ["bluetoothctl", "power", "on"],
        ["bluetoothctl", "show"],
    ]
    with pytest.raises(DesktopToolError):
        executor.execute("set_bluetooth_power", {"enabled": 1})


def test_close_window_requires_a_unique_title_and_verifies_disappearance(
    monkeypatch,
) -> None:
    windows = [
        ("0x001", "Browser"),
        ("0x002", "Ember CLI Terminal"),
    ]
    commands = []
    monkeypatch.setattr(
        "ember.desktop_tools.shutil.which",
        lambda name: "/usr/bin/wmctrl" if name == "wmctrl" else None,
    )

    def fake_run(arguments, **_kwargs):
        commands.append(arguments)
        if arguments[-2:] == ["-l", "-p"]:
            output = "\n".join(
                f"{window_id} 0 42 host {title}"
                for window_id, title in windows
            )
        elif arguments[-2:] == ["-ic", "0x002"]:
            windows.remove(("0x002", "Ember CLI Terminal"))
            output = ""
        else:
            pytest.fail(f"Unexpected wmctrl command: {arguments}")
        return type(
            "Result",
            (),
            {"stdout": output, "stderr": "", "returncode": 0},
        )()

    monkeypatch.setattr("ember.desktop_tools.subprocess.run", fake_run)
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    result = executor.execute("close_window", {"title": "Terminal"})

    assert result == {
        "text": "أُغلقت نافذة «Ember CLI Terminal» وتحققت من اختفائها."
    }
    assert commands == [
        ["/usr/bin/wmctrl", "-l", "-p"],
        ["/usr/bin/wmctrl", "-ic", "0x002"],
        ["/usr/bin/wmctrl", "-l", "-p"],
    ]


def test_close_window_refuses_ambiguous_title_without_sending_close(
    monkeypatch,
) -> None:
    commands = []
    monkeypatch.setattr(
        "ember.desktop_tools.shutil.which",
        lambda name: "/usr/bin/wmctrl" if name == "wmctrl" else None,
    )
    monkeypatch.setattr(
        "ember.desktop_tools.subprocess.run",
        lambda arguments, **_kwargs: commands.append(arguments)
        or type(
            "Result",
            (),
            {
                "stdout": (
                    "0x001 0 42 host Terminal\n"
                    "0x002 0 43 host Terminal"
                ),
                "stderr": "",
                "returncode": 0,
            },
        )(),
    )
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=FakeRemoteInput(),
    )

    with pytest.raises(DesktopToolError, match="أكثر من نافذة"):
        executor.execute("close_window", {"title": "Terminal"})

    assert len(commands) == 1


def test_active_window_close_is_explicitly_reported_as_unverified() -> None:
    remote_input = FakeRemoteInput()
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=remote_input,
    )

    result = executor.execute("close_active_window", {})

    assert "تعذر التحقق" in result["text"]
    assert remote_input.calls == [("press_keys", 0xFFE9, 0xFFC1)]


def test_read_only_command_worker_returns_output_without_blocking_caller() -> None:
    worker = ReadOnlyCommandWorker("request-1", "pwd")
    results = []
    worker.result_ready.connect(
        lambda request_id, result: results.append((request_id, result))
    )

    worker.run()

    assert results
    assert results[0][0] == "request-1"
    assert "text" in results[0][1]


def test_address_bar_shortcut_and_whitespace_are_sent_to_remote_input() -> None:
    remote_input = FakeRemoteInput()
    executor = DesktopToolExecutor(
        application_dirs=(),
        launcher=lambda *_args: False,
        remote_input=remote_input,
    )

    executor.focus_address_bar()
    executor.execute("type_text", {"text": " "})
    executor.execute("type_text", {"text": "\n"})

    assert remote_input.calls == [
        ("press_keys", 0xFFE3, ord("l")),
        ("type_text", " "),
        ("type_text", "\n"),
    ]


def test_portal_uses_linux_left_button_and_vertical_scroll_codes(
    qapp, monkeypatch
) -> None:
    remote_input = PortalRemoteInput()
    calls = []
    monkeypatch.setattr(
        remote_input,
        "_notify",
        lambda method, *args: calls.append((method, *args)),
    )

    remote_input.click(100, 120)
    remote_input.scroll(100, 120, "down", 3)

    assert [call for call in calls if call[0] == "NotifyPointerButton"] == [
        ("NotifyPointerButton", 0x110, 1),
        ("NotifyPointerButton", 0x110, 0),
    ]
    assert (
        "NotifyPointerAxisDiscrete",
        0,
        3,
    ) in calls


def test_portal_releases_shortcut_keys_in_reverse_order(qapp, monkeypatch) -> None:
    remote_input = PortalRemoteInput()
    calls = []
    monkeypatch.setattr(
        remote_input,
        "_notify",
        lambda method, *args: calls.append((method, *args)),
    )
    monkeypatch.setattr(remote_input, "_ensure_session", lambda: "session")

    remote_input.press_keys(0xFFE3, ord("l"))

    assert calls == [
        ("NotifyKeyboardKeysym", 0xFFE3, 1),
        ("NotifyKeyboardKeysym", ord("l"), 1),
        ("NotifyKeyboardKeysym", ord("l"), 0),
        ("NotifyKeyboardKeysym", 0xFFE3, 0),
    ]
