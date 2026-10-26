"""Transparent always-on-top Qt window for the character."""

from __future__ import annotations

import math
import random
import time
from collections import deque
from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import (
    QEvent,
    QEventLoop,
    QPoint,
    QPointF,
    QRect,
    Qt,
    QTimer,
    Slot,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QGuiApplication,
    QMouseEvent,
    QPainter,
    QRegion,
    QTransform,
    QWindow,
)
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QWidget

from .animation import AnimationState, CharacterAnimation, Pose
from .character import (
    ARM_PIVOTS,
    BODY_RECT,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    GROUND_Y,
    LEFT_ARM_RECT,
    LEG_RECTS,
    RIGHT_ARM_RECT,
    CharacterRenderer,
    body_size,
    character_hit_test,
    transformed_bounds,
)
from .conversation import (
    AskBubble,
    ChimePlayer,
    ConversationWindow,
    GeminiReplyWorker,
    ScreenWatchWorker,
    MessageBubble,
    MicrophoneCapture,
    COPY,
    detect_conversation_language,
    response_language,
)
from .desktop_tools import (
    DesktopToolError,
    DesktopToolExecutor,
    DesktopToolWorker,
    ReadOnlyCommandWorker,
)
from .dock import DockTargetError, chrome_dock_icon_position
from .settings import ApiKeyStore, AppSettings, SecretStorageError, SettingsStore
from .settings_window import SettingsWindow
from .memory import LocalMemoryStore
from .wake_word import WakeWordListener
from .web_search import (
    WebSearchRequest,
    is_direct_chrome_open_request,
    parse_web_search_request,
)


