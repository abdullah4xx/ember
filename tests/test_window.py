from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from ember.animation import AnimationState
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
) -> None:
    event = QMouseEvent(
        event_type,
        QPointF(local_x, local_y),
        QPointF(global_x, global_y),
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(window, event)


def test_left_drag_moves_window_without_triggering_happy_click(qapp) -> None:
    window = CharacterWindow()
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
    assert window.animation.state is AnimationState.IDLE
    window.close()


def test_left_click_without_drag_shows_happy_pose(qapp) -> None:
    window = CharacterWindow()
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
