from PySide6.QtGui import QImage, QPainter

from ember.animation import CharacterAnimation
from ember.character import (
    BODY_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    EYE_COLOR,
    LEG_COLOR,
    CharacterRenderer,
)


def test_renderer_paints_pixel_art_on_transparent_canvas(qapp) -> None:
    image = QImage(CANVAS_WIDTH, CANVAS_HEIGHT, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    CharacterRenderer().paint(painter, CharacterAnimation().pose())
    painter.end()

    assert image.pixelColor(140, 110) == BODY_COLOR
    assert image.pixelColor(156, 145) == EYE_COLOR
    assert image.pixelColor(140, 190) == LEG_COLOR
    assert image.pixelColor(20, 20).alpha() == 0