class CharacterWindow(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setWindowTitle("Ember")
        self.settings_store = SettingsStore()
        self.settings = self.settings_store.load()
        self.display_scale = self.settings.display_scale
        self._home_scale = self.display_scale
        self.setFixedSize(
            round(CANVAS_WIDTH * self.display_scale),
            round(CANVAS_HEIGHT * self.display_scale),
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)
        self.animation = CharacterAnimation()
        self.renderer = CharacterRenderer()
        self._preferred_language = (
            self.settings.response_language
            if self.settings.response_language in ("ar", "en")
            else "ar"
        )
        self._right_button_active = False
        self._listen_started = False
        self._drag_origin: QPoint | None = None
        self._window_origin: QPoint | None = None
        self._drag_moved = False
        self._drag_armed = False
        self._native_drag = False
        self._drag_settling = False
        self._drag_samples: deque[tuple[float, QPoint]] = deque(maxlen=12)
        self._drag_target_position = QPointF()
        self._physics_active = False
        self._physics_velocity = QPointF()
        self._physics_last_tick = time.monotonic()
        self._wall_cling_side: str | None = None
        self._celebration_pending = False
        self._is_hanging = False
        self._orientation_angle = 0.0
        self._sleep_transition = False
        self._woke_hanging = False
        self._seated_for_chat = False
        self._chat_character_detached = False
        self._chat_return_state: tuple[QPoint, float, bool] | None = None
        self._attached_window: QWindow | None = None
        self._attachment_offset = QPoint()
        self._drag_preserve_scale = False
        self._transition_start = QPoint()
        self._transition_target = QPoint()
        self._transition_start_scale = self.display_scale
        self._transition_target_scale = self.display_scale
        self._transition_started = 0.0
        self._transition_duration = 0.75
        self._transition_final_state = AnimationState.IDLE
        self._transition_finished: Callable[[], None] | None = None
        self._last_activity = time.monotonic()
        self._conversation_history: list[tuple[str, str]] = []
        self._conversation_busy = False
        self._desktop_tool_executor: DesktopToolExecutor | None = None
        self._shell_command_workers: dict[str, ReadOnlyCommandWorker] = {}
        self._desktop_action_workers: dict[str, DesktopToolWorker] = {}
        self._memory_store = LocalMemoryStore()
        self._api_quota_exhausted = False
        self._web_search_active = False
        self._web_search_query = ""
        self._web_search_typed = ""
        self._web_search_bubble: MessageBubble | None = None
        self._web_search_character_active = False
        self._web_search_character_return: tuple[QPoint, float] | None = None
        self._chrome_dock_target: QPoint | None = None
        self._pending_voice_message: MessageBubble | None = None
        self._audio_capture: MicrophoneCapture | None = None
        self._shutting_down = False
        self._wake_recording = False
        self._wake_recording_started = 0.0
        self._last_voice_activity = 0.0
        self._gemini_worker: GeminiReplyWorker | None = None
        self._screen_watch_worker: ScreenWatchWorker | None = None
        self._last_screen_observation = ""
        self.api_key_store = ApiKeyStore()
        self.conversation_window = ConversationWindow()
        self.conversation_window.dismissed.connect(self._return_from_conversation)
        self.conversation_window.question_submitted.connect(self._submit_text)
        self.conversation_window.screen_watch_toggled.connect(
            self._toggle_screen_watch
        )
        self.conversation_window.position_changed.connect(
            self._sync_attached_character
        )
        self.ask_bubble = AskBubble()
        self.ask_bubble.message_submitted.connect(self._submit_text)
        self.ask_bubble.send_feedback.connect(
            lambda: self._play_chime("send")
        )
        self.ask_bubble.dismissed.connect(self._cancel_recording)
        self._wake_listener = WakeWordListener(self)
        self._wake_listener.wake_word_detected.connect(
            self._on_wake_word_detected
        )
        self._wake_listener.status_changed.connect(self._wake_status_changed)
        self.settings_window: SettingsWindow | None = None
        self._wake_recording_timer = QTimer(self)
        self._wake_recording_timer.setInterval(100)
        self._wake_recording_timer.timeout.connect(
            self._check_wake_recording_timeout
        )
        self._drag_hold_timer = QTimer(self)
        self._drag_hold_timer.setSingleShot(True)
        self._drag_hold_timer.setInterval(320)
        self._drag_hold_timer.timeout.connect(self._arm_drag)
        self._listen_timer = QTimer(self)
        self._listen_timer.setSingleShot(True)
        self._listen_timer.setInterval(350)
        self._listen_timer.timeout.connect(self._begin_listening)
        self._transition_timer = QTimer(self)
        self._transition_timer.setInterval(16)
        self._transition_timer.timeout.connect(self._advance_transition)
        self._web_search_timer = QTimer(self)
        self._web_search_timer.setInterval(42)
        self._web_search_timer.timeout.connect(self._type_web_search_character)
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(1000)
        self._idle_timer.timeout.connect(self._check_idle_sleep)
        self._idle_timer.start()
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._apply_input_mask()
        self._place_on_workarea()
        self._home_position = self.pos()
        self._update_wake_tooltip()

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceOver
        )
        painter.scale(self.display_scale, self.display_scale)
        pose = self.animation.pose()
        if self._orientation_angle:
            painter.translate(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)
            painter.rotate(self._orientation_angle)
            painter.translate(-CANVAS_WIDTH / 2, -CANVAS_HEIGHT / 2)
        render_pose = self._display_pose(pose)
        if self._is_hanging:
            render_pose = replace(render_pose, show_sleep_z=False)
        self.renderer.paint(
            painter,
            render_pose,
            show_shadow=not self._is_hanging,
            show_laptop=self._web_search_character_active,
        )
        self._paint_wake_indicator(painter)
        if self._is_hanging and pose.show_sleep_z:
            painter.save()
            painter.resetTransform()
            self.renderer.draw_sleep_marks(
                painter,
                pose.effect_phase,
                self.display_scale,
                (45.0, 128.0),
            )
            painter.restore()
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        point = event.position()
        x, y = self._canvas_point(point.x(), point.y())
        if character_hit_test(x, y, self._display_pose(self.animation.pose())):
            self._last_activity = time.monotonic()
            if self._physics_active or self._wall_cling_side is not None:
                self._physics_active = False
                self._wall_cling_side = None
                self.animation.set_state(AnimationState.IDLE)
            if event.button() == Qt.MouseButton.RightButton:
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self.open_settings()
                    event.accept()
                    return
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._show_context_menu(event.globalPosition().toPoint())
                    event.accept()
                    return
                if self._seated_for_chat:
                    event.accept()
                    return
                self._right_button_active = True
                self._listen_started = False
                self._listen_timer.start()
            elif event.button() == Qt.MouseButton.LeftButton:
                self._drag_origin = event.globalPosition().toPoint()
                self._window_origin = self.pos()
                self._drag_samples.clear()
                self._record_drag_sample(self._drag_origin)
                self._drag_target_position = QPointF(self.pos())
                self._drag_moved = False
                self._drag_armed = False
                self._native_drag = False
                self._drag_hold_timer.start()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self._drag_origin is not None
            and self._window_origin is not None
            and self._drag_armed
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            global_position = event.globalPosition().toPoint()
            self._record_drag_sample(global_position)
            offset = global_position - self._drag_origin
            if offset.manhattanLength() >= QApplication.startDragDistance():
                self._drag_moved = True
                if self._native_drag:
                    event.accept()
                    return
                if QGuiApplication.platformName().lower().startswith("wayland"):
                    handle = self.windowHandle()
                    if handle is not None and handle.startSystemMove():
                        self._native_drag = True
                        event.accept()
                        return
                self.animation.set_facing(
                    1 if offset.x() >= 0 else -1
                )
                target = self._window_origin + offset
                area = self._available_geometry()
                self._drag_target_position = QPointF(
                    self._clamp_position_to_workarea(target, area)
                )
                local = self.mapFromGlobal(global_position)
                x, y = self._canvas_point(local.x(), local.y())
                self.animation.set_mouse_position(x, y)
            event.accept()
            return
        x, y = self._canvas_point(event.position().x(), event.position().y())
        self.animation.set_mouse_position(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        dragged = False
        velocity = (0.0, 0.0)
        release_position = event.globalPosition().toPoint()
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._drag_origin is not None
        ):
            self._drag_hold_timer.stop()
            if not self._drag_moved:
                if self._seated_for_chat:
                    self._return_from_conversation()
                elif not self._is_hanging:
                    self.animation.trigger_affection()
                    self.animation.celebrate()
                    self._play_chime("pet")
            else:
                dragged = True
                self._record_drag_sample(release_position)
                velocity = self._drag_release_velocity()
                if self._native_drag:
                    self._home_position = self.pos()
                    self._woke_hanging = False
                    self._last_activity = time.monotonic()
                else:
                    self.move(self._drag_target_position.toPoint())
                    self._home_position = self.pos()
                    self._woke_hanging = False
                    self._last_activity = time.monotonic()
                self._drag_settling = False
            self._drag_origin = None
            self._window_origin = None
            self._drag_moved = False
            self._drag_armed = False
            self._native_drag = False
            self._drag_preserve_scale = False
            if dragged and not self._dock_on_window_at(release_position):
                self._start_throw(*velocity)
        if (
            event.button() == Qt.MouseButton.RightButton
            and self._right_button_active
        ):
            self._listen_timer.stop()
            self._right_button_active = False
            if self._listen_started:
                self._stop_recording()
                self.animation.set_state(AnimationState.IDLE)
            else:
                self._show_ask_bubble()
            self._listen_started = False
            self._last_activity = time.monotonic()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: QEvent) -> None:
        self.animation.set_mouse_position(190.0, 156.0)
        super().enterEvent(event)

    def eventFilter(self, watched, event) -> bool:
        event_type = event.type()
        if event_type in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.KeyPress,
        ):
            pointer = QCursor.pos()
            if self._is_hanging and event_type == QEvent.Type.MouseMove:
                self._wake_if_near(pointer)
            elif event_type == QEvent.Type.MouseMove and not self._drag_armed:
                self._set_gaze_from_global(pointer)
            close_bounds = self.geometry().adjusted(-125, -125, 125, 125)
            if (
                self._is_ember_surface(watched)
                or (
                    event_type == QEvent.Type.MouseMove
                    and close_bounds.contains(pointer)
                )
            ):
                self._last_activity = time.monotonic()
        return super().eventFilter(watched, event)

    def _is_ember_surface(self, watched: object) -> bool:
        if not isinstance(watched, QWidget):
            return False
        return watched.window() in (
            self,
            self.ask_bubble,
            self.conversation_window,
            self.settings_window,
        )

    def _tick(self) -> None:
        self._sync_attached_character()
        if (self._drag_armed and self._drag_moved) or self._drag_settling:
            if self._drag_origin is not None:
                self._record_drag_sample(QCursor.pos())
            current = self.pos()
            dx = self._drag_target_position.x() - current.x()
            dy = self._drag_target_position.y() - current.y()
            if math.hypot(dx, dy) < 1.5:
                self.move(self._drag_target_position.toPoint())
                if self._drag_settling:
                    self._drag_settling = False
                    self.animation.trigger_landing()
            else:
                self.move(
                    round(current.x() + dx * 0.42),
                    round(current.y() + dy * 0.42),
                )
        if self._physics_active:
            self._advance_physics()
        self.animation.update(0.033)
        self._apply_input_mask()
        self.update()

    def _record_drag_sample(self, position: QPoint) -> None:
        now = time.monotonic()
        self._drag_samples.append((now, QPoint(position)))
        while len(self._drag_samples) > 2 and now - self._drag_samples[0][0] > 0.18:
            self._drag_samples.popleft()

    def _drag_release_velocity(self) -> tuple[float, float]:
        if len(self._drag_samples) < 2:
            return 0.0, 0.0
        start_time, start_position = self._drag_samples[0]
        end_time, end_position = self._drag_samples[-1]
        elapsed = end_time - start_time
        if elapsed <= 0.015:
            return 0.0, 0.0
        velocity_x = (end_position.x() - start_position.x()) / elapsed
        velocity_y = (end_position.y() - start_position.y()) / elapsed
        speed = math.hypot(velocity_x, velocity_y)
        if speed > 1800:
            scale = 1800 / speed
            velocity_x *= scale
            velocity_y *= scale
        return velocity_x, velocity_y

    def _start_throw(self, velocity_x: float, velocity_y: float) -> None:
        self._physics_velocity = QPointF(velocity_x, velocity_y)
        self._physics_last_tick = time.monotonic()
        self._physics_active = True
        self._wall_cling_side = None
        self.animation.set_facing(1 if velocity_x >= 0 else -1)
        self.animation.set_state(AnimationState.FALLING)
        self._play_chime("throw")

    def _advance_physics(self) -> None:
        now = time.monotonic()
        dt = min(0.05, max(0.0, now - self._physics_last_tick))
        self._physics_last_tick = now
        if dt == 0:
            return

        velocity_x = self._physics_velocity.x() * math.exp(-0.18 * dt)
        velocity_y = self._physics_velocity.y() + 1850 * dt
        position = QPoint(
            round(self.x() + velocity_x * dt),
            round(self.y() + velocity_y * dt),
        )
        area = self._available_geometry()
        bounded = self._clamp_position_to_workarea(position, area)
        hit_left = position.x() < bounded.x()
        hit_right = position.x() > bounded.x()
        hit_top = position.y() < bounded.y()
        hit_floor = position.y() > bounded.y() and not hit_top
        self.move(bounded)

        if hit_floor:
            impact = abs(velocity_y)
            if impact >= 180:
                rebound = -impact * 0.28
                self.animation.set_state(AnimationState.FALLING)
                self.animation.trigger_landing()
                if abs(rebound) < 95:
                    self._physics_active = False
                    self.animation.set_state(AnimationState.IDLE)
                    self.animation.trigger_landing()
                    self._play_chime("landing")
                    self._home_position = self.pos()
                    self._home_scale = self.display_scale
                else:
                    self._physics_velocity = QPointF(velocity_x, rebound)
                    self._play_chime("jump")
            else:
                self._physics_active = False
                self.animation.set_state(AnimationState.IDLE)
                self.animation.trigger_landing()
                self._play_chime("landing")
                self._home_position = self.pos()
                self._home_scale = self.display_scale
            return

        if hit_top:
            velocity_y = abs(velocity_y) * 0.28
            self._play_chime("fall")
        if hit_left or hit_right:
            impact = abs(velocity_x)
            if impact < 260:
                self._physics_active = False
                self._wall_cling_side = "left" if hit_left else "right"
                self.animation.set_facing(1 if hit_left else -1)
                self.animation.set_state(AnimationState.CLINGING)
                self._play_chime("cling")
                self._home_position = self.pos()
                self._home_scale = self.display_scale
                return
            velocity_x = -velocity_x * 0.38

        self._physics_velocity = QPointF(velocity_x, velocity_y)

    def _canvas_point(self, x: float, y: float) -> tuple[float, float]:
        x /= self.display_scale
        y /= self.display_scale
        angle = math.radians(-self._orientation_angle)
        center_x, center_y = CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2
        dx, dy = x - center_x, y - center_y
        return (
            center_x + dx * math.cos(angle) - dy * math.sin(angle),
            center_y + dx * math.sin(angle) + dy * math.cos(angle),
        )

    def _display_pose(self, pose: Pose) -> Pose:
        if not self._is_hanging:
            return pose
        display_pose = replace(
            pose,
            body_y=0.0,
            body_stretch=0.0,
            sleep_amount=0.0,
        )
        if self.animation.state is AnimationState.SLEEPING:
            display_pose = replace(
                display_pose,
                closed_eyes=True,
                eye_opening=0.0,
            )
        return display_pose

    def _set_gaze_from_global(self, point: QPoint) -> None:
        local = self.mapFromGlobal(point)
        x, y = self._canvas_point(local.x(), local.y())
        self.animation.set_mouse_position(x, y)

    def open_settings(self) -> None:
        self._wake_listener.pause()
        self.ask_bubble.hide()
        if self.settings_window is None:
            self.settings_window = SettingsWindow(
                parent=self, memory_store=self._memory_store
            )
            self.settings_window.settings_applied.connect(self._apply_settings)
            self.settings_window.closed.connect(
                self._restore_conversation_after_settings
            )
        self._conversation_was_visible_for_settings = (
            self.conversation_window.isVisible()
        )
        self.settings_window.set_api_quota_warning(
            self._api_quota_exhausted
        )
        if self._conversation_was_visible_for_settings:
            self._stop_screen_watch()
            self.conversation_window.hide()
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _restore_conversation_after_settings(self) -> None:
        if (
            self._conversation_was_visible_for_settings
            and self.conversation_window is not None
        ):
            self._conversation_was_visible_for_settings = False
            self.conversation_window.show()
            self.conversation_window.raise_()
            self.conversation_window.activateWindow()
            self._sync_attached_character()
        self._resume_wake_listener_if_idle()

    def start_wake_word_listener(self) -> None:
        if not self._shutting_down and self.settings.wake_word_enabled:
            self._wake_listener.start()

    def _resume_wake_listener_if_idle(self) -> None:
        if self._shutting_down:
            return
        settings_visible = (
            self.settings_window is not None and self.settings_window.isVisible()
        )
        if (
            self.settings.wake_word_enabled
            and not self.ask_bubble.isVisible()
            and not self.conversation_window.isVisible()
            and not settings_visible
            and self._audio_capture is None
        ):
            self._wake_listener.start()

    def _wake_status_changed(self, _status: str) -> None:
        self._update_wake_tooltip()
        self._apply_input_mask()
        self.update()

    def _update_wake_tooltip(self) -> None:
        if not self.settings.wake_word_enabled:
            self.setToolTip("استماع كلمة التنبيه متوقف")
            return
        if self._wake_listener.is_listening:
            self.setToolTip("Ember يستمع محليًا لكلمة التنبيه. أوقفه من قائمة Ember.")
        else:
            self.setToolTip("استماع Ember المحلي قيد التجهيز أو متوقف مؤقتًا.")

    def _paint_wake_indicator(self, painter: QPainter) -> None:
        if not self.settings.wake_word_enabled:
            return
        color = QColor("#8BCB9B" if self._wake_listener.is_listening else "#D9A55F")
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#24221F"))
        painter.drawRoundedRect(QRect(268, 198, 24, 22), 7, 7)
        painter.setBrush(color)
        painter.drawEllipse(QRect(276, 205, 8, 8))
        painter.restore()

    def _apply_settings(self, value: AppSettings) -> None:
        wake_word_was_enabled = self.settings.wake_word_enabled
        self.settings = value
        if value.wake_word_enabled:
            self._resume_wake_listener_if_idle()
        else:
            self._wake_listener.stop()
        if wake_word_was_enabled != value.wake_word_enabled:
            self._update_wake_tooltip()
        self._home_scale = value.display_scale
        if self._chat_return_state is not None:
            position, _scale, was_hanging = self._chat_return_state
            self._chat_return_state = (
                position,
                value.display_scale,
                was_hanging,
            )
        if self._transition_timer.isActive():
            self._transition_target_scale = (
                self._conversation_character_scale(value.display_scale)
                if self._chat_return_state is not None
                else value.display_scale
            )
        else:
            scale = (
                self._conversation_character_scale(value.display_scale)
                if self._seated_for_chat
                and not self._chat_character_detached
                else value.display_scale
            )
            self._resize_preserving_anchor(scale)
        self._refresh_connection_status()
        self._apply_input_mask()
        self.update()

    def _begin_listening(self) -> None:
        if self._right_button_active:
            self._listen_started = True
            self._start_audio_capture()

    def _start_audio_capture(self, *, wake_word: bool = False) -> None:
        self._wake_listener.pause()
        self.animation.set_state(AnimationState.LISTENING)
        self._show_ask_bubble(focus=False)
        self.ask_bubble.set_recording(True)
        capture = MicrophoneCapture(self)
        self._audio_capture = capture
        self._wake_recording = wake_word
        if wake_word:
            self._wake_recording_started = time.monotonic()
            self._last_voice_activity = self._wake_recording_started
        capture.level_changed.connect(self.ask_bubble.waveform.set_level)
        capture.level_changed.connect(self._recording_level_changed)
        capture.recording_finished.connect(self._submit_audio)
        capture.recording_failed.connect(self._recording_failed)
        capture.start(self._preferred_language)
        if wake_word and self._audio_capture is capture:
            self._wake_recording_timer.start()

    def _on_wake_word_detected(self) -> None:
        if (
            not self.settings.wake_word_enabled
            or self.ask_bubble.isVisible()
            or self.conversation_window.isVisible()
            or (self.settings_window is not None and self.settings_window.isVisible())
        ):
            return
        self._last_activity = time.monotonic()
        self._start_audio_capture(wake_word=True)

    def _recording_level_changed(self, level: float) -> None:
        if self._wake_recording and level >= 0.018:
            self._last_voice_activity = time.monotonic()

    def _check_wake_recording_timeout(self) -> None:
        if not self._wake_recording or self._audio_capture is None:
            self._wake_recording_timer.stop()
            return
        now = time.monotonic()
        elapsed = now - self._wake_recording_started
        if elapsed >= 25 or (
            elapsed >= 1.5 and now - self._last_voice_activity >= 1.25
        ):
            self._wake_recording_timer.stop()
            self._wake_recording = False
            self._stop_recording()
            self.animation.set_state(AnimationState.IDLE)

    def _recording_failed(self, message: str) -> None:
        self._wake_recording_timer.stop()
        self._wake_recording = False
        self._listen_started = False
        self.animation.set_state(AnimationState.IDLE)
        self.ask_bubble.set_recording(False)
        self.ask_bubble.set_status(message)
        if self._audio_capture is not None:
            self._audio_capture.deleteLater()
            self._audio_capture = None

    def _stop_recording(self) -> None:
        self._wake_recording_timer.stop()
        self._wake_recording = False
        self.ask_bubble.set_recording(False)
        capture = self._audio_capture
        if capture is None:
            return
        self._audio_capture = None
        capture.stop(self._preferred_language)
        capture.deleteLater()

    def _cancel_recording(self) -> None:
        if self._audio_capture is not None:
            self._audio_capture.cancel()
            self._audio_capture.deleteLater()
            self._audio_capture = None
        self._listen_timer.stop()
        self._right_button_active = False
        self._listen_started = False
        self._wake_recording_timer.stop()
        self._wake_recording = False
        self.animation.set_voice_loudness(0)
        if self.animation.state is AnimationState.LISTENING:
            self.animation.set_state(AnimationState.IDLE)
        QTimer.singleShot(0, self._resume_wake_listener_if_idle)

    def _show_ask_bubble(self, focus: bool = True) -> None:
        self._wake_listener.pause()
        self.ask_bubble.set_language(self._preferred_language)
        self.ask_bubble.show_for_character(
            self.geometry(), self._available_geometry(), focus=focus
        )

    def _submit_text(self, question: str) -> None:
        language = response_language(
            question,
            self.settings.response_language,
            self.settings.same_language,
        )
        self._preferred_language = language
        self.ask_bubble.set_language(language)
        search_request = parse_web_search_request(question)
        if search_request is not None:
            self._start_web_search(question, language, search_request)
            return
        if is_direct_chrome_open_request(question):
            self._open_chrome_directly(question, language)
            return
        self._start_conversation(question, language)

    def _open_chrome_directly(self, question: str, language: str) -> None:
        self.ask_bubble.hide()
        self._show_conversation_window()
        conversation = self.conversation_window
        conversation.set_language(language)
        conversation.add_message(question, language, is_user=True)
        if self._conversation_busy:
            conversation.add_message(COPY[language]["wait"], language, False)
            return

        tier = self.settings.tool_tiers.get("open_app", "disabled")
        if tier not in ("auto", "ask"):
            conversation.add_message(
                COPY[language]["chrome_open_disabled"], language, False
            )
            return
        if tier == "ask" and not self._confirm_desktop_tool(
            "open_app", {"app_name": "Chrome"}
        ):
            conversation.add_message(
                COPY[language]["chrome_open_denied"], language, False
            )
            return

        try:
            if self._desktop_tool_executor is None:
                self._desktop_tool_executor = DesktopToolExecutor()
            self._desktop_tool_executor.execute(
                "open_app", {"app_name": "Chrome"}
            )
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            conversation.add_message(
                COPY[language]["chrome_open_failed"].format(error=error),
                language,
                False,
            )
            return
        self._play_chime("opened")
        conversation.add_message(
            COPY[language]["chrome_opened"], language, is_user=False
        )

    def _start_web_search(
        self, question: str, language: str, request: WebSearchRequest
    ) -> None:
        self.ask_bubble.hide()
        self._show_conversation_window()
        conversation = self.conversation_window
        conversation.set_language(language)
        conversation.add_message(question, language, is_user=True)
        if self._conversation_busy:
            conversation.add_message(COPY[language]["wait"], language, False)
            return
        if len(request.query) > 400:
            conversation.add_message(
                COPY[language]["web_search_failed"].format(
                    error=COPY[language]["too_long"]
                ),
                language,
                False,
            )
            return

        tiers = self.settings.tool_tiers
        if any(tiers.get(name, "disabled") == "disabled" for name in ("open_app", "type_text")):
            conversation.add_message(
                COPY[language]["web_search_disabled"], language, False
            )
            return
        if tiers.get("open_app") == "ask" and not self._confirm_desktop_tool(
            "open_app", {"app_name": "Chrome"}
        ):
            conversation.add_message(
                COPY[language]["web_search_denied"], language, False
            )
            return
        if tiers.get("type_text") == "ask" and not self._confirm_desktop_tool(
            "type_text", {"text": request.query}
        ):
            conversation.add_message(
                COPY[language]["web_search_denied"], language, False
            )
            return

        try:
            if self._desktop_tool_executor is None:
                self._desktop_tool_executor = DesktopToolExecutor()
            screen = QApplication.primaryScreen()
            if screen is None:
                raise DockTargetError("لا توجد شاشة متاحة.")
            self._chrome_dock_target = chrome_dock_icon_position(
                screen.geometry()
            )
        except DockTargetError:
            conversation.add_message(
                COPY[language]["chrome_dock_unavailable"], language, False
            )
            return
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            conversation.add_message(
                COPY[language]["web_search_failed"].format(error=error),
                language,
                False,
            )
            return
        search_text = request.query
        if request.host and request.host not in ("google.com", "www.google.com"):
            search_text = f"site:{request.host} {search_text}"
        self._web_search_query = search_text
        self._web_search_typed = ""
        self._web_search_bubble = conversation.add_message(
            COPY[language]["web_search_start"], language, is_user=False
        )
        self._conversation_busy = True
        conversation.set_busy(True)
        self._web_search_active = True
        self._launch_chrome_for_search()
        if self._web_search_active:
            QTimer.singleShot(0, self._move_to_chrome_dock)

    def _move_to_chrome_dock(self) -> None:
        if (
            not self._web_search_active
            or self._shutting_down
            or not self.conversation_window.isVisible()
            or self._chrome_dock_target is None
        ):
            return
        screen = QApplication.primaryScreen()
        if screen is None:
            self._finish_web_search("لا توجد شاشة متاحة.")
            return
        self._web_search_character_return = (QPoint(self.pos()), self.display_scale)
        self._detach_from_window()
        self._seated_for_chat = False
        self._web_search_character_active = True
        geometry = screen.geometry()
        target_scale = min(0.36, max(0.24, self._home_scale * 0.52))
        target_width = round(CANVAS_WIDTH * target_scale)
        target_height = round(CANVAS_HEIGHT * target_scale)
        icon_center = self._chrome_dock_target
        target_top = max(
            geometry.top(),
            icon_center.y() - target_height // 2,
        )
        approach = QPoint(
            max(
                geometry.left(),
                min(
                    icon_center.x() - round(target_width * 1.55),
                    geometry.right() - target_width,
                ),
            ),
            target_top,
        )
        self.raise_()
        self._start_character_transition(
            approach,
            target_scale,
            AnimationState.IDLE,
            0.82,
            self._jump_to_chrome_dock,
        )

    def _jump_to_chrome_dock(self) -> None:
        dock_target = self._chrome_dock_target
        if not self._web_search_active or dock_target is None:
            return
        target_scale = self.display_scale
        target_width = round(CANVAS_WIDTH * target_scale)
        self._start_character_transition(
            QPoint(
                dock_target.x() - target_width // 2,
                max(0, dock_target.y() - round(CANVAS_HEIGHT * target_scale) // 2),
            ),
            target_scale,
            AnimationState.IDLE,
            0.46,
            self._move_to_chrome_search,
            travel_state=AnimationState.JUMPING,
        )

    def _launch_chrome_for_search(self) -> None:
        if not self._web_search_active or self._desktop_tool_executor is None:
            return
        try:
            self._desktop_tool_executor.execute(
                "open_app", {"app_name": "Chrome"}
            )
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            self._finish_web_search(str(error))
            return
        self._play_chime("opened")

    def _move_to_chrome_search(self) -> None:
        if (
            not self._web_search_active
            or self._shutting_down
            or not self.conversation_window.isVisible()
        ):
            return
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            self._finish_web_search("لا توجد شاشة متاحة." if self._preferred_language == "ar" else "No screen is available.")
            return
        self._detach_from_window()
        self._seated_for_chat = False
        self._web_search_character_active = True
        geometry = screen.geometry()
        target_scale = min(0.36, max(0.24, self._home_scale * 0.52))
        target_width = round(CANVAS_WIDTH * target_scale)
        target_height = round(CANVAS_HEIGHT * target_scale)
        target = QPoint(
            max(geometry.left(), geometry.right() - target_width - 24),
            min(geometry.bottom() - target_height, geometry.top() + 34),
        )
        self.raise_()
        self._start_character_transition(
            target,
            target_scale,
            AnimationState.WALKING,
            0.95,
            self._begin_chrome_search_typing,
        )

    def _begin_chrome_search_typing(self) -> None:
        if not self._web_search_active:
            return
        try:
            if self._desktop_tool_executor is None:
                raise DesktopToolError("تعذر تهيئة أدوات سطح المكتب.")
            self._desktop_tool_executor.focus_address_bar()
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            self._finish_web_search(str(error))
            return
        self.animation.set_state(AnimationState.TYPING)
        self._web_search_timer.start()

    def _type_web_search_character(self) -> None:
        if not self._web_search_active:
            self._web_search_timer.stop()
            return
        if len(self._web_search_typed) < len(self._web_search_query):
            character = self._web_search_query[len(self._web_search_typed)]
            try:
                if self._desktop_tool_executor is None:
                    raise DesktopToolError("تعذر تهيئة أدوات سطح المكتب.")
                self._desktop_tool_executor.execute(
                    "type_text", {"text": character}
                )
            except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
                self._finish_web_search(str(error))
                return
            self._web_search_typed += character
            if self._web_search_bubble is not None:
                copy = COPY[self._preferred_language]
                self._web_search_bubble.message_label.setText(
                    f"{copy['web_search_typing']}\n{self._web_search_typed}"
                )
            return

        self._web_search_timer.stop()
        try:
            if self._desktop_tool_executor is None:
                raise DesktopToolError("تعذر تهيئة أدوات سطح المكتب.")
            self._desktop_tool_executor.execute("type_text", {"text": "\n"})
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            self._finish_web_search(str(error))
            return
        QTimer.singleShot(900, self._finish_web_search)

    def _finish_web_search(self, error: str | None = None) -> None:
        self._web_search_timer.stop()
        if not self._web_search_active:
            return
        self._web_search_active = False
        self._chrome_dock_target = None
        self._conversation_busy = False
        self.conversation_window.set_busy(False)
        if self._web_search_bubble is not None:
            copy = COPY[self._preferred_language]
            self._web_search_bubble.message_label.setText(
                copy["web_search_failed"].format(error=error)
                if error
                else copy["web_search_done"]
            )
        if error:
            self._play_chime("denied")
        self._return_character_from_chrome_search()

    def _return_character_from_chrome_search(self) -> None:
        return_state = self._web_search_character_return
        if (
            return_state is None
            or not self.conversation_window.isVisible()
            or self._shutting_down
        ):
            self._web_search_character_active = False
            self._web_search_character_return = None
            return
        position, scale = return_state
        self._start_character_transition(
            position,
            scale,
            AnimationState.SITTING,
            0.82,
            self._finish_chrome_search_return,
        )

    def _finish_chrome_search_return(self) -> None:
        self._web_search_character_active = False
        self._web_search_character_return = None
        self._seated_for_chat = True
        handle = self.conversation_window.windowHandle()
        if handle is not None:
            self._attach_to_window(handle)
        self.animation.set_state(
            AnimationState.THINKING
            if self._conversation_busy
            else AnimationState.SITTING
        )

    def _submit_audio(self, recording: bytes) -> None:
        preference = self.settings.response_language
        language = (
            "ar"
            if self.settings.same_language
            else preference if preference in ("ar", "en") else "ar"
        )
        self._preferred_language = language
        self._start_conversation(
            "",
            language,
            audio_data=recording,
            match_audio_language=self.settings.same_language,
        )

    def _start_conversation(
        self,
        question: str,
        language: str,
        audio_data: bytes | None = None,
        match_audio_language: bool = False,
    ) -> None:
        self.ask_bubble.hide()
        self._show_conversation_window()
        conversation = self.conversation_window
        conversation.set_language(language)
        user_message = conversation.add_message(
            question,
            language,
            is_user=True,
            voice=audio_data is not None,
        )
        if self._conversation_busy:
            conversation.add_message(
                COPY[language]["wait"],
                language,
                is_user=False,
            )
            return
        self._refresh_connection_status()
        try:
            api_key = self.api_key_store.get_key()
        except SecretStorageError:
            conversation.update_connection_status("error")
            conversation.add_message(COPY[language]["key_error"], language, False)
            return
        if not api_key:
            conversation.update_connection_status("missing")
            conversation.add_message(COPY[language]["missing_key"], language, False)
            return

        conversation.update_connection_status("checking")
        self._pending_voice_message = (
            user_message if audio_data is not None else None
        )
        conversation.set_busy(True)
        self._conversation_busy = True
        if self._seated_for_chat:
            self.animation.set_state(AnimationState.THINKING)
        worker = GeminiReplyWorker(
            api_key,
            self.settings.model,
            question,
            language,
            audio_data=audio_data,
            match_audio_language=match_audio_language,
            history=tuple(self._conversation_history),
            concise_replies=self.settings.concise_replies,
            attachments=conversation.take_pending_attachments(),
            screen_context=self._last_screen_observation,
        )
        self._conversation_history.append(
            ("user", question if question else "Voice message")
        )
        self._gemini_worker = worker
        worker.reply_ready.connect(
            self._gemini_reply_ready,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.request_failed.connect(
            self._gemini_request_failed,
            Qt.ConnectionType.QueuedConnection,
        )
        tool_requested = getattr(worker, "tool_requested", None)
        if tool_requested is not None:
            tool_requested.connect(
                self._handle_desktop_tool,
                Qt.ConnectionType.QueuedConnection,
            )
        worker.start()

    @Slot(str, str, object)
    def _handle_desktop_tool(
        self, request_id: str, name: str, arguments: object
    ) -> None:
        worker = self._gemini_worker
        if worker is None or not hasattr(worker, "resolve_tool_call"):
            return
        args = arguments if isinstance(arguments, dict) else {}
        allowed_tools = {
            "open_app",
            "open_url",
            "take_screenshot_and_describe",
            "click",
            "type_text",
            "scroll",
            "set_volume",
            "open_bluetooth_settings",
            "open_system_settings",
            "set_bluetooth_power",
            "repair_microphone",
            "list_windows",
            "close_window",
            "close_active_window",
            "run_shell_command",
            "run_terminal_command",
            "close_ember_terminal",
            "remember_this",
            "recall_memory",
            "forget_memory",
        }
        if name not in allowed_tools:
            worker.resolve_tool_call(
                request_id, {"text": "هذه العملية غير متاحة."}
            )
            return

        permission_name = "remember_this" if name in {
            "remember_this", "recall_memory", "forget_memory"
        } else name
        tier = self.settings.tool_tiers.get(permission_name, "disabled")
        if tier not in ("auto", "ask"):
            worker.resolve_tool_call(
                request_id, {"text": "هذا الإجراء معطّل في إعدادات Ember."}
            )
            return
        if tier == "ask":
            if not self._confirm_desktop_tool(name, args):
                self._play_chime("denied")
                worker.resolve_tool_call(
                    request_id, {"text": "لم يوافق المستخدم على تنفيذ الإجراء."}
                )
                return
            self._play_chime("approved")

        if name == "run_shell_command":
            command = args.get("command")
            if not isinstance(command, str):
                worker.resolve_tool_call(
                    request_id, {"text": "الأمر المحدد غير صالح."}
                )
                return
            command_worker = ReadOnlyCommandWorker(request_id, command)
            self._shell_command_workers[request_id] = command_worker
            command_worker.result_ready.connect(
                self._read_only_command_finished,
                Qt.ConnectionType.QueuedConnection,
            )
            command_worker.finished.connect(command_worker.deleteLater)
            command_worker.start()
            return

        if name in {
            "repair_microphone",
            "set_bluetooth_power",
            "list_windows",
            "close_window",
        }:
            if self._desktop_tool_executor is None:
                self._desktop_tool_executor = DesktopToolExecutor()
            action_worker = DesktopToolWorker(
                request_id,
                self._desktop_tool_executor,
                name,
                args,
            )
            self._desktop_action_workers[request_id] = action_worker
            action_worker.result_ready.connect(
                self._desktop_action_finished,
                Qt.ConnectionType.QueuedConnection,
            )
            action_worker.finished.connect(action_worker.deleteLater)
            action_worker.start()
            return

        try:
            if name == "remember_this":
                fact = args.get("fact")
                if not isinstance(fact, str):
                    raise ValueError("المعلومة المطلوب حفظها غير صالحة.")
                saved = self._memory_store.add(fact)
                result = {
                    "text": COPY[self._preferred_language][
                        "memory_saved" if saved else "memory_duplicate"
                    ]
                }
            elif name == "recall_memory":
                query = args.get("query", "")
                if not isinstance(query, str):
                    raise ValueError("عبارة البحث في الذاكرة غير صالحة.")
                facts = self._memory_store.search(query)
                result = {
                    "text": "\n".join(facts)
                    if facts
                    else COPY[self._preferred_language]["memory_empty"]
                }
            elif name == "forget_memory":
                fact = args.get("fact")
                if not isinstance(fact, str):
                    raise ValueError("المعلومة المطلوب حذفها غير صالحة.")
                removed = self._memory_store.remove_fact(fact)
                result = {
                    "text": COPY[self._preferred_language][
                        "memory_forgotten" if removed else "memory_not_found"
                    ]
                }
            else:
                if self._desktop_tool_executor is None:
                    self._desktop_tool_executor = DesktopToolExecutor()
                result = self._desktop_tool_executor.execute(name, args)
        except (DesktopToolError, OSError, RuntimeError, ValueError) as error:
            result = {"text": f"تعذر تنفيذ الإجراء: {error}"}
        except Exception as error:
            result = {"text": f"حدث خطأ أثناء تنفيذ الإجراء: {error}"}
        else:
            if name in {"open_app", "open_url"}:
                self._play_chime("opened")
        worker.resolve_tool_call(request_id, result)

    @Slot(str, object)
    def _read_only_command_finished(
        self, request_id: str, result: object
    ) -> None:
        self._shell_command_workers.pop(request_id, None)
        worker = self._gemini_worker
        if (
            worker is not None
            and hasattr(worker, "resolve_tool_call")
            and isinstance(result, dict)
        ):
            worker.resolve_tool_call(request_id, result)

    @Slot(str, object)
    def _desktop_action_finished(
        self, request_id: str, result: object
    ) -> None:
        self._desktop_action_workers.pop(request_id, None)
        worker = self._gemini_worker
        if (
            worker is not None
            and hasattr(worker, "resolve_tool_call")
            and isinstance(result, dict)
        ):
            worker.resolve_tool_call(request_id, result)

    @Slot(bool)
    def _toggle_screen_watch(self, enabled: bool) -> None:
        if not enabled:
            self._stop_screen_watch()
            return
        if self._screen_watch_worker is not None:
            self.conversation_window.set_screen_watch_active(True)
            return
        if self.settings.tool_tiers.get(
            "take_screenshot_and_describe", "disabled"
        ) == "disabled":
            self.conversation_window.set_screen_watch_active(False)
            self.conversation_window.add_message(
                (
                    "فعّل لقطات الشاشة من إعدادات الصلاحيات أولًا."
                    if self._preferred_language == "ar"
                    else "Enable screenshots in permissions first."
                ),
                self._preferred_language,
                is_user=False,
            )
            return
        try:
            api_key = self.api_key_store.get_key()
        except SecretStorageError:
            self.conversation_window.set_screen_watch_active(False)
            self.conversation_window.add_message(
                COPY[self._preferred_language]["key_error"],
                self._preferred_language,
                is_user=False,
            )
            return
        if not api_key:
            self.conversation_window.set_screen_watch_active(False)
            self.conversation_window.add_message(
                COPY[self._preferred_language]["missing_key"],
                self._preferred_language,
                is_user=False,
            )
            return
        screen = QApplication.primaryScreen()
        if screen is None:
            self.conversation_window.set_screen_watch_active(False)
            self.conversation_window.add_message(
                (
                    "لا توجد شاشة متاحة لبدء المشاهدة."
                    if self._preferred_language == "ar"
                    else "No screen is available to watch."
                ),
                self._preferred_language,
                is_user=False,
            )
            return
        geometry = screen.geometry()
        screen_geometry = (
            geometry.x(),
            geometry.y(),
            geometry.width(),
            geometry.height(),
        )
        language = self._preferred_language

        executor_holder: list[DesktopToolExecutor] = []

        def capture(cancel_event):
            if not executor_holder:
                executor_holder.append(DesktopToolExecutor())
            return executor_holder[0]._capture_screenshot(
                cancel_event=cancel_event,
                screen_geometry=screen_geometry,
            )

        screen_worker = ScreenWatchWorker(
            api_key,
            self.settings.model,
            capture,
            language=language,
        )
        self._screen_watch_worker = screen_worker
        screen_worker.observation_ready.connect(self._screen_observation_ready)
        screen_worker.observation_failed.connect(self._screen_watch_failed)
        screen_worker.finished.connect(self._screen_watch_finished)
        self._last_screen_observation = ""
        self.conversation_window.set_screen_watch_active(True)
        screen_worker.start()

    @Slot(str)
    def _screen_observation_ready(self, summary: str) -> None:
        if self._screen_watch_worker is not None:
            self._last_screen_observation = summary
            self.conversation_window.set_screen_observation(summary)
            self._api_quota_exhausted = False
            if self.settings_window is not None:
                self.settings_window.set_api_quota_warning(False)

    @Slot(str)
    def _screen_watch_failed(self, message: str) -> None:
        self.conversation_window.set_screen_watch_active(False)
        self._last_screen_observation = ""
        self.conversation_window.add_message(
            (
                f"توقفت مشاهدة الشاشة: {message}"
                if self._preferred_language == "ar"
                else f"Screen watch stopped: {message}"
            ),
            self._preferred_language,
            is_user=False,
        )
        if message == COPY[self._preferred_language]["quota_error"]:
            self._api_quota_exhausted = True
            if self.settings_window is not None:
                self.settings_window.set_api_quota_warning(True)

    @Slot()
    def _screen_watch_finished(self) -> None:
        worker = self.sender()
        if worker is self._screen_watch_worker:
            self._screen_watch_worker = None
            worker.deleteLater()

    def _stop_screen_watch(self) -> None:
        worker = self._screen_watch_worker
        self._last_screen_observation = ""
        self.conversation_window.set_screen_watch_active(False)
        if worker is not None:
            worker.stop()

    def _confirm_desktop_tool(
        self, name: str, args: dict[str, object]
    ) -> bool:
        labels = {
            "open_app": f"فتح التطبيق: {args.get('app_name', '')}",
            "open_url": f"فتح الرابط: {args.get('url', '')}",
            "take_screenshot_and_describe": (
                "التقاط الشاشة وإرسال الصورة إلى Gemini لتحليلها."
            ),
            "click": f"النقر عند الإحداثيات ({args.get('x', '?')}, {args.get('y', '?')})",
            "type_text": f"كتابة النص التالي في التطبيق النشط:\n{args.get('text', '')}",
            "scroll": (
                f"التمرير {args.get('direction', '')} عند "
                f"({args.get('x', '?')}, {args.get('y', '?')})"
            ),
            "set_volume": f"ضبط مستوى الصوت على {args.get('level', '?')}٪",
            "open_bluetooth_settings": "فتح إعدادات Bluetooth",
            "open_system_settings": (
                f"فتح صفحة إعدادات النظام: {args.get('page', '')}"
            ),
            "set_bluetooth_power": (
                "تشغيل Bluetooth"
                if args.get("enabled") is True
                else "إيقاف Bluetooth"
            ),
            "repair_microphone": "فحص وإصلاح إعدادات إدخال الميكروفون",
            "list_windows": "عرض النوافذ المفتوحة",
            "close_window": (
                f"إغلاق النافذة: {args.get('title', '')}"
            ),
            "close_active_window": "إغلاق النافذة النشطة (احفظ عملك أولًا)",
            "run_shell_command": (
                f"تشغيل الأمر المحدد للقراءة فقط: {args.get('command', '')}"
            ),
            "remember_this": f"حفظ هذه المعلومة محليًا:\n{args.get('fact', '')}",
            "recall_memory": f"البحث في الذكريات المحلية عن:\n{args.get('query', '')}",
            "forget_memory": f"حذف هذه المعلومة من الذاكرة:\n{args.get('fact', '')}",
        }
        dialog = QMessageBox(self.conversation_window)
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setWindowTitle("السماح لـEmber بالتحكم؟")
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setText(f"هل تريد تنفيذ الإجراء التالي؟\n\n{labels[name]}")
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.button(QMessageBox.StandardButton.Yes).setText("سماح")
        dialog.button(QMessageBox.StandardButton.No).setText("رفض")
        return dialog.exec() == QMessageBox.StandardButton.Yes

    @Slot(str, bool)
    def _gemini_reply_ready(
        self, answer: str, auto_language: bool
    ) -> None:
        worker = self._gemini_worker
        if worker is None:
            return
        worker.wait()
        self._conversation_busy = False
        self.conversation_window.set_busy(False)
        self.conversation_window.update_connection_status("connected")
        self._api_quota_exhausted = False
        if self.settings_window is not None:
            self.settings_window.set_api_quota_warning(False)
        if auto_language:
            self._preferred_language = detect_conversation_language(answer)
            self.conversation_window.set_language(self._preferred_language)
            if self._pending_voice_message is not None:
                self._pending_voice_message.set_voice_language(
                    self._preferred_language
                )
        self._pending_voice_message = None
        self.conversation_window.add_message(
            answer, self._preferred_language, is_user=False
        )
        self._play_chime("reply")
        self._conversation_history.append(("assistant", answer))
        if self._seated_for_chat:
            self.animation.celebrate(AnimationState.SITTING)
        else:
            self._celebration_pending = True
        QTimer.singleShot(220, lambda: self._play_chime("celebrate", 0.45))
        self._gemini_worker = None
        worker.deleteLater()

    @Slot(str)
    def _gemini_request_failed(
        self, message: str
    ) -> None:
        worker = self._gemini_worker
        if worker is None:
            return
        worker.wait()
        self._conversation_busy = False
        self.conversation_window.set_busy(False)
        self.conversation_window.update_connection_status("error")
        self._api_quota_exhausted = message in {
            COPY["ar"]["quota_error"],
            COPY["en"]["quota_error"],
        }
        if self.settings_window is not None:
            self.settings_window.set_api_quota_warning(
                self._api_quota_exhausted
            )
        self.conversation_window.add_message(
            message, self._preferred_language, is_user=False
        )
        if self._seated_for_chat:
            self.animation.set_state(AnimationState.CONFUSED)
        self._pending_voice_message = None
        self._gemini_worker = None
        worker.deleteLater()

    def _refresh_connection_status(self) -> None:
        try:
            has_key = bool(self.api_key_store.get_key())
        except SecretStorageError:
            status = "error"
        else:
            status = "unknown" if has_key else "missing"
        if hasattr(self, "conversation_window"):
            self.conversation_window.update_connection_status(status)

    def _show_conversation_window(self) -> None:
        if self.conversation_window.isVisible():
            return
        self._detach_from_window()
        self._chat_character_detached = False
        self._chat_return_state = (
            self.pos(),
            self._home_scale,
            self._is_hanging,
        )
        self._is_hanging = False
        self._orientation_angle = 0.0
        self._sleep_transition = False
        self._woke_hanging = False
        self.animation.set_state(AnimationState.WALKING)
        area = self._available_geometry()
        self.conversation_window.place_on_screen(area)
        self.conversation_window.show()
        self.conversation_window.raise_()
        self.raise_()
        target_scale = self._conversation_character_scale(
            self.settings.display_scale
        )
        target_width = round(CANVAS_WIDTH * target_scale)
        target_height = round(CANVAS_HEIGHT * target_scale)
        target = QPoint(
            self.conversation_window.x()
            + self.conversation_window.width() // 2
            - target_width // 2,
            max(
                area.top(),
                self.conversation_window.y() - round(target_height * 0.88),
            ),
        )
        self._seated_for_chat = False
        self._start_character_transition(
            target,
            target_scale,
            AnimationState.SITTING,
            1.18,
            self._finish_chat_arrival,
        )

    def _finish_chat_arrival(self) -> None:
        self._seated_for_chat = True
        handle = self.conversation_window.windowHandle()
        if handle is not None:
            self._attach_to_window(handle)
        self.animation.set_mouse_position(190.0, 220.0)
        if self._celebration_pending:
            self._celebration_pending = False
            self.animation.celebrate(AnimationState.SITTING)
        else:
            self.animation.set_state(
                AnimationState.THINKING
                if self._conversation_busy
                else AnimationState.SITTING
            )

    def _return_from_conversation(self) -> None:
        if not self.conversation_window.isVisible():
            return
        self._stop_screen_watch()
        if self._web_search_active:
            self._web_search_timer.stop()
            self._web_search_active = False
            self._chrome_dock_target = None
            self._conversation_busy = False
            self.conversation_window.set_busy(False)
            self._web_search_character_active = False
            self._web_search_character_return = None
        self.conversation_window.hide()
        self.ask_bubble.hide()
        if self._chat_character_detached:
            self._chat_return_state = None
            self._seated_for_chat = False
            self._chat_character_detached = False
            self._resume_wake_listener_if_idle()
            return
        self._detach_from_window()
        if self._chat_return_state is None:
            self._seated_for_chat = False
            self._resume_wake_listener_if_idle()
            return
        position, scale, was_hanging = self._chat_return_state
        self._chat_return_state = None
        self._seated_for_chat = False
        self._start_character_transition(
            position,
            scale,
            AnimationState.HANGING if was_hanging else AnimationState.IDLE,
            0.8,
            lambda hanging=was_hanging: self._finish_chat_return(hanging),
        )

    def _finish_chat_return(self, was_hanging: bool) -> None:
        self._is_hanging = was_hanging
        self._orientation_angle = 180.0 if was_hanging else 0.0
        self._woke_hanging = was_hanging
        self._home_position = self.pos()
        self._home_scale = self.display_scale
        self._last_activity = time.monotonic()
        self._resume_wake_listener_if_idle()

    def _start_character_transition(
        self,
        target: QPoint,
        scale: float,
        final_state: AnimationState,
        duration: float,
        finished: Callable[[], None],
        travel_state: AnimationState = AnimationState.WALKING,
    ) -> None:
        self._transition_timer.stop()
        self._transition_start = self.pos()
        self._transition_target = target
        self._transition_start_scale = self.display_scale
        self._transition_target_scale = scale
        self._transition_started = time.monotonic()
        self._transition_duration = duration
        self._transition_final_state = final_state
        self._transition_finished = finished
        direction = 1 if target.x() >= self.x() else -1
        self.animation.set_facing(direction)
        self.animation.set_state(travel_state)
        self._transition_timer.start()

    def _advance_transition(self) -> None:
        progress = min(
            1.0,
            (time.monotonic() - self._transition_started)
            / self._transition_duration,
        )
        eased = 1 - (1 - progress) ** 3
        if self._sleep_transition:
            self._orientation_angle = 180.0 * eased
        x = round(
            self._transition_start.x()
            + (self._transition_target.x() - self._transition_start.x()) * eased
        )
        y = round(
            self._transition_start.y()
            + (self._transition_target.y() - self._transition_start.y()) * eased
        )
        scale = self._transition_start_scale + (
            self._transition_target_scale - self._transition_start_scale
        ) * eased
        self.move(x, y)
        self._set_display_scale(scale)
        if progress < 1:
            return
        self._transition_timer.stop()
        self.animation.set_state(self._transition_final_state)
        finished = self._transition_finished
        self._transition_finished = None
        if finished is not None:
            finished()

    def _set_display_scale(self, scale: float) -> None:
        self.display_scale = scale
        self.setFixedSize(
            round(CANVAS_WIDTH * scale),
            round(CANVAS_HEIGHT * scale),
        )
        self._apply_input_mask()
        self.update()

    def _resize_preserving_anchor(self, scale: float) -> None:
        visible = self.mask().boundingRect()
        if visible.isNull():
            visible = self.rect()
        anchor = QPoint(
            self.x() + visible.center().x(),
            self.y() + visible.bottom(),
        )
        attached_window = self._attached_window
        self._set_display_scale(scale)
        if attached_window is not None:
            self._dock_to_window(
                attached_window, anchor.x(), update_chat_state=False
            )
            return
        visible = self.mask().boundingRect()
        if visible.isNull():
            visible = self.rect()
        self.move(
            anchor.x() - visible.center().x(),
            anchor.y() - visible.bottom(),
        )

    def _conversation_character_scale(self, display_scale: float) -> float:
        return max(0.18, min(0.6, display_scale * (140 / (CANVAS_WIDTH * 0.7))))

    def _attach_to_window(self, target: QWindow) -> None:
        if self._attached_window is target:
            self._attachment_offset = self.pos() - target.frameGeometry().topLeft()
            return
        self._attached_window = target
        self._attachment_offset = self.pos() - target.frameGeometry().topLeft()
        target.destroyed.connect(
            lambda *_args, attached=target: self._clear_attachment(attached)
        )

    def _clear_attachment(self, target: QWindow) -> None:
        if self._attached_window is target:
            self._attached_window = None
            self._attachment_offset = QPoint()

    def _detach_from_window(self) -> None:
        self._attached_window = None
        self._attachment_offset = QPoint()

    def _sync_attached_character(self, *_args: object) -> None:
        target = self._attached_window
        if (
            target is None
            or self._drag_origin is not None
            or self._physics_active
            or self._transition_timer.isActive()
            or not target.isVisible()
        ):
            return
        position = target.frameGeometry().topLeft() + self._attachment_offset
        if self.pos() != position:
            self.move(position)

    def _dock_to_window(
        self,
        target: QWindow,
        center_x: int,
        update_chat_state: bool = True,
    ) -> None:
        frame = target.frameGeometry()
        visible = self.mask().boundingRect()
        if visible.isNull():
            visible = self.rect()
        left = frame.left() - visible.left()
        right = max(left, frame.right() - visible.right())
        x = max(left, min(right, center_x - visible.center().x()))
        y = frame.top() - visible.bottom()
        self.move(x, y)
        self._attach_to_window(target)
        self._physics_active = False
        self._wall_cling_side = None
        self._drag_settling = False
        if update_chat_state:
            conversation_handle = self.conversation_window.windowHandle()
            chat_session_active = (
                self._chat_return_state is not None
                or self.conversation_window.isVisible()
            )
            self._seated_for_chat = (
                target is conversation_handle
                and self.conversation_window.isVisible()
            )
            self._chat_character_detached = (
                chat_session_active and target is not conversation_handle
            )
            self.animation.set_state(
                AnimationState.SITTING
                if self._seated_for_chat
                else AnimationState.PERCHING
            )
            if not self._seated_for_chat:
                self.animation.trigger_landing()
        self._home_position = self.pos()
        self._last_activity = time.monotonic()
        self.raise_()

    def _dock_on_window_at(self, position: QPoint) -> bool:
        if not self.settings.stand_on_windows:
            return False
        was_visible = self.isVisible()
        self.hide()
        QApplication.processEvents(
            QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
        )
        target = QGuiApplication.topLevelAt(position)
        if target is None:
            widget = QApplication.widgetAt(position)
            if widget is not None:
                target = widget.window().windowHandle()
        if was_visible:
            self.show()
            self.raise_()
        if target is None or target is self.windowHandle():
            return False
        self._dock_to_window(target, position.x())
        return True

    def _arm_drag(self) -> None:
        if self._drag_origin is None:
            return
        self._drag_preserve_scale = (
            self._seated_for_chat
            or self._chat_character_detached
            or self._attached_window is not None
        )
        if self._seated_for_chat or (
            self._transition_timer.isActive()
            and self._chat_return_state is not None
        ):
            self._detach_from_window()
            self._seated_for_chat = False
            self._chat_character_detached = True
            self._transition_timer.stop()
            self._transition_finished = None
            self.animation.set_state(AnimationState.IDLE)
            self._drag_origin = QCursor.pos()
            self._window_origin = self.pos()
        elif self._attached_window is not None:
            self._detach_from_window()
            self.animation.set_state(AnimationState.IDLE)
            self._drag_origin = QCursor.pos()
            self._window_origin = self.pos()
        elif self._transition_timer.isActive():
            self._transition_timer.stop()
            self._transition_finished = None
        if self._is_hanging:
            self._is_hanging = False
            self._woke_hanging = False
            self.animation.set_state(AnimationState.IDLE)
        if self._wall_cling_side is not None:
            self._wall_cling_side = None
            self.animation.set_state(AnimationState.IDLE)
        self._physics_active = False
        self._drag_samples.clear()
        self._record_drag_sample(QCursor.pos())
        if not self._drag_preserve_scale:
            self._set_display_scale(self._home_scale)
        self._drag_target_position = QPointF(self.pos())
        self._drag_settling = False
        self._drag_armed = True

    def _available_geometry(self) -> QRect:
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1280, 720)
        return self._workarea_to_screen_bottom(screen)

    @staticmethod
    def _workarea_to_screen_bottom(screen) -> QRect:
        available = screen.availableGeometry()
        geometry = screen.geometry()
        return QRect(
            available.left(),
            available.top(),
            available.width(),
            geometry.bottom() - available.top() + 1,
        )

    def _clamp_position_to_workarea(self, position: QPoint, area: QRect) -> QPoint:
        visible = self.mask().boundingRect()
        if visible.isNull():
            visible = self.rect()
        left = area.left() - visible.left()
        right = max(left, area.right() - visible.right())
        top = area.top() - visible.top()
        bottom = max(top, area.bottom() - visible.bottom())
        return QPoint(
            max(left, min(right, position.x())),
            max(top, min(bottom, position.y())),
        )

    def _check_idle_sleep(self) -> None:
        if (
            self._is_hanging
            or self._physics_active
            or self._wall_cling_side is not None
            or self._attached_window is not None
            or self._seated_for_chat
            or self._transition_timer.isActive()
            or self.ask_bubble.isVisible()
            or self.conversation_window.isVisible()
            or (self.settings_window is not None and self.settings_window.isVisible())
            or self._drag_origin is not None
            or self._drag_settling
            or self._right_button_active
            or self.settings.sleep_delay_minutes <= 0
        ):
            return
        if time.monotonic() - self._last_activity >= self.settings.sleep_delay_minutes * 60:
            self._enter_sleep()

    def _enter_sleep(self, play_sound: bool = False) -> None:
        area = self._available_geometry()
        max_x = max(area.left(), area.right() - self.width() + 1)
        x = random.randint(area.left(), max_x)
        self._is_hanging = False
        self._orientation_angle = 0.0
        self._sleep_transition = True
        self._woke_hanging = False
        self._apply_input_mask()
        y = area.top() - round((CANVAS_HEIGHT - GROUND_Y) * self.display_scale)

        def finish_sleep_entry() -> None:
            self._is_hanging = True
            self._orientation_angle = 180.0
            self._sleep_transition = False
            self.animation.set_state(AnimationState.SLEEPING)
            self._apply_input_mask()
            if play_sound:
                self._play_chime("sleep")
            self.update()

        self._start_character_transition(
            QPoint(x, y),
            self.display_scale,
            AnimationState.HANGING,
            0.95,
            finish_sleep_entry,
        )
        self.update()

    def _wake_if_near(self, pointer: QPoint) -> None:
        bounds = self.geometry()
        nearest_x = max(bounds.left(), min(pointer.x(), bounds.right()))
        nearest_y = max(bounds.top(), min(pointer.y(), bounds.bottom()))
        if math.hypot(pointer.x() - nearest_x, pointer.y() - nearest_y) > 125:
            return
        if self.animation.state is AnimationState.SLEEPING or (
            self._is_hanging and self._transition_timer.isActive()
        ):
            self._transition_timer.stop()
            self._transition_finished = None
            self.animation.set_state(AnimationState.HANGING)
            self._woke_hanging = True
            self._play_chime("wake")
            self._apply_input_mask()
            self.update()

    def _play_chime(self, name: str, volume_scale: float = 1.0) -> None:
        if not self.settings.sounds_enabled:
            return
        if not hasattr(self, "_chime_player"):
            self._chime_player = ChimePlayer(self)
        self._chime_player.play(
            name,
            round(self.settings.sound_volume * min(1.0, max(0.0, volume_scale))),
        )


    def _show_context_menu(self, position: QPoint) -> None:
        menu = QMenu(self)
        settings_action = menu.addAction("الإعدادات")
        wake_action = menu.addAction(
            "إيقاف الاستماع المحلي"
            if self.settings.wake_word_enabled
            else "تشغيل الاستماع إلى Ember"
        )
        mute_action = menu.addAction(
            "إلغاء كتم الأصوات" if not self.settings.sounds_enabled else "كتم الأصوات"
        )
        menu.addSeparator()
        sleep_action = menu.addAction("النوم الآن")
        quit_action = menu.addAction("إنهاء Ember")
        selected = menu.exec(position)
        if selected is settings_action:
            self.open_settings()
        elif selected is wake_action:
            self.settings.wake_word_enabled = not self.settings.wake_word_enabled
            self.settings_store.save(self.settings)
            if self.settings.wake_word_enabled:
                self._resume_wake_listener_if_idle()
            else:
                self._wake_listener.stop()
            self._update_wake_tooltip()
        elif selected is mute_action:
            self.settings.sounds_enabled = not self.settings.sounds_enabled
            self.settings_store.save(self.settings)
        elif selected is sleep_action:
            self._enter_sleep(play_sound=True)
        elif selected is quit_action:
            QApplication.quit()

    def _place_on_workarea(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = self._workarea_to_screen_bottom(screen)
        visible = self.mask().boundingRect()
        if visible.isNull():
            visible = self.rect()
        position = QPoint(
            area.center().x() - visible.center().x(),
            area.bottom() + 1 - round(GROUND_Y * self.display_scale),
        )
        clamped = self._clamp_position_to_workarea(position, area)
        self.move(clamped.x(), position.y())

    def _apply_input_mask(self) -> None:
        pose = self._display_pose(self.animation.pose())
        body_width, body_height = body_size(pose)
        body_rect = QRect(round(190 - body_width / 2), 100, body_width, body_height)
        body = transformed_bounds(
            body_rect,
            (190.0, 143.0),
            math.degrees(pose.lean),
            pose.body_y,
        )
        region = QRegion(body)
        for rect, pivot, angle in (
            (LEFT_ARM_RECT, ARM_PIVOTS[0], pose.arm_left),
            (RIGHT_ARM_RECT, ARM_PIVOTS[1], pose.arm_right),
        ):
            region |= QRegion(
                transformed_bounds(rect, pivot, angle, pose.body_y * 0.6)
            )
        for index, rect in enumerate(LEG_RECTS):
            sleep = pose.sleep_amount
            height = round(rect.height() * (1 - sleep) + 14 * sleep)
            top = round(rect.y() + sleep * 18 + pose.body_y * 0.18)
            region |= QRegion(
                transformed_bounds(
                    QRect(rect.x(), top, rect.width(), height),
                    (rect.x() + rect.width() / 2, float(rect.y())),
                    pose.leg_angles[index] * (1 - sleep),
                )
            )
        if self._orientation_angle == 0.0:
            region |= QRegion(QRect(122, 207, 136, 7))
        if self.settings.wake_word_enabled:
            region |= QRegion(QRect(268, 198, 24, 22))
        if pose.thought_dots:
            region |= QRegion(QRect(248, 74, 25, 24))
        if self._web_search_character_active:
            region |= QRegion(QRect(146, 153, 88, 49))
        if pose.show_sleep_z and not self._is_hanging:
            region |= QRegion(QRect(250, 75, 62, 54))
        if pose.landing_amount > 0:
            for x, y, width, height in (
                (116, 202, 5, 5),
                (124, 198, 4, 4),
                (134, 204, 4, 4),
                (246, 201, 5, 5),
                (255, 198, 4, 4),
                (264, 203, 4, 4),
            ):
                region |= QRegion(QRect(x, y, width, height))
        if self._orientation_angle:
            transform = QTransform()
            transform.translate(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)
            transform.rotate(self._orientation_angle)
            transform.translate(-CANVAS_WIDTH / 2, -CANVAS_HEIGHT / 2)
            region = transform.map(region)
        if self._is_hanging:
            if pose.show_sleep_z:
                region |= QRegion(QRect(38, 78, 88, 62))
        self.setMask(QTransform().scale(self.display_scale, self.display_scale).map(region))

    def closeEvent(self, event) -> None:
        self._shutting_down = True
        self._stop_screen_watch()
        if self._screen_watch_worker is not None:
            self._screen_watch_worker.wait(12_000)
        for worker in tuple(self._shell_command_workers.values()):
            worker.wait(5_500)
        self._web_search_timer.stop()
        self._web_search_active = False
        self._chrome_dock_target = None
        self._wake_listener.shutdown()
        if self._audio_capture is not None:
            self._audio_capture.cancel()
            self._audio_capture.deleteLater()
            self._audio_capture = None
        super().closeEvent(event)
