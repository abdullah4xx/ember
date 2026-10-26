from PySide6.QtGui import QImage, QPainter

from ember.animation import CharacterAnimation
from ember.character import (
    BODY_COLOR,
    BODY_RECT,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    EYE_RECTS,
    GROUND_Y,
    LEG_COLOR,
    LEG_RECTS,
    CharacterRenderer,
    character_hit_test,
)


def test_design_geometry_and_palette() -> None:
    assert (CANVAS_WIDTH, CANVAS_HEIGHT, GROUND_Y) == (380, 250, 214)
    assert (BODY_RECT.x(), BODY_RECT.y(), BODY_RECT.width(), BODY_RECT.height()) == (
        130,
        100,
        120,
        86,
    )
    assert tuple((r.x(), r.y(), r.width(), r.height()) for r in LEG_RECTS) == (
        (134, 182, 16, 32),
        (166, 182, 16, 32),
        (198, 182, 16, 32),
        (230, 182, 16, 32),
    )
    assert tuple((r.x(), r.y(), r.width(), r.height()) for r in EYE_RECTS) == (
        (155, 142, 14, 28),
        (211, 142, 14, 28),
    )
    assert BODY_COLOR.name() == "#da7756"
    assert LEG_COLOR.name() == "#c15f3c"


def test_hit_test_includes_character_and_excludes_empty_canvas() -> None:
    assert character_hit_test(150, 150)
    assert character_hit_test(110, 140)
    assert character_hit_test(140, 200)
    assert not character_hit_test(20, 20)
    assert not character_hit_test(190, 220)


def test_sleep_marks_float_and_fade_over_time(qapp) -> None:
    rendered = []
    for phase in (0.0, 1.0):
        image = QImage(380, 250, QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        CharacterRenderer.draw_sleep_marks(painter, phase)
        painter.end()
        rendered.append(image)

    assert rendered[0] != rendered[1]


def test_laptop_is_only_painted_when_requested(qapp) -> None:
    renderer = CharacterRenderer()
    pose = CharacterAnimation().pose()
    images = []

    for show_laptop in (False, True):
        image = QImage(380, 250, QImage.Format.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        renderer.paint(painter, pose, show_laptop=show_laptop)
        painter.end()
        images.append(image)

    assert images[0] != images[1]
