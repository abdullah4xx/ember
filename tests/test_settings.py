from pathlib import Path
from types import SimpleNamespace
import sys

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit
import pytest

from ember.settings import (
    ApiKeyStore,
    AppSettings,
    SecretStorageError,
    SettingsStore,
    TOOL_NAMES,
)
from ember.memory import LocalMemoryStore
from ember.settings_window import (
    PAGES,
    ConnectionWorker,
    ModelListWorker,
    SettingsWindow,
)


class MemoryKeyStore:
    def __init__(self) -> None:
        self.value: str | None = None

    def has_key(self) -> bool:
        return self.value is not None

    def get_key(self) -> str | None:
        return self.value

    def set_key(self, value: str) -> None:
        self.value = value

    def delete_key(self) -> None:
        self.value = None


def make_store(path: Path) -> SettingsStore:
    return SettingsStore(QSettings(str(path), QSettings.Format.IniFormat))


def test_settings_round_trip_and_safe_tool_defaults(tmp_path: Path) -> None:
    store = make_store(tmp_path / "ember.ini")
    settings = AppSettings(
        model="gemini-3.8-live",
        response_language="ar",
        same_language=False,
        concise_replies=False,
        display_scale=0.7,
        allowed_folders=("/home/test/Documents",),
        wake_word_enabled=False,
    )
    settings.tool_tiers["run_shell_command"] = "ask"

    store.save(settings)
    loaded = store.load()

    assert loaded.model == "gemini-3.8-live"
    assert loaded.response_language == "ar"
    assert not loaded.same_language
    assert not loaded.concise_replies
    assert loaded.display_scale == 0.7
    assert loaded.allowed_folders == ("/home/test/Documents",)
    assert loaded.tool_tiers["run_shell_command"] == "ask"
    assert set(loaded.tool_tiers) == {name for name, _label in TOOL_NAMES}
    assert loaded.tool_tiers["type_text"] == "auto"
    assert loaded.tool_tiers["set_volume"] == "auto"
    assert loaded.tool_tiers["repair_microphone"] == "auto"
    assert loaded.tool_tiers["set_bluetooth_power"] == "auto"
    assert loaded.tool_tiers["list_windows"] == "auto"
    assert loaded.tool_tiers["close_window"] == "auto"
    assert not loaded.wake_word_enabled


def test_settings_reset_restores_defaults(tmp_path: Path) -> None:
    store = make_store(tmp_path / "ember.ini")
    store.save(AppSettings(response_language="en", display_scale=0.9))

    store.reset()

    assert store.load() == AppSettings()
    assert AppSettings().tool_tiers["run_shell_command"] == "auto"


def test_legacy_confirmation_prompts_migrate_to_automatic_once(
    tmp_path: Path,
) -> None:
    store = make_store(tmp_path / "ember.ini")
    store.settings.setValue("tools/open_bluetooth_settings", "ask")
    store.settings.setValue("tools/close_active_window", "ask")

    migrated = store.load()

    assert migrated.tool_tiers["open_bluetooth_settings"] == "auto"
    assert migrated.tool_tiers["close_active_window"] == "ask"

    migrated.tool_tiers["open_bluetooth_settings"] = "ask"
    store.save(migrated)

    assert store.load().tool_tiers["open_bluetooth_settings"] == "ask"


def test_previous_permission_migration_enables_requested_controls(
    tmp_path: Path,
) -> None:
    store = make_store(tmp_path / "ember.ini")
    store.settings.setValue("tool_permission_migration_version", 1)
    store.settings.setValue("tools/open_app", "ask")
    store.settings.setValue("tools/type_text", "ask")
    store.settings.setValue("tools/click", "ask")
    store.settings.setValue("tools/run_shell_command", "ask")

    settings = store.load()

    assert settings.tool_tiers["open_app"] == "auto"
    assert settings.tool_tiers["type_text"] == "auto"
    assert settings.tool_tiers["click"] == "auto"
    assert settings.tool_tiers["run_shell_command"] == "auto"
    assert settings.tool_tiers["open_system_settings"] == "auto"
    assert settings.tool_tiers["repair_microphone"] == "auto"
    assert settings.tool_tiers["list_windows"] == "auto"


