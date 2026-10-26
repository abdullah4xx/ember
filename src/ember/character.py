"""Pixel-art character definition and QPainter renderer."""

from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QPointF, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from .animation import AnimationState, CharacterAnimation, Pose

CANVAS_WIDTH = 380
CANVAS_HEIGHT = 250
GROUND_Y = 214

BODY_COLOR = QColor("#DA7756")
LEG_COLOR = QColor("#C15F3C")
EYE_COLOR = QColor("#17151F")

BODY_RECT = QRect(130, 100, 120, 86)
LEG_RECTS = tuple(QRect(x, 182, 16, 32) for x in (134, 166, 198, 230))
LEFT_ARM_RECT = QRect(104, 130, 28, 22)
RIGHT_ARM_RECT = QRect(248, 130, 28, 22)
ARM_PIVOTS = ((130.0, 141.0), (250.0, 141.0))
EYE_RECTS = (QRect(155, 142, 14, 28), QRect(211, 142, 14, 28))


def body_size(pose: Pose) -> tuple[int, int]:
    width = round(120 + 30 * pose.sleep_amount - min(0.0, pose.body_stretch) * 45)
    height = round(86 + pose.body_stretch * 35 - 22 * pose.sleep_amount)
    return width, height


def character_hit_test(x: float, y: float, pose: Pose | None = None) -> bool:
    """Return whether a canvas point lies on Ember or its soft ground shadow."""
    pose = pose or CharacterAnimation().pose()
    point = QPoint(round(x), round(y))
    body_width, body_height = body_size(pose)
    body_rect = QRect(round(190 - body_width / 2), 100, body_width, body_height)
    body_bounds = transformed_bounds(
        body_rect,
        (190.0, 143.0),
        math.degrees(pose.lean),
        pose.body_y,
    )
    if body_bounds.contains(point):
        return True
    for rect, pivot, angle in (
        (LEFT_ARM_RECT, ARM_PIVOTS[0], pose.arm_left),
        (RIGHT_ARM_RECT, ARM_PIVOTS[1], pose.arm_right),
    ):
        bounds = transformed_bounds(
            rect,
            pivot,
            angle,
            pose.body_y * 0.6,
        )
        if bounds.contains(point):
            return True
    for index, rect in enumerate(LEG_RECTS):
        sleep = pose.sleep_amount
        leg_height = round(rect.height() * (1 - sleep) + 14 * sleep)
        leg_top = round(rect.y() + sleep * 18 + pose.body_y * 0.18)
        bounds = transformed_bounds(
            QRect(rect.x(), leg_top, rect.width(), leg_height),
            (rect.x() + rect.width() / 2, float(rect.y())),
            pose.leg_angles[index] * (1 - sleep),
        )
        if bounds.contains(point):
            return True
    if QRect(122, 207, 136, 7).contains(point):
        return True
    if pose.thought_dots and QRect(248, 74, 25, 24).contains(point):
        return True
    if pose.show_sleep_z and QRect(250, 75, 62, 54).contains(point):
        return True
    return pose.landing_amount > 0 and any(
        QRect(x, y, width, height).contains(point)
        for x, y, width, height in (
            (116, 202, 5, 5),
            (124, 198, 4, 4),
            (134, 204, 4, 4),
            (246, 201, 5, 5),
            (255, 198, 4, 4),
            (264, 203, 4, 4),
        )
    )


