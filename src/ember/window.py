"""Transparent always-on-top Qt window for the character."""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QRegion, QTransform
from PySide6.QtWidgets import QApplication, QWidget

from .animation import AnimationState, CharacterAnimation
from .character import (
    ARM_PIVOTS,
    BODY_RECT,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    LEFT_ARM_RECT,
    LEG_RECTS,
    RIGHT_ARM_RECT,
    CharacterRenderer,
    character_hit_test,
    transformed_bounds,
)

DISPLAY_SCALE = 0.70


class CharacterWindow(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self.setWindowTitle("Ember")
        self.setFixedSize(
            round(CANVAS_WIDTH * DISPLAY_SCALE),
            round(CANVAS_HEIGHT * DISPLAY_SCALE),
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)
        self.animation = CharacterAnimation()
        self.renderer = CharacterRenderer()
        self._right_button_active = False
        self._drag_origin: QPoint | None = None
        self._window_origin: QPoint | None = None
        self._drag_moved = False
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._apply_input_mask()
        self._place_on_workarea()

    def paintEvent(self, event: QEvent) -> None:
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceOver
        )
        painter.scale(DISPLAY_SCALE, DISPLAY_SCALE)
        self.renderer.paint(painter, self.animation.pose())
        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        point = event.position()
        x, y = point.x() / DISPLAY_SCALE, point.y() / DISPLAY_SCALE
        if character_hit_test(x, y, self.animation.pose()):
            if event.button() == Qt.MouseButton.RightButton:
                self._right_button_active = True
                self.animation.set_state(AnimationState.LISTENING)
            elif event.button() == Qt.MouseButton.LeftButton:
                self._drag_origin = event.globalPosition().toPoint()
                self._window_origin = self.pos()
                self._drag_moved = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if (
            self._drag_origin is not None
            and self._window_origin is not None
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            global_position = event.globalPosition().toPoint()
            offset = global_position - self._drag_origin
            if offset.manhattanLength() >= QApplication.startDragDistance():
                self._drag_moved = True
                self.move(self._window_origin + offset)
            event.accept()
            return
        point = event.position()
        x, y = point.x() / DISPLAY_SCALE, point.y() / DISPLAY_SCALE
        if character_hit_test(x, y, self.animation.pose()):
            self.animation.set_mouse_position(x, y)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._drag_origin is not None
        ):
            if not self._drag_moved:
                self.animation.set_state(AnimationState.HAPPY)
            self._drag_origin = None
            self._window_origin = None
            self._drag_moved = False
        if (
            event.button() == Qt.MouseButton.RightButton
            and self._right_button_active
        ):
            self._right_button_active = False
            if self.animation.state is AnimationState.LISTENING:
                self.animation.set_state(AnimationState.IDLE)
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: QEvent) -> None:
        self.animation.set_mouse_position(190.0, 156.0)
        super().enterEvent(event)

    def _tick(self) -> None:
        self.animation.update(0.033)
        self._apply_input_mask()
        self.update()

    def _place_on_workarea(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        area = screen.availableGeometry()
        x = area.center().x() - self.width() // 2
        y = area.bottom() - self.height() + 1
        self.move(x, y)

    def _apply_input_mask(self) -> None:
        pose = self.animation.pose()
        body_width = round(120 + 30 * pose.sleep_amount)
        body_height = round(
            86 + pose.body_stretch * 35 - 22 * pose.sleep_amount
        )
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
        region |= QRegion(QRect(122, 207, 136, 7))
        if pose.thought_dots:
            region |= QRegion(QRect(248, 74, 25, 24))
        if pose.show_sleep_z:
            region |= QRegion(QRect(257, 95, 30, 34))
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
        self.setMask(
            QTransform().scale(DISPLAY_SCALE, DISPLAY_SCALE).map(region)
        )