def test_settings_window_is_arabic_and_has_all_sections(qapp, tmp_path: Path) -> None:
    memory_store = LocalMemoryStore(tmp_path / "memory.sqlite3")
    memory_store.add("أحب الردود المختصرة.")
    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=MemoryKeyStore(),
        memory_store=memory_store,
        autostart_writer=lambda _enabled: None,
    )
    window.show()
    qapp.processEvents()

    assert window.layoutDirection().name == "RightToLeft"
    assert window.navigation.count() == 6
    assert window._font_family == "AlMotLaQ-V2.5"
    assert window._font_bold_family == "AlMotLaQ-V2.5 Bold"
    assert window.model_combo.currentData() == "gemini-3.8-flash"
    assert window.models_refresh_button.text() == "قراءة النماذج"
    assert window.api_key_edit.echoMode().name == "Password"
    assert window.emergency_hotkey.keySequence() == QKeySequence("Ctrl+Alt+S")
    assert window.permission_combos["run_shell_command"].currentData() == "auto"
    assert window.permission_combos["repair_microphone"].currentData() == "auto"
    assert window.permission_combos["set_bluetooth_power"].currentData() == "auto"
    assert window.permission_combos["close_window"].currentData() == "auto"
    window._open_settings_page("memory")
    assert window.memory_list.count() == 1
    assert window.memory_list.item(0).text() == "أحب الردود المختصرة."
    assert window.wake_word_enabled.isChecked()
    assert not window.api_quota_warning.isVisible()
    window.set_api_quota_warning(True)
    assert not window.api_quota_warning.isHidden()
    window.set_api_quota_warning(False)
    assert window.api_quota_warning.isHidden()
    assert not hasattr(window, "actions_limit")
    assert not hasattr(window, "steps_limit")
    display_scale, is_scale = window._controls["display_scale"]
    assert (display_scale.minimum(), display_scale.maximum()) == (35, 150)
    assert is_scale

    window.close()


def test_home_dashboard_opens_and_returns_from_settings(qapp, tmp_path: Path) -> None:
    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=MemoryKeyStore(),
        autostart_writer=lambda _enabled: None,
    )
    window.show()
    qapp.processEvents()

    assert window.screen_stack.currentIndex() == 0
    assert len(window.home_stage.links) == 6
    QTest.mouseClick(window.home_stage.links["voice"], Qt.MouseButton.LeftButton)
    qapp.processEvents()

    assert window.screen_stack.currentIndex() == 1
    assert window.navigation.currentRow() == 1
    assert window.pages.currentIndex() == 1
    window._show_home()
    qapp.processEvents()
    assert window.screen_stack.currentIndex() == 0

    window.close()