def transformed_bounds(
    rect: QRect,
    pivot: tuple[float, float],
    angle_degrees: float,
    offset_y: float = 0.0,
) -> QRect:
    angle = math.radians(angle_degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    points = []
    for x, y in (
        (rect.x(), rect.y()),
        (rect.x() + rect.width(), rect.y()),
        (rect.x(), rect.y() + rect.height()),
        (rect.x() + rect.width(), rect.y() + rect.height()),
    ):
        dx = x - pivot[0]
        dy = y - pivot[1]
        points.append(
            (
                pivot[0] + dx * cosine - dy * sine,
                pivot[1] + dx * sine + dy * cosine + offset_y,
            )
        )
    left = math.floor(min(point[0] for point in points))
    top = math.floor(min(point[1] for point in points))
    right = math.ceil(max(point[0] for point in points))
    bottom = math.ceil(max(point[1] for point in points))
    return QRect(left, top, right - left, bottom - top)


class CharacterRenderer:
    """Draws Ember into an existing 380x250 QPainter canvas."""

    def paint(
        self,
        painter: QPainter,
        pose: Pose,
        show_shadow: bool = True,
        show_laptop: bool = False,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        painter.setPen(Qt.PenStyle.NoPen)
        if show_shadow:
            self._draw_shadow(painter, pose)
        self._draw_legs(painter, pose)
        self._draw_body(painter, pose)
        self._draw_arms(painter, pose)
        if show_laptop:
            self._draw_laptop(painter)
        self._draw_effects(painter, pose)
        painter.restore()

    @staticmethod
    def _draw_laptop(painter: QPainter) -> None:
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#252222"))
        painter.drawRect(QRect(153, 153, 74, 43))
        painter.setBrush(QColor("#e9ddca"))
        painter.drawRect(QRect(157, 157, 66, 34))
        painter.setBrush(QColor("#d87959"))
        painter.drawRect(QRect(162, 163, 18, 3))
        painter.drawRect(QRect(162, 170, 37, 3))
        painter.drawRect(QRect(162, 177, 28, 3))
        painter.setBrush(QColor("#403634"))
        painter.drawRect(QRect(146, 196, 88, 6))
        painter.setBrush(QColor("#8f7970"))
        painter.drawRect(QRect(181, 197, 18, 2))
        painter.restore()

    def _draw_shadow(self, painter: QPainter, pose: Pose) -> None:
        opacity = max(31, min(115, 72 - int(pose.body_y * 1.4)))
        painter.setBrush(QColor(0, 0, 0, opacity))
        painter.drawRect(QRect(122, 207, 136, 7))
        painter.drawRect(QRect(132, 204, 116, 3))

    def _draw_legs(self, painter: QPainter, pose: Pose) -> None:
        painter.setBrush(LEG_COLOR)
        for index, base_rect in enumerate(LEG_RECTS):
            hip_x = base_rect.x() + base_rect.width() / 2
            sleep = pose.sleep_amount
            height = round(base_rect.height() * (1 - sleep) + 14 * sleep)
            top = round(base_rect.y() + sleep * 18 + pose.body_y * 0.18)
            angle = pose.leg_angles[index] * (1 - sleep)
            painter.save()
            painter.translate(hip_x, float(base_rect.y()))
            painter.rotate(angle)
            painter.translate(-hip_x, -float(base_rect.y()))
            painter.drawRect(QRect(base_rect.x(), top, base_rect.width(), height))
            painter.restore()

    def _draw_body(self, painter: QPainter, pose: Pose) -> None:
        painter.save()
        painter.translate(190.0, 143.0 + pose.body_y)
        painter.rotate(math.degrees(pose.lean))
        painter.translate(-190.0, -143.0)
        painter.setBrush(BODY_COLOR)
        body_width, body_height = body_size(pose)
        body_left = round(190 - body_width / 2)
        painter.drawRect(QRect(body_left, 100, body_width, body_height))
        self._draw_eyes(painter, pose)
        self._draw_mouth(painter, pose)
        painter.restore()

    @staticmethod
    def _draw_mouth(painter: QPainter, pose: Pose) -> None:
        if pose.mouth_opening <= 0:
            return
        width = 7 + round(pose.mouth_opening * 5)
        height = 2 + round(pose.mouth_opening * 7)
        painter.setBrush(EYE_COLOR)
        painter.drawRect(QRect(190 - width // 2, 173, width, height))

    def _draw_eyes(self, painter: QPainter, pose: Pose) -> None:
        gaze_x = round(pose.gaze_x * 5)
        gaze_y = round(pose.gaze_y * 5)
        eye_y = round(142 - pose.sleep_amount * 21)
        if pose.closed_eyes:
            if pose.eye_opening > 0:
                eye_height = max(1, round(28 * pose.eye_opening))
                for rect in EYE_RECTS:
                    painter.drawRect(
                        QRect(
                            rect.x() + gaze_x,
                            eye_y + rect.height() - eye_height,
                            rect.width(),
                            eye_height,
                        )
                    )
                return
            pen = QPen(EYE_COLOR, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
            painter.setPen(pen)
            for rect in EYE_RECTS:
                y = eye_y + rect.height() - 8
                painter.drawLine(
                    rect.x() + gaze_x,
                    y,
                    rect.x() + rect.width() - 1 + gaze_x,
                    y,
                )
            painter.setPen(Qt.PenStyle.NoPen)
            return
        painter.setBrush(EYE_COLOR)
        if pose.happy_eyes:
            pen = QPen(EYE_COLOR, 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap)
            painter.setPen(pen)
            for rect in EYE_RECTS:
                center = rect.x() + rect.width() // 2 + gaze_x
                top = eye_y + 8 + gaze_y
                painter.drawLine(center - 7, top + 8, center, top)
                painter.drawLine(center, top, center + 7, top + 8)
            painter.setPen(Qt.PenStyle.NoPen)
            return
        eye_height = 32 if pose.surprised else 28
        for rect in EYE_RECTS:
            adjusted_y = eye_y + gaze_y - (2 if pose.surprised else 0)
            painter.drawRect(
                QRect(rect.x() + gaze_x, adjusted_y, rect.width(), eye_height)
            )

    def _draw_arms(self, painter: QPainter, pose: Pose) -> None:
        for rect, pivot, angle in (
            (LEFT_ARM_RECT, ARM_PIVOTS[0], pose.arm_left),
            (RIGHT_ARM_RECT, ARM_PIVOTS[1], pose.arm_right),
        ):
            painter.save()
            painter.translate(pivot[0], pivot[1] + pose.body_y * 0.6)
            painter.rotate(angle)
            painter.translate(-pivot[0], -pivot[1])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(BODY_COLOR)
            painter.drawRect(rect)
            painter.restore()

    def _draw_effects(self, painter: QPainter, pose: Pose) -> None:
        if pose.landing_amount > 0:
            opacity = round(210 * pose.landing_amount)
            painter.setBrush(QColor("#EBA27E"))
            painter.setOpacity(opacity / 255)
            spread = round((1 - pose.landing_amount) * 9)
            puff_positions = (
                (116 - spread, 202 - spread // 2, 5, 5),
                (124 - spread // 2, 198 - spread, 4, 4),
                (134 - spread // 3, 204, 4, 4),
                (246 + spread // 3, 201, 5, 5),
                (255 + spread // 2, 198 - spread, 4, 4),
                (264 + spread, 203 - spread // 2, 4, 4),
            )
            for x, y, width, height in puff_positions:
                painter.drawRect(QRect(x, y, width, height))
            painter.setOpacity(1.0)
        if pose.affection_amount > 0:
            age = 1.0 - pose.affection_amount
            painter.setBrush(QColor("#F06A91"))
            painter.setOpacity(pose.affection_amount)
            hearts = (
                ((155, 89), 3, 0.0),
                ((183, 73), 4, 0.7),
                ((219, 87), 3, 1.4),
            )
            pixels = (
                (0, 0), (1, 0), (3, 0), (4, 0),
                (0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
                (1, 2), (2, 2), (3, 2),
                (2, 3),
            )
            for (x, y), size, phase in hearts:
                rise = round(age * 25 + math.sin(pose.effect_phase * 8 + phase) * 2)
                for pixel_x, pixel_y in pixels:
                    painter.drawRect(
                        QRect(
                            x + pixel_x * size,
                            y - rise + pixel_y * size,
                            size,
                            size,
                        )
                    )
            painter.setOpacity(1.0)
        if pose.thought_dots:
            painter.setBrush(EYE_COLOR)
            for index in range(pose.thought_dots):
                painter.drawRect(QRect(248 + index * 10, 93 - index * 7, 5, 5))
        if pose.show_sleep_z:
            self.draw_sleep_marks(painter, pose.effect_phase)

    @staticmethod
    def draw_sleep_marks(
        painter: QPainter,
        effect_phase: float,
        scale: float = 1.0,
        origin: tuple[float, float] = (257.0, 124.0),
    ) -> None:
        for index in range(3):
            progress = ((effect_phase * 0.72 + index * 0.68) % 2.3) / 2.3
            x = (
                origin[0] + index * 12 + math.sin(effect_phase + index) * 1.5
            ) * scale
            y = (origin[1] - progress * 25) * scale
            painter.save()
            painter.setPen(QColor("#F18A3C"))
            painter.setOpacity(0.9 * (1.0 - progress))
            font = QFont("monospace", 11, QFont.Weight.Bold)
            font.setPixelSize(max(9, round(17 * scale)))
            painter.setFont(font)
            painter.translate(x, y)
            painter.rotate(math.sin(effect_phase * 0.7 + index) * 8)
            painter.drawText(QPointF(0, 0), "z")
            painter.restore()
