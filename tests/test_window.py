import os
from types import SimpleNamespace
import time

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, Qt, QThread, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

import ember.__main__ as ember_main
from ember.animation import AnimationState
from ember.character import GROUND_Y
import ember.window as window_module
from ember.window import CharacterWindow


def send_mouse_event(
    window: CharacterWindow,
    event_type: QMouseEvent.Type,
    local_x: float,
    local_y: float,
    global_x: float,
    global_y: float,
    button: Qt.MouseButton,
    buttons: Qt.MouseButton,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    event = QMouseEvent(
        event_type,
        QPointF(local_x, local_y),
        QPointF(global_x, global_y),
        button,
        buttons,
        modifiers,
    )
    QApplication.sendEvent(window, event)


def wait_until(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    return predicate()


def test_left_drag_moves_window_without_triggering_happy_click(qapp) -> None:
    window = CharacterWindow()
    window.settings.stand_on_windows = False
    window.move(500, 500)
    window.show()
    qapp.processEvents()
    start = window.pos()
    local_x, local_y = 100.0, 100.0

    send_mouse_event(
        window,
        QMouseEvent.Type.MouseButtonPress,
        local_x,
        local_y,
        start.x() + local_x,
        start.y() + local_y,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
    )
    QTest.qWait(340)
    send_mouse_event(
        window,
        QMouseEvent.Type.MouseMove,
        local_x + 20,
        local_y + 15,
        start.x() + local_x + 20,
        start.y() + local_y + 15,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
    )
    QTest.qWait(700)
    assert window.pos() == start + QPoint(20, 15)

    send_mouse_event(
        window,
        QMouseEvent.Type.MouseButtonRelease,
        local_x + 20,
        local_y + 15,
        start.x() + local_x + 20,
        start.y() + local_y + 15,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
    )
    assert window.animation.state is AnimationState.FALLING
    window.close()


def test_character_position_can_reach_each_workarea_edge(qapp) -> None:
    window = CharacterWindow()
    area = window._available_geometry()
    visible = window.mask().boundingRect()

    upper_left = window._clamp_position_to_workarea(QPoint(-10_000, -10_000), area)
    lower_right = window._clamp_position_to_workarea(QPoint(10_000, 10_000), area)

    assert upper_left.x() + visible.left() == area.left()
    assert upper_left.y() + visible.top() == area.top()
    assert lower_right.x() + visible.right() == area.right()
    assert lower_right.y() + visible.bottom() == area.bottom()
    window.close()


def test_character_stands_on_physical_bottom_edge(qapp, monkeypatch) -> None:
    window = CharacterWindow()
    window._set_display_scale(0.5)
    screen = SimpleNamespace(
        availableGeometry=lambda: QRect(0, 32, 1366, 718),
        geometry=lambda: QRect(0, 0, 1366, 768),
    )
    monkeypatch.setattr(window_module.QApplication, "primaryScreen", lambda: screen)

    window._place_on_workarea()

    assert window.y() + round(GROUND_Y * window.display_scale) == 768
    window.close()


def test_workarea_reaches_physical_bottom_but_keeps_top_panel_clear() -> None:
    screen = SimpleNamespace(
        availableGeometry=lambda: QRect(0, 32, 1366, 736),
        geometry=lambda: QRect(0, 0, 1366, 768),
    )

    area = CharacterWindow._workarea_to_screen_bottom(screen)

    assert area.top() == 32
    assert area.bottom() == 767


def test_throw_bounces_off_a_wall_then_clings_when_speed_drops(qapp, monkeypatch) -> None:
    window = CharacterWindow()
    area = QRect(0, 0, 800, 600)
    monkeypatch.setattr(window, "_available_geometry", lambda: area)
    left = window._clamp_position_to_workarea(QPoint(-10_000, 200), area).x()
    window.move(left + 5, 200)
    window.animation.set_state(AnimationState.FALLING)
    window._physics_active = True
    window._physics_velocity = QPointF(-1200, 0)
    window._physics_last_tick = time.monotonic() - 0.05

    window._advance_physics()

    assert window.x() == left
    assert window._physics_velocity.x() > 0
    assert window._physics_active

    window.move(left + 1, window.y())
    window._physics_velocity = QPointF(-100, 0)
    window._physics_last_tick = time.monotonic() - 0.05
    window._advance_physics()

    assert window._wall_cling_side == "left"
    assert not window._physics_active
    assert window.animation.state is AnimationState.CLINGING
    window.close()


def test_throw_stops_with_a_superhero_landing_at_the_workarea_floor(
    qapp, monkeypatch
) -> None:
    window = CharacterWindow()
    area = QRect(0, 0, 800, 600)
    monkeypatch.setattr(window, "_available_geometry", lambda: area)
    bottom = window._clamp_position_to_workarea(QPoint(200, 10_000), area).y()
    window.move(200, bottom - 5)
    window.animation.set_state(AnimationState.FALLING)
    window._physics_active = True
    window._physics_velocity = QPointF(0, 150)
    window._physics_last_tick = time.monotonic() - 0.05

    window._advance_physics()

    assert window.y() == bottom
    assert not window._physics_active
    assert window.animation.state is AnimationState.LANDING
    assert window.animation.pose().landing_amount == 1
    window.close()


def test_wayland_drag_uses_compositor_system_move(qapp, monkeypatch) -> None:
    class FakeWindowHandle:
        def __init__(self) -> None:
            self.started = False

        def startSystemMove(self) -> bool:
            self.started = True
            return True

    window = CharacterWindow()
    window.show()
    qapp.processEvents()
    start = window.pos()
    window._drag_origin = QPoint(start.x() + 100, start.y() + 100)
    window._window_origin = start
    window._drag_target_position = QPointF(start)
    window._drag_armed = True
    handle = FakeWindowHandle()
    monkeypatch.setattr(
        window_module.QGuiApplication, "platformName", lambda: "wayland"
    )
    monkeypatch.setattr(window, "windowHandle", lambda: handle)

    send_mouse_event(
        window,
        QMouseEvent.Type.MouseMove,
        120,
        115,
        start.x() + 120,
        start.y() + 115,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
    )

    assert handle.started
    assert window._native_drag
    assert window._drag_target_position == start
    window._drag_hold_timer.stop()
    window.close()


def test_left_click_without_drag_shows_happy_pose(qapp) -> None:
    window = CharacterWindow()
    window._set_display_scale(0.7)
    window.show()
    qapp.processEvents()
    local_x = local_y = 100.0
    global_x = window.x() + local_x
    global_y = window.y() + local_y

    send_mouse_event(
        window,
        QMouseEvent.Type.MouseButtonPress,
        local_x,
        local_y,
        global_x,
        global_y,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
    )
    send_mouse_event(
        window,
        QMouseEvent.Type.MouseButtonRelease,
        local_x,
        local_y,
        global_x,
        global_y,
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
    )

    assert window.animation.state is AnimationState.HAPPY
    window.close()


def test_control_right_click_opens_settings(qapp) -> None:
    window = CharacterWindow()
    window._set_display_scale(0.7)
    window.show()
    window._show_ask_bubble()
    qapp.processEvents()
    point = QPointF(100, 100)
    position = window.mapToGlobal(point.toPoint())
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        point,
        QPointF(position),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.ControlModifier,
    )
    qapp.sendEvent(window, event)
    qapp.processEvents()

    assert window.settings_window is not None
    assert window.settings_window.isVisible()
    assert window.settings_window.windowTitle() == "إعدادات Ember"
    assert not window.ask_bubble.isVisible()
    assert window.settings_window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint

    window.settings_window.close()
    window.close()


def test_settings_hides_visible_conversation_and_restores_it_on_close(qapp) -> None:
    window = CharacterWindow()
    window.show()
    window.conversation_window.show()
    qapp.processEvents()

    window.open_settings()
    qapp.processEvents()
    assert window.settings_window is not None
    assert window.settings_window.isVisible()
    assert not window.conversation_window.isVisible()

    window.settings_window.close()
    qapp.processEvents()
    assert window.conversation_window.isVisible()
    window.conversation_window.close()
    window.close()


def test_right_click_on_seated_character_does_not_open_ask_bubble(qapp) -> None:
    window = CharacterWindow()
    window._seated_for_chat = True
    window.animation.set_state(AnimationState.SITTING)
    window.show()
    qapp.processEvents()
    point = QPointF(100, 100)
    position = window.mapToGlobal(point.toPoint())

    send_mouse_event(
        window,
        QMouseEvent.Type.MouseButtonPress,
        point.x(),
        point.y(),
        position.x(),
        position.y(),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.RightButton,
    )
    send_mouse_event(
        window,
        QMouseEvent.Type.MouseButtonRelease,
        point.x(),
        point.y(),
        position.x(),
        position.y(),
        Qt.MouseButton.RightButton,
        Qt.MouseButton.NoButton,
    )

    assert not window.ask_bubble.isVisible()
    assert not window._right_button_active
    window.close()


def test_holding_seated_character_detaches_without_closing_chat(qapp) -> None:
    window = CharacterWindow()
    home = QPoint(420, 360)
    window._home_scale = 0.7
    window._chat_return_state = (home, 0.7, False)
    window._seated_for_chat = True
    window._set_display_scale(140 / 380)
    window.move(700, 260)
    window.conversation_window.show()
    window._drag_origin = QPoint(740, 300)
    window._window_origin = window.pos()

    window._arm_drag()

    assert window.pos() == QPoint(700, 260)
    assert abs(window.display_scale - 140 / 380) < 0.001
    assert window.conversation_window.isVisible()
    assert window._chat_return_state == (home, 0.7, False)
    assert window._chat_character_detached
    assert not window._seated_for_chat
    assert window._drag_armed
    assert window.animation.state is AnimationState.IDLE

    window.close()


def test_attached_character_follows_conversation_window(qapp) -> None:
    window = CharacterWindow()
    conversation = window.conversation_window
    conversation.show()
    qapp.processEvents()
    handle = conversation.windowHandle()
    assert handle is not None
    window.move(420, 230)
    window._attach_to_window(handle)
    offset = window._attachment_offset

    conversation.move(conversation.x() + 36, conversation.y() + 24)
    qapp.processEvents()

    assert window.pos() == handle.frameGeometry().topLeft() + offset
    window.close()
    conversation.close()


def test_drag_release_perches_character_on_window(qapp, monkeypatch) -> None:
    target = QWidget()
    target.setGeometry(300, 240, 500, 360)
    target.show()
    qapp.processEvents()
    handle = target.windowHandle()
    assert handle is not None
    window = CharacterWindow()
    window._set_display_scale(0.5)
    window.show()
    monkeypatch.setattr(
        window_module.QGuiApplication,
        "topLevelAt",
        staticmethod(lambda _position: handle),
    )

    assert window._dock_on_window_at(QPoint(500, 360))

    visible = window.mask().boundingRect()
    assert window.y() + visible.bottom() == handle.frameGeometry().top()
    assert window._attached_window is handle
    assert window.animation.state is AnimationState.LANDING
    for _ in range(10):
        window.animation.update(0.05)
    assert window.animation.state is AnimationState.PERCHING
    window.close()
    target.close()


def test_disabling_stand_on_windows_prevents_docking(qapp, monkeypatch) -> None:
    target = QWidget()
    target.setGeometry(300, 240, 500, 360)
    target.show()
    qapp.processEvents()
    handle = target.windowHandle()
    assert handle is not None
    window = CharacterWindow()
    window.settings.stand_on_windows = False
    monkeypatch.setattr(
        window_module.QGuiApplication,
        "topLevelAt",
        staticmethod(lambda _position: handle),
    )

    assert not window._dock_on_window_at(QPoint(500, 360))
    assert window._attached_window is None
    window.close()
    target.close()


def test_settings_resize_character_while_seated(qapp) -> None:
    window = CharacterWindow()
    window._set_display_scale(140 / 380)
    window._seated_for_chat = True
    window._chat_return_state = (QPoint(100, 200), 0.7, False)
    window.conversation_window.show()
    qapp.processEvents()
    handle = window.conversation_window.windowHandle()
    assert handle is not None
    window._attach_to_window(handle)

    window.settings.display_scale = 0.9
    window._apply_settings(window.settings)

    expected_scale = window._conversation_character_scale(0.9)
    assert window.display_scale == expected_scale
    assert window._seated_for_chat
    assert window._chat_return_state == (QPoint(100, 200), 0.9, False)
    window.close()
    window.conversation_window.close()


def test_closing_chat_keeps_detached_character_on_target_window(qapp) -> None:
    window = CharacterWindow()
    target = QWidget()
    target.show()
    window.conversation_window.show()
    qapp.processEvents()
    handle = target.windowHandle()
    assert handle is not None
    window.move(240, 180)
    window._attach_to_window(handle)
    window._chat_return_state = (QPoint(30, 40), 0.7, False)
    window._chat_character_detached = True
    original_position = window.pos()

    window._return_from_conversation()

    assert not window.conversation_window.isVisible()
    assert window._attached_window is handle
    assert window.pos() == original_position
    assert window._chat_return_state is None
    assert not window._transition_timer.isActive()
    window.close()
    target.close()
    window.conversation_window.close()


def test_hanging_character_is_clear_of_top_workarea_edge(qapp, monkeypatch) -> None:
    window = CharacterWindow()
    area = QRect(0, 32, 1366, 700)
    monkeypatch.setattr(window, "_available_geometry", lambda: area)
    window._set_display_scale(0.7)

    window._enter_sleep()

    feet_offset = round(
        (window_module.CANVAS_HEIGHT - GROUND_Y) * window.display_scale
    )
    assert window._transition_target.y() + feet_offset == area.top()
    window.close()


def test_hanging_keeps_character_shape_and_closes_eyes(qapp) -> None:
    window = CharacterWindow()
    window._is_hanging = True
    window.animation.set_state(AnimationState.SLEEPING)

    pose = window._display_pose(window.animation.pose())

    assert (pose.body_y, pose.body_stretch, pose.sleep_amount) == (0, 0, 0)
    assert pose.closed_eyes
    assert pose.eye_opening == 0

    window.animation.set_state(AnimationState.HANGING)
    for _ in range(24):
        window.animation.update(0.05)
    assert not window._display_pose(window.animation.pose()).closed_eyes
    window.close()


def test_sleep_entry_rotates_and_does_not_play_audio_automatically(
    qapp, monkeypatch
) -> None:
    window = CharacterWindow()
    area = QRect(0, 32, 1366, 700)
    monkeypatch.setattr(window, "_available_geometry", lambda: area)
    sounds: list[str] = []
    window._play_chime = sounds.append

    window._enter_sleep()
    assert not window._is_hanging
    assert window._orientation_angle == 0

    window._transition_started = time.monotonic() - window._transition_duration / 2
    window._advance_transition()
    assert 0 < window._orientation_angle < 180
    assert not window._is_hanging

    window._transition_started = time.monotonic() - window._transition_duration
    window._advance_transition()
    assert window._is_hanging
    assert window._orientation_angle == 180
    assert window.animation.state is AnimationState.SLEEPING
    assert sounds == []

    window._enter_sleep(play_sound=True)
    window._transition_started = time.monotonic() - window._transition_duration
    window._advance_transition()
    assert sounds == ["sleep"]
    window.close()


def test_animation_state_changes_do_not_play_sounds_without_an_action(qapp) -> None:
    window = CharacterWindow()
    sounds: list[str] = []
    window._play_chime = sounds.append

    window.animation.set_state(AnimationState.THINKING)
    window._tick()
    window.animation.set_state(AnimationState.SITTING)
    window._tick()

    assert sounds == []
    window.close()


def test_conversation_transition_returns_character_to_home(qapp) -> None:
    class NoKeyStore:
        def get_key(self) -> None:
            return None

    window = CharacterWindow()
    window.api_key_store = NoKeyStore()
    home = window.pos()
    home_scale = window.display_scale

    window._start_conversation("Hello, Ember", "en")
    QTest.qWait(1300)

    assert window.conversation_window.isVisible()
    assert window._seated_for_chat
    assert window.animation.state is AnimationState.SITTING
    assert (
        abs(
            window.display_scale
            - window._conversation_character_scale(home_scale)
        )
        < 0.01
    )
    assert (
        window.y() + round(214 * window.display_scale)
        <= window.conversation_window.y() + 4
    )

    window._return_from_conversation()
    QTest.qWait(950)

    assert not window.conversation_window.isVisible()
    assert window.pos() == home
    assert abs(window.display_scale - home_scale) < 0.001
    assert window.animation.state is AnimationState.IDLE

    window.conversation_window.close()
    window.ask_bubble.close()
    window.close()


def test_unrelated_desktop_activity_does_not_reset_ember_idle_timer(
    qapp, monkeypatch
) -> None:
    window = CharacterWindow()
    unrelated_widget = QWidget()
    monkeypatch.setattr(
        window_module,
        "QCursor",
        SimpleNamespace(pos=lambda: QPoint(0, 0)),
    )
    previous_activity = time.monotonic() - 30
    window._last_activity = previous_activity

    window.eventFilter(unrelated_widget, QEvent(QEvent.Type.MouseMove))
    assert window._last_activity == previous_activity

    window.eventFilter(window, QEvent(QEvent.Type.KeyPress))
    assert window._last_activity > previous_activity

    window.close()


def test_wake_listener_does_not_restart_after_window_shutdown(qapp, monkeypatch) -> None:
    window = CharacterWindow()
    starts = []
    monkeypatch.setattr(window._wake_listener, "start", lambda: starts.append(True))

    window.close()
    window.start_wake_word_listener()
    window._resume_wake_listener_if_idle()

    assert not starts


def test_gemini_reply_updates_chat_through_the_gui_thread(qapp, monkeypatch) -> None:
    class FakeReplyWorker(QThread):
        reply_ready = Signal(str, bool)
        request_failed = Signal(str)

        def __init__(self, *_args, **_kwargs):
            super().__init__()

        def run(self) -> None:
            self.reply_ready.emit("Queued response", False)

    monkeypatch.setattr(window_module, "GeminiReplyWorker", FakeReplyWorker)
    window = CharacterWindow()
    window.api_key_store = SimpleNamespace(get_key=lambda: "test-key")

    window._start_conversation("Hello", "en")

    assert wait_until(lambda: not window._conversation_busy)
    assert "9bc7a1" in window.conversation_window.connection_button.styleSheet()
    reply_bubble = window.conversation_window.thread_layout.itemAt(1).widget()
    assert isinstance(reply_bubble, QWidget)
    assert reply_bubble.findChild(QLabel, "messageText").text() == "Queued response"

    window.conversation_window.close()
    window.ask_bubble.close()
    window.close()


def test_gemini_error_marks_status_indicator_red(qapp, monkeypatch) -> None:
    class FakeReplyWorker(QThread):
        reply_ready = Signal(str, bool)
        request_failed = Signal(str)

        def __init__(self, *_args, **_kwargs):
            super().__init__()

        def run(self) -> None:
            self.request_failed.emit("Connection failed")

    monkeypatch.setattr(window_module, "GeminiReplyWorker", FakeReplyWorker)
    window = CharacterWindow()
    window.api_key_store = SimpleNamespace(get_key=lambda: "test-key")

    window._start_conversation("Hello", "en")

    assert wait_until(
        lambda: "e46e62"
        in window.conversation_window.connection_button.styleSheet()
    )
    assert (
        window.conversation_window.connection_button.toolTip()
        == "There is a problem with the Gemini connection"
    )
    window.conversation_window.close()
    window.ask_bubble.close()
    window.close()


def test_auto_desktop_tool_is_dispatched_and_result_returned(qapp) -> None:
    results = []
    calls = []
    window = CharacterWindow()
    window._gemini_worker = SimpleNamespace(
        resolve_tool_call=lambda request_id, result: results.append(
            (request_id, result)
        )
    )
    window._desktop_tool_executor = SimpleNamespace(
        execute=lambda name, args: calls.append((name, args))
        or {"text": "تم فتح Chrome."}
    )

    window._handle_desktop_tool(
        "request-1", "open_app", {"app_name": "Chrome"}
    )

    assert calls == [("open_app", {"app_name": "Chrome"})]
    assert results == [("request-1", {"text": "تم فتح Chrome."})]
    window.close()


def test_requested_desktop_controls_do_not_show_confirmation(qapp, monkeypatch) -> None:
    results = []
    calls = []
    window = CharacterWindow()
    window._gemini_worker = SimpleNamespace(
        resolve_tool_call=lambda request_id, result: results.append(
            (request_id, result)
        )
    )
    window._desktop_tool_executor = SimpleNamespace(
        execute=lambda name, args: calls.append((name, args)) or {"text": "ok"}
    )
    monkeypatch.setattr(
        window,
        "_confirm_desktop_tool",
        lambda *_args: pytest.fail("An internal confirmation dialog was shown"),
    )

    for request_id, name, args in (
        ("app", "open_app", {"app_name": "Settings"}),
        ("bluetooth", "open_bluetooth_settings", {}),
        ("system-page", "open_system_settings", {"page": "sound"}),
        ("bluetooth-power", "set_bluetooth_power", {"enabled": True}),
        ("microphone", "repair_microphone", {}),
        ("windows", "list_windows", {}),
        ("close-window", "close_window", {"title": "Terminal"}),
        ("typing", "type_text", {"text": "git status\n"}),
        ("terminal", "run_terminal_command", {"command": "local-cli"}),
        ("close-terminal", "close_ember_terminal", {}),
    ):
        window._handle_desktop_tool(request_id, name, args)

    deadline = time.monotonic() + 2
    while len(results) < 10 and time.monotonic() < deadline:
        QTest.qWait(10)

    assert len(calls) == 10
    assert dict(calls) == {
        "open_app": {"app_name": "Settings"},
        "open_bluetooth_settings": {},
        "open_system_settings": {"page": "sound"},
        "set_bluetooth_power": {"enabled": True},
        "repair_microphone": {},
        "list_windows": {},
        "close_window": {"title": "Terminal"},
        "type_text": {"text": "git status\n"},
        "run_terminal_command": {"command": "local-cli"},
        "close_ember_terminal": {},
    }
    assert {request_id for request_id, _result in results} == {
        "app",
        "bluetooth",
        "system-page",
        "bluetooth-power",
        "microphone",
        "windows",
        "close-window",
        "typing",
        "terminal",
        "close-terminal",
    }
    window.close()


def test_web_search_opens_chrome_and_types_into_its_address_bar(qapp, monkeypatch) -> None:
    calls = []
    transition_states = []
    event_order = []

    class FakeDesktopTools:
        def execute(self, name, args):
            if name == "open_app":
                assert window._chrome_dock_target is not None
                event_order.append("open_chrome")
            calls.append((name, args))
            return {"text": "ok"}

        def focus_address_bar(self):
            calls.append(("focus_address_bar", {}))

    window = CharacterWindow()
    window.settings.tool_tiers["open_app"] = "auto"
    window.settings.tool_tiers["type_text"] = "auto"
    window._desktop_tool_executor = FakeDesktopTools()
    monkeypatch.setattr(window, "_confirm_desktop_tool", lambda *_args: True)
    monkeypatch.setattr(
        window,
        "_show_conversation_window",
        lambda: window.conversation_window.show(),
    )

    def finish_transition(
        target,
        scale,
        final_state,
        _duration,
        finished,
        travel_state=AnimationState.WALKING,
    ):
        window.move(target)
        window._set_display_scale(scale)
        transition_states.append(travel_state)
        if travel_state == AnimationState.JUMPING:
            event_order.append("jump")
        window.animation.set_state(final_state)
        finished()

    monkeypatch.setattr(window, "_start_character_transition", finish_transition)
    monkeypatch.setattr(window, "_play_chime", lambda *_args: None)
    monkeypatch.setattr(
        window_module,
        "chrome_dock_icon_position",
        lambda _geometry: QPoint(24, 220),
    )

    window._submit_text("Open Google and search for cats")

    assert wait_until(lambda: not window._web_search_active, timeout=5)
    assert calls == [
        ("open_app", {"app_name": "Chrome"}),
        ("focus_address_bar", {}),
        ("type_text", {"text": "c"}),
        ("type_text", {"text": "a"}),
        ("type_text", {"text": "t"}),
        ("type_text", {"text": "s"}),
        ("type_text", {"text": "\n"}),
    ]
    assert window._web_search_bubble.message_label.text() == (
        window_module.COPY["en"]["web_search_done"]
    )
    assert not window._conversation_busy
    assert window._chrome_dock_target is None
    assert event_order[:2] == ["open_chrome", "jump"]

    window.conversation_window.close()
    window.ask_bubble.close()
    window.close()


def test_direct_chrome_open_skips_the_gemini_request(qapp, monkeypatch) -> None:
    calls = []

    class FakeDesktopTools:
        def execute(self, name, args):
            calls.append((name, args))
            return {"text": "تم فتح Chrome."}

    window = CharacterWindow()
    window.settings.tool_tiers["open_app"] = "auto"
    window._desktop_tool_executor = FakeDesktopTools()
    messages = []
    monkeypatch.setattr(
        window,
        "_show_conversation_window",
        lambda: window.conversation_window.show(),
    )
    add_message = window.conversation_window.add_message

    def capture_message(*args, **kwargs):
        message = add_message(*args, **kwargs)
        messages.append(message)
        return message

    monkeypatch.setattr(window.conversation_window, "add_message", capture_message)
    monkeypatch.setattr(window, "_play_chime", lambda *_args: None)
    monkeypatch.setattr(
        window,
        "_start_conversation",
        lambda *_args, **_kwargs: pytest.fail("Direct Chrome open called Gemini"),
    )

    window._submit_text("افتح كروم")

    assert calls == [("open_app", {"app_name": "Chrome"})]
    assert messages[-1].message_label.text() == (
        window_module.COPY["ar"]["chrome_opened"]
    )
    window.conversation_window.close()
    window.ask_bubble.close()
    window.close()


def test_api_quota_failure_stays_visible_in_settings(qapp, monkeypatch) -> None:
    window = CharacterWindow()
    warnings = []

    class FakeWorker:
        def wait(self):
            pass

        def deleteLater(self):
            pass

    window._gemini_worker = FakeWorker()
    window.settings_window = SimpleNamespace(
        set_api_quota_warning=warnings.append
    )
    monkeypatch.setattr(window.conversation_window, "add_message", lambda *_args, **_kwargs: None)

    window._gemini_request_failed(window_module.COPY["en"]["quota_error"])

    assert window._api_quota_exhausted
    assert warnings == [True]
    window.close()


def test_ask_desktop_tool_requires_confirmation_before_execution(
    qapp, monkeypatch
) -> None:
    results = []
    calls = []
    window = CharacterWindow()
    window._gemini_worker = SimpleNamespace(
        resolve_tool_call=lambda request_id, result: results.append(
            (request_id, result)
        )
    )
    window.settings.tool_tiers["take_screenshot_and_describe"] = "ask"
    window._desktop_tool_executor = SimpleNamespace(
        execute=lambda *args: calls.append(args)
    )
    monkeypatch.setattr(window, "_confirm_desktop_tool", lambda *_args: False)

    window._handle_desktop_tool(
        "request-2", "take_screenshot_and_describe", {}
    )

    assert not calls
    assert results == [
        ("request-2", {"text": "لم يوافق المستخدم على تنفيذ الإجراء."})
    ]
    window.close()


def test_screen_watch_button_starts_without_modal_and_stops_immediately(
    qapp, monkeypatch
) -> None:
    workers = []

    class FakeScreenWorker(QWidget):
        observation_ready = Signal(str)
        observation_failed = Signal(str)
        finished = Signal()

        def __init__(self, *_args, **_kwargs):
            super().__init__()
            self.started = False
            self.stopped = False
            workers.append(self)

        def start(self):
            self.started = True

        def stop(self):
            self.stopped = True

        def wait(self, *_args):
            return True

    window = CharacterWindow()
    window.api_key_store = SimpleNamespace(get_key=lambda: "test-key")
    window.settings.tool_tiers["take_screenshot_and_describe"] = "ask"
    monkeypatch.setattr(window_module, "ScreenWatchWorker", FakeScreenWorker)

    window._toggle_screen_watch(True)

    assert workers[0].started
    assert window.conversation_window.screen_watch_button.isChecked()
    assert window.settings_window is None

    window._toggle_screen_watch(False)

    assert workers[0].stopped
    assert not window.conversation_window.screen_watch_button.isChecked()
    assert window.settings_window is None
    window.close()


def test_wayland_linux_defaults_to_xwayland_but_respects_explicit_backend(
    monkeypatch,
) -> None:
    monkeypatch.setattr(ember_main.sys, "platform", "linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)

    ember_main._prefer_xwayland()

    assert os.environ["QT_QPA_PLATFORM"] == "xcb"
    monkeypatch.setenv("QT_QPA_PLATFORM", "wayland")
    ember_main._prefer_xwayland()
    assert os.environ["QT_QPA_PLATFORM"] == "wayland"