def test_home_character_tracks_pointer(qapp, tmp_path: Path) -> None:
    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=MemoryKeyStore(),
        autostart_writer=lambda _enabled: None,
    )
    window.show()
    qapp.processEvents()

    window.home_stage._update_gaze(QPoint(20, window.home_stage.height() // 2))
    QTest.qWait(120)

    assert window.home_stage.portrait.animation.state.value == "listening"
    assert window.home_stage.portrait.animation.gaze_x.value < 0
    window.close()


def test_character_hotspots_open_their_matching_settings_pages(
    qapp, tmp_path: Path
) -> None:
    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=MemoryKeyStore(),
        autostart_writer=lambda _enabled: None,
    )
    window.show()
    qapp.processEvents()
    stage = window.home_stage

    page_indexes = {
        key: index for index, (key, _title, _subtitle) in enumerate(PAGES)
    }
    for page in stage.CHARACTER_HOTSPOTS:
        hotspot = stage.hotspot_buttons[page]
        assert hotspot.isVisible()
        assert hotspot.accessibleName().startswith("فتح إعدادات ")
        QTest.mouseClick(hotspot, Qt.MouseButton.LeftButton)
        qapp.processEvents()
        assert window.screen_stack.currentIndex() == 1
        assert window.navigation.currentRow() == page_indexes[page]
        window._show_home()
        qapp.processEvents()

    keyboard_hotspot = stage.hotspot_buttons["gemini"]
    keyboard_hotspot.setFocus()
    QTest.keyClick(keyboard_hotspot, Qt.Key.Key_Space)
    qapp.processEvents()
    assert window.navigation.currentRow() == page_indexes["gemini"]

    window.close()


def test_settings_navigation_animation_can_be_reused_and_interrupted(
    qapp, tmp_path: Path
) -> None:
    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=MemoryKeyStore(),
        autostart_writer=lambda _enabled: None,
    )
    window.show()
    window._open_settings_page("gemini")
    window.navigation.setCurrentRow(1)
    window.navigation.setCurrentRow(2)
    QTest.qWait(220)
    window.navigation.setCurrentRow(3)
    QTest.qWait(500)

    assert window.pages.currentIndex() == 3
    assert abs(window._page_effects[3].opacity() - 1.0) < 0.001

    window.close()


def test_saving_settings_keeps_api_key_out_of_ini_file(
    qapp, tmp_path: Path
) -> None:
    ini_path = tmp_path / "ember.ini"
    store = make_store(ini_path)
    key_store = MemoryKeyStore()
    window = SettingsWindow(
        store=store,
        key_store=key_store,
        autostart_writer=lambda _enabled: None,
    )
    secret = "private-test-gemini-key"
    window.api_key_edit.setText(secret)
    window.language_combo.setCurrentIndex(window.language_combo.findData("ar"))
    window._save()

    assert key_store.value == secret
    assert "private-test-gemini-key" not in ini_path.read_text(encoding="utf-8")
    assert store.load().response_language == "ar"
    assert window.api_key_edit.text() == secret
    window._save()
    assert key_store.value == secret
    window.close()


def test_saving_other_settings_does_not_remove_stored_api_key(
    qapp, tmp_path: Path
) -> None:
    key_store = MemoryKeyStore()
    key_store.set_key("existing-api-key")
    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=key_store,
        autostart_writer=lambda _enabled: None,
    )

    window.sleep_delay.setValue(7)
    window._save()

    assert key_store.value == "existing-api-key"
    assert "المفتاح محفوظ" in window.key_status.text()
    window.close()


def test_saved_api_key_is_loaded_masked_when_settings_reopen(
    qapp, tmp_path: Path
) -> None:
    key_store = MemoryKeyStore()
    key_store.set_key("saved-test-key")

    window = SettingsWindow(
        store=make_store(tmp_path / "ember.ini"),
        key_store=key_store,
        autostart_writer=lambda _enabled: None,
    )

    assert window.api_key_edit.text() == "saved-test-key"
    assert window.api_key_edit.echoMode() == QLineEdit.EchoMode.Password
    assert "المفتاح محفوظ" in window.key_status.text()
    window.close()


def test_api_key_store_confirms_the_keyring_write(monkeypatch) -> None:
    stored = {}
    fake_keyring = SimpleNamespace(
        set_password=lambda service, username, value: stored.__setitem__(
            (service, username), value
        ),
        get_password=lambda service, username: stored.get((service, username)),
    )
    monkeypatch.setitem(sys.modules, "keyring", fake_keyring)

    store = ApiKeyStore()
    store.set_key("private-test-key")

    assert store.get_key() == "private-test-key"


def test_api_key_store_reports_when_the_keyring_does_not_persist(monkeypatch) -> None:
    fake_keyring = SimpleNamespace(
        set_password=lambda *_args: None,
        get_password=lambda *_args: None,
    )
    monkeypatch.setitem(sys.modules, "keyring", fake_keyring)

    with pytest.raises(SecretStorageError, match="لم يؤكد مخزن النظام"):
        ApiKeyStore().set_key("private-test-key")


def test_connection_worker_reports_success_without_network() -> None:
    received: list[tuple[str, str]] = []
    worker = ConnectionWorker(
        "never-written-to-storage",
        "gemini-3.8-flash",
        lambda api_key, model: received.append((api_key, model)),
    )
    results: list[tuple[bool, str]] = []
    worker.result_ready.connect(lambda success, message: results.append((success, message)))

    worker.run()

    assert received == [("never-written-to-storage", "gemini-3.8-flash")]
    assert results == [
        (True, "الاتصال ناجح، والمفتاح يستطيع الوصول إلى Gemini.")
    ]


def test_model_list_worker_returns_all_content_generation_models() -> None:
    received = []
    worker = ModelListWorker(
        "private-test-key",
        lambda _key: [
            ("gemini-2.0-flash", "Gemini 2.0 Flash"),
            ("gemini-2.5-pro", "Gemini 2.5 Pro"),
        ],
    )
    worker.models_ready.connect(received.append)

    worker.run()

    assert received == [[
        ("gemini-2.0-flash", "Gemini 2.0 Flash"),
        ("gemini-2.5-pro", "Gemini 2.5 Pro"),
    ]]


def test_model_list_filters_non_generation_models_and_closes_client(monkeypatch) -> None:
    from types import SimpleNamespace

    class FakeModels:
        def list(self, *, config):
            assert config == {"page_size": 100}
            return [
                SimpleNamespace(
                    name="models/gemini-2.5-flash",
                    display_name="Gemini 2.5 Flash",
                    supported_actions=["generateContent"],
                ),
                SimpleNamespace(
                    name="models/text-embedding-004",
                    display_name="Text Embedding",
                    supported_actions=["embedContent"],
                ),
                SimpleNamespace(
                    name="models/gemini-2.5-pro",
                    display_name="Gemini 2.5 Pro",
                    supported_actions=["generateContent"],
                ),
            ]

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "private-test-key"
            self.models = FakeModels()
            self.closed = False

        def close(self):
            self.closed = True

    clients = []

    def make_client(**kwargs):
        client = FakeClient(**kwargs)
        clients.append(client)
        return client

    monkeypatch.setattr("ember.settings_window.genai.Client", make_client)

    assert ModelListWorker._list_google_models("private-test-key") == [
        ("gemini-2.5-flash", "Gemini 2.5 Flash"),
        ("gemini-2.5-pro", "Gemini 2.5 Pro"),
    ]
    assert clients[0].closed


def test_connection_probe_checks_selected_model_without_listing_every_model(
    monkeypatch,
) -> None:
    requested = []

    class FakeModels:
        def get(self, *, model):
            requested.append(model)
            return SimpleNamespace(supported_actions=["generateContent"])

    class FakeClient:
        def __init__(self, *, api_key):
            assert api_key == "private-test-key"
            self.models = FakeModels()

        def close(self):
            pass

    monkeypatch.setattr("ember.settings_window.genai.Client", FakeClient)

    ConnectionWorker._probe_google("private-test-key", "gemini-2.5-flash")

    assert requested == ["gemini-2.5-flash"]


def test_loaded_models_preserve_saved_selection_and_show_all(qapp, tmp_path: Path) -> None:
    settings = AppSettings(model="gemini-saved-model")
    store = make_store(tmp_path / "ember.ini")
    store.save(settings)
    window = SettingsWindow(
        store=store,
        key_store=MemoryKeyStore(),
        autostart_writer=lambda _enabled: None,
    )

    window._on_models_loaded(
        [
            ("gemini-2.5-flash", "Gemini 2.5 Flash"),
            ("gemini-2.5-pro", "Gemini 2.5 Pro"),
        ]
    )

    assert window.model_combo.count() == 3
    assert window.model_combo.itemData(0) == "gemini-2.5-flash"
    assert window.model_combo.currentData() == "gemini-saved-model"
    assert "غير متاح في القائمة" in window.model_combo.currentText()
    window.close()
