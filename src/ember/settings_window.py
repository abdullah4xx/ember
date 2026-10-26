"""Arabic, right-to-left preferences window for Ember."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sqlite3

from google import genai
from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    QThread,
    QTimer,
    QObject,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QCursor,
    QFontDatabase,
    QKeySequence,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtWidgets import (
    QCheckBox,
    QApplication,
    QAbstractSpinBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QKeySequenceEdit,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .animation import CharacterAnimation
from .character import CharacterRenderer
from .settings import (
    ApiKeyStore,
    AppSettings,
    SecretStorageError,
    SettingsStore,
    set_autostart,
)
from .memory import LocalMemoryStore

PAGES = (
    ("gemini", "Gemini وواجهة API", "المفتاح والنموذج وطريقة الرد"),
    ("voice", "الصوت واللغة", "الردود الصوتية والخصوصية"),
    ("behavior", "الحركة والراحة", "المشي والحجم وروتين النوم"),
    ("permissions", "الصلاحيات والأمان", "الأدوات والمجلدات والحدود"),
    ("memory", "الذاكرة", "معلومات تحفظها محليًا بإذنك"),
    ("shortcuts", "الاختصارات والتشغيل", "مفاتيح التحكم وبدء التشغيل"),
)

HOME_LINKS = (
    ("gemini", "01", "Gemini وواجهة API", "اختار عقل Ember"),
    ("voice", "02", "الصوت واللغة", "يسمعك ويرد عليك"),
    ("shortcuts", "06", "الاختصارات والتشغيل", "قريب منك دايمًا"),
    ("behavior", "03", "الحركة والراحة", "حياة صغيرة على سطح المكتب"),
    ("permissions", "04", "الصلاحيات والأمان", "أنت المتحكم دائمًا"),
    ("memory", "05", "الذاكرة", "ما طلبت من Ember أن يتذكره"),
)

PAGE_PRESENTATION = {
    "gemini": (
        "العقل",
        "الشرارة اللي بتحرّك Ember.",
        "اربط نموذج Gemini واختار طريقة رد Ember. في التطبيق الحقيقي، المفتاح مكانه مخزن مفاتيح النظام.",
    ),
    "voice": (
        "الصوت",
        "اسمعوا بعض بطبيعية.",
        "اختار طريقة استماع Ember وكلامه. يُرسل الصوت إلى Google فقط عند استخدام ميزات الصوت.",
    ),
    "behavior": (
        "الحركة",
        "حياة صغيرة على سطح مكتبك.",
        "اضبط سرعة Ember وأماكن تجوله وموعد استعداده لقيلولة.",
    ),
    "permissions": (
        "الحدود",
        "يساعدك، من غير ما يخرج عن سيطرتك.",
        "حدد ما يمكن لـEmber فعله تلقائيًا، وما يحتاج موافقتك، وما هو ممنوع دائمًا.",
    ),
    "memory": (
        "الذاكرة",
        "اللي تطلب منه يفتكره.",
        "تُحفظ الذكريات هنا على جهازك فقط. Ember لا يحفظ شيئًا إلا بطلبك، ويمكنك حذف أي ذكرى في أي وقت.",
    ),
    "shortcuts": (
        "التحكم السريع",
        "Ember، على بُعد ضغطة.",
        "اختار طريقة سريعة للوصول إلى Ember وإيقاف إجراء وبدء العمل عند تسجيل الدخول.",
    ),
}


class ToggleSwitch(QCheckBox):
    def __init__(self, accessible_name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAccessibleName(accessible_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(46, 28)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def sizeHint(self) -> QSize:
        return QSize(46, 28)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        checked = self.isChecked()
        track = QColor("#a3543a" if checked else "#35372f")
        border = QColor("#da7756" if checked else "#5a5c53")
        painter.setPen(QPen(border, 1))
        painter.setBrush(track)
        painter.drawRoundedRect(QRectF(1, 3, 44, 22), 11, 11)
        on_left = checked == (
            self.layoutDirection() == Qt.LayoutDirection.LeftToRight
        )
        knob_x = 5 if on_left else 23
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#fff0e4" if checked else "#cecdc4"))
        painter.drawEllipse(QRectF(knob_x, 7, 14, 14))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#f28c67"), 1))
            painter.drawRoundedRect(QRectF(0.5, 2.5, 45, 23), 12, 12)
        painter.end()


class EmberMark(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(48, 40)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#c15f3c"))
        for x in (134, 166, 198, 230):
            painter.drawRect(self._rect(x, 182, 16, 32))
        painter.setBrush(QColor("#da7756"))
        painter.drawRect(self._rect(104, 130, 28, 22))
        painter.drawRect(self._rect(248, 130, 28, 22))
        painter.drawRect(self._rect(130, 100, 120, 86))
        painter.setBrush(QColor("#17151f"))
        painter.drawRect(self._rect(155, 142, 14, 28))
        painter.drawRect(self._rect(211, 142, 14, 28))
        painter.end()

    def _rect(self, x: int, y: int, width: int, height: int) -> QRectF:
        scale_x = self.width() / 172
        scale_y = self.height() / 114
        return QRectF(
            (x - 104) * scale_x,
            (y - 100) * scale_y,
            width * scale_x,
            height * scale_y,
        )


class EmberPortrait(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.animation = CharacterAnimation()
        self.renderer = CharacterRenderer()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        scale = min(self.width() / 380, self.height() / 250)
        painter.translate(
            (self.width() - 380 * scale) / 2,
            (self.height() - 250 * scale) / 2,
        )
        painter.scale(scale, scale)
        self.renderer.paint(painter, self.animation.pose())
        painter.end()

    def _tick(self) -> None:
        self.animation.update(0.033)
        self.update()


class OrbitLink(QPushButton):
    def __init__(
        self,
        index: str,
        title: str,
        subtitle: str,
        page: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("orbitLink")
        self.setProperty("page", page)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(f"{title}: {subtitle}")
        self.setMinimumSize(150, 56)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 7, 10, 7)
        row.setSpacing(10)
        badge = QLabel(index)
        badge.setObjectName("orbitIndex")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(30, 30)
        copy = QVBoxLayout()
        copy.setSpacing(2)
        name = QLabel(title)
        name.setObjectName("orbitTitle")
        detail = QLabel(subtitle)
        detail.setObjectName("orbitSubtitle")
        name.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        detail.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        copy.addWidget(name)
        copy.addWidget(detail)
        arrow = QLabel("↗")
        arrow.setObjectName("orbitArrow")
        row.addWidget(badge)
        row.addLayout(copy, 1)
        row.addWidget(arrow)


class HomeStage(QWidget):
    CHARACTER_HOTSPOTS = {
        "gemini": (151, 91, 78, 58),
        "voice": (92, 119, 54, 48),
        "shortcuts": (234, 119, 54, 48),
        "behavior": (124, 175, 64, 46),
        "permissions": (192, 175, 64, 46),
    }

    def __init__(
        self,
        on_page_requested: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_page_requested = on_page_requested
        self._pressed_hotspot: str | None = None
        self.setObjectName("orbitStage")
        self.setMinimumHeight(390)
        self.setMouseTracking(True)
        self.links: dict[str, OrbitLink] = {}
        for page, index, title, subtitle in HOME_LINKS:
            link = OrbitLink(index, title, subtitle, page, self)
            link.setMouseTracking(True)
            link.installEventFilter(self)
            link.clicked.connect(
                lambda _checked=False, page=page: on_page_requested(page)
            )
            self.links[page] = link
        self.portrait = EmberPortrait(self)
        self.hotspot_buttons: dict[str, QPushButton] = {}
        for page, (x, y, width, height) in self.CHARACTER_HOTSPOTS.items():
            title = next(title for key, title, _subtitle in PAGES if key == page)
            hotspot = QPushButton(self)
            hotspot.setObjectName("characterHotspot")
            hotspot.setAccessibleName(f"فتح إعدادات {title}")
            hotspot.setToolTip(title)
            hotspot.setCursor(Qt.CursorShape.PointingHandCursor)
            hotspot.installEventFilter(self)
            hotspot.clicked.connect(
                lambda _checked=False, page=page: self._on_page_requested(page)
            )
            self.hotspot_buttons[page] = hotspot
        self.left_note = QLabel("✳  مرّر الماوس على Ember عشان تشوف وظيفة كل جزء.", self)
        self.left_note.setObjectName("stageNote")
        self.left_note.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.left_note.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignAbsolute
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.right_note = QLabel("متصمم لسطح مكتبك", self)
        self.right_note.setObjectName("stageNote")
        self.right_note.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.right_note.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        for link in self.links.values():
            link.raise_()
        self.left_note.raise_()
        self.right_note.raise_()
        for hotspot in self.hotspot_buttons.values():
            hotspot.raise_()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        position = event.position().toPoint()
        self._update_hotspot_hover(self._character_page_at(position))
        self._update_gaze(position)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed_hotspot = self._character_page_at(
                event.position().toPoint()
            )
            if self._pressed_hotspot is not None:
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            page = self._pressed_hotspot
            self._pressed_hotspot = None
            if page is not None and self._character_page_at(
                event.position().toPoint()
            ) == page:
                self._on_page_requested(page)
                event.accept()
                return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        QTimer.singleShot(0, self._reset_gaze_if_outside)
        self._update_hotspot_hover(None)
        super().leaveEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            event.type() == QEvent.Type.MouseMove
            and isinstance(watched, QWidget)
            and isinstance(event, QMouseEvent)
        ):
            global_position = watched.mapToGlobal(event.position().toPoint())
            position = self.mapFromGlobal(global_position)
            self._update_hotspot_hover(self._character_page_at(position))
            self._update_gaze(position)
        elif event.type() == QEvent.Type.Leave:
            QTimer.singleShot(0, self._reset_gaze_if_outside)
            self._update_hotspot_hover(None)
        elif (
            event.type() == QEvent.Type.Enter
            and watched in self.hotspot_buttons.values()
        ):
            page = next(
                key for key, button in self.hotspot_buttons.items() if button is watched
            )
            self._update_hotspot_hover(page)
        return super().eventFilter(watched, event)

    def _character_page_at(self, position: QPoint) -> str | None:
        scale = min(
            self.portrait.width() / 380,
            self.portrait.height() / 250,
        )
        if scale <= 0:
            return None
        origin_x = self.portrait.x() + (self.portrait.width() - 380 * scale) / 2
        origin_y = self.portrait.y() + (self.portrait.height() - 250 * scale) / 2
        character_x = (position.x() - origin_x) / scale
        character_y = (position.y() - origin_y) / scale
        for page, (x, y, width, height) in self.CHARACTER_HOTSPOTS.items():
            if x <= character_x <= x + width and y <= character_y <= y + height:
                return page
        return None

    def _update_hotspot_hover(self, page: str | None) -> None:
        self.setCursor(
            Qt.CursorShape.PointingHandCursor
            if page is not None
            else Qt.CursorShape.ArrowCursor
        )
        for key, link in self.links.items():
            active = key == page
            if link.property("linked") == active:
                continue
            link.setProperty("linked", active)
            link.style().unpolish(link)
            link.style().polish(link)

    def _update_gaze(self, position: QPoint) -> None:
        scale = self.portrait.width() / 380
        if scale <= 0:
            return
        self.portrait.animation.set_state("listening")
        self.portrait.animation.set_mouse_position(
            (position.x() - self.portrait.x()) / scale,
            (position.y() - self.portrait.y()) / scale,
        )

    def _reset_gaze_if_outside(self) -> None:
        position = self.mapFromGlobal(QCursor.pos())
        if not self.rect().contains(position):
            self.portrait.animation.set_state("idle")

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        clip = QPainterPath()
        clip.addRoundedRect(bounds, 24, 24)
        painter.setClipPath(clip)
        background = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        background.setColorAt(0, QColor("#1e201b"))
        background.setColorAt(1, QColor("#151714"))
        painter.fillPath(clip, background)
        glow = QRadialGradient(bounds.center(), min(self.width(), self.height()) * 0.48)
        glow.setColorAt(0, QColor(195, 103, 72, 28))
        glow.setColorAt(1, QColor(195, 103, 72, 0))
        painter.fillRect(bounds, glow)

        painter.setPen(QPen(QColor(244, 240, 232, 18), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(clip)
        painter.setPen(QColor("#85877e"))
        painter.drawText(
            QRectF(24, 12, 200, 22),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            "01   اختار قسمًا",
        )
        painter.drawText(
            QRectF(self.width() - 190, 12, 166, 22),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            "معاينة مباشرة   ●",
        )
        for x in range(16, self.width(), 19):
            for y in range(14, self.height(), 19):
                painter.setPen(QPen(QColor(244, 240, 232, 34), 1))
                painter.drawPoint(x, y)

        center = QPointF(self.width() / 2, self.height() / 2)
        diameter = min(460, self.height() * 0.96, self.width() * 0.58)
        for expansion, alpha in ((0, 31), (34, 7), (92, 5)):
            painter.setPen(QPen(QColor(218, 119, 86, alpha), 1))
            painter.drawEllipse(
                center,
                diameter / 2 + expansion,
                diameter / 2 + expansion,
            )

        painter.setPen(QPen(QColor(221, 164, 137, 54), 1, Qt.PenStyle.DashLine))
        anchors = {
            "gemini": (190, 100),
            "voice": (108, 141),
            "shortcuts": (272, 141),
            "behavior": (142, 212),
            "permissions": (238, 212),
        }
        character_rect = self.portrait.geometry()
        character_scale = min(character_rect.width() / 380, character_rect.height() / 250)
        for page, point in anchors.items():
            link = self.links[page]
            origin = link.geometry().center()
            target = QPointF(
                character_rect.x() + point[0] * character_scale,
                character_rect.y() + point[1] * character_scale,
            )
            route = QPainterPath(QPointF(origin))
            control = QPointF((origin.x() + target.x()) / 2, (origin.y() + target.y()) / 2)
            if page == "gemini":
                control.setY(control.y() - 18)
            elif page in ("voice", "shortcuts"):
                control.setY(control.y() - 14)
            else:
                control.setY(control.y() + 14)
            route.quadTo(control, target)
            painter.drawPath(route)
            painter.setPen(QPen(QColor("#da7756"), 1))
            painter.drawEllipse(target, 2, 2)
            painter.setPen(QPen(QColor(221, 164, 137, 54), 1, Qt.PenStyle.DashLine))

        painter.end()

    def resizeEvent(self, event: QResizeEvent) -> None:
        width = self.width()
        height = self.height()
        card_width = min(220, max(154, round(width * 0.22)))
        card_height = 58
        self.links["gemini"].setGeometry(
            (width - card_width) // 2, round(height * 0.09), card_width, card_height
        )
        self.links["voice"].setGeometry(
            round(width * 0.03), round(height * 0.43), card_width, card_height
        )
        self.links["shortcuts"].setGeometry(
            width - round(width * 0.03) - card_width,
            round(height * 0.43),
            card_width,
            card_height,
        )
        bottom_y = height - round(height * 0.08) - card_height
        self.links["behavior"].setGeometry(
            round(width * 0.09), bottom_y, card_width, card_height
        )
        self.links["permissions"].setGeometry(
            width - round(width * 0.09) - card_width,
            bottom_y,
            card_width,
            card_height,
        )
        portrait_width = min(
            760,
            round(width * 0.66),
            round(height * 380 / 250),
        )
        portrait_height = round(portrait_width * 250 / 380)
        self.portrait.setGeometry(
            (width - portrait_width) // 2,
            round(height * 0.53 - portrait_height / 2),
            portrait_width,
            portrait_height,
        )
        scale = min(portrait_width / 380, portrait_height / 250)
        origin_x = self.portrait.x() + (portrait_width - 380 * scale) / 2
        origin_y = self.portrait.y() + (portrait_height - 250 * scale) / 2
        for page, (x, y, hotspot_width, hotspot_height) in (
            self.CHARACTER_HOTSPOTS.items()
        ):
            self.hotspot_buttons[page].setGeometry(
                round(origin_x + x * scale),
                round(origin_y + y * scale),
                round(hotspot_width * scale),
                round(hotspot_height * scale),
            )
        self.left_note.setGeometry(22, height - 31, max(100, width // 2), 22)
        self.right_note.setGeometry(width - 220, height - 31, 198, 22)
        self.update()
        super().resizeEvent(event)

class ConnectionWorker(QThread):
    result_ready = Signal(bool, str)

    def __init__(
        self,
        api_key: str,
        model: str,
        probe: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._model = model
        self._probe = probe or self._probe_google

    def run(self) -> None:
        try:
            self._probe(self._api_key, self._model)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status is None:
                status = getattr(exc, "code", None)
            if status == 401 or status == 403:
                message = "رفض Google المفتاح أو لم يُفعّل له الوصول إلى Gemini."
            elif status == 429:
                message = "وصل المفتاح إلى حد الاستخدام أو الحصة. جرّب لاحقًا."
            else:
                message = (
                    "تعذر الاتصال بـGemini. تحقق من الإنترنت والمفتاح "
                    "وإتاحة النموذج في بلدك."
                )
            self.result_ready.emit(False, message)
            return
        self.result_ready.emit(True, "الاتصال ناجح، والمفتاح يستطيع الوصول إلى Gemini.")

    @staticmethod
    def _probe_google(api_key: str, model: str) -> None:
        client = genai.Client(api_key=api_key)
        try:
            selected = client.models.get(model=model)
            actions = getattr(selected, "supported_actions", ()) or ()
            if "generateContent" not in actions:
                raise ValueError("النموذج المحدد غير متاح لهذا المفتاح.")
        finally:
            client.close()


class ModelListWorker(QThread):
    models_ready = Signal(object)
    request_failed = Signal(str)

    def __init__(
        self,
        api_key: str,
        probe: Callable[[str], list[tuple[str, str]]] | None = None,
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._probe = probe or self._list_google_models

    def run(self) -> None:
        try:
            models = self._probe(self._api_key)
        except Exception as exc:
            self.request_failed.emit(str(exc) or "تعذر تحميل قائمة النماذج.")
            return
        self.models_ready.emit(models)

    @staticmethod
    def _list_google_models(api_key: str) -> list[tuple[str, str]]:
        client = genai.Client(api_key=api_key)
        try:
            models: dict[str, str] = {}
            for item in client.models.list(config={"page_size": 100}):
                actions = getattr(item, "supported_actions", ()) or ()
                name = getattr(item, "name", None)
                if not name or "generateContent" not in actions:
                    continue
                model_id = str(name).rsplit("/", 1)[-1]
                label = getattr(item, "display_name", None) or model_id
                models[model_id] = str(label)
            return sorted(
                ((model_id, label) for model_id, label in models.items()),
                key=lambda model: model[0].casefold(),
            )
        finally:
            client.close()


class SettingsWindow(QMainWindow):
    settings_applied = Signal(object)
    closed = Signal()

    def __init__(
        self,
        store: SettingsStore | None = None,
        key_store: ApiKeyStore | None = None,
        memory_store: LocalMemoryStore | None = None,
        connection_probe: Callable[[str, str], None] | None = None,
        autostart_writer: Callable[[bool], None] = set_autostart,
        parent: QWidget | None = None,
        model_list_probe: Callable[[str], list[tuple[str, str]]] | None = None,
    ) -> None:
        super().__init__(
            parent,
            Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setWindowTitle("إعدادات Ember")
        self.setObjectName("settingsWindow")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.resize(1280, 820)
        self.setMinimumSize(760, 580)
        self._font_family = "Noto Sans Arabic"
        self._font_bold_family = self._font_family
        for font_name in ("almotlaq-regular.ttf", "almotlaq-bold.ttf"):
            font_path = Path(__file__).with_name("assets") / font_name
            if font_path.is_file():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                families = (
                    QFontDatabase.applicationFontFamilies(font_id)
                    if font_id >= 0
                    else []
                )
                if families:
                    if font_name.endswith("-bold.ttf"):
                        self._font_bold_family = families[0]
                    else:
                        self._font_family = families[0]
        self.store = store or SettingsStore()
        self.key_store = key_store or ApiKeyStore()
        self.memory_store = memory_store or LocalMemoryStore()
        self.connection_probe = connection_probe
        self.model_list_probe = model_list_probe
        self.autostart_writer = autostart_writer
        self.settings = self.store.load()
        self._delete_api_key = False
        self._worker: ConnectionWorker | None = None
        self._models_worker: ModelListWorker | None = None
        self._models_loaded = False
        self._controls: dict[str, object] = {}
        self._build_ui()
        self._load_controls(self.settings)
        self._fit_home_stage()

    def _build_ui(self) -> None:
        stylesheet = """
            QMainWindow#settingsWindow, QWidget#settingsRoot, QWidget#homeView {
                background: #111310;
                color: #f4f0e8;
                font-family: "__FONT_REGULAR__";
                font-size: 14px;
            }
            QWidget#topBar {
                background: #111310;
                border-bottom: 1px solid rgba(242, 235, 221, 0.1);
            }
            QWidget#brandButton { background: transparent; }
            QLabel#brandName {
                color: #f4f0e8;
                font-family: "__FONT_BOLD__";
                font-size: 21px;
                font-weight: 700;
            }
            QLabel#brandCaption, QLabel#homeDescription { color: #aaa99f; }
            QLabel#topStatus { color: #b4c2a8; font-size: 10px; }
            QWidget#homeIntro { background: transparent; }
            QLabel#homeTitle {
                color: #f4f0e8;
                font-family: "__FONT_BOLD__";
                font-size: 36px;
                font-weight: 700;
            }
            QWidget#awakeCard {
                background: #1b1d19;
                border: 1px solid rgba(242, 235, 221, 0.1);
                border-radius: 14px;
            }
            QLabel#awakeMain {
                color: #f4f0e8;
                font-family: "__FONT_BOLD__";
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#awakeSub { color: #aaa99f; font-size: 10px; }
            QLabel#awakeSpark { color: #da7756; font-size: 16px; }
            QLabel#awakeDot { color: #96c8a5; font-size: 10px; }
            QWidget#settingsScreen { background: #111310; }
            QWidget#settingsSidebar {
                background: #171915;
                border-left: 1px solid rgba(242, 235, 221, 0.1);
            }
            QLabel#settingsBrand {
                color: #f4f0e8;
                font-family: "__FONT_BOLD__";
                font-size: 19px;
                font-weight: 700;
            }
            QLabel#settingsBrandSubtitle { color: #aaa99f; font-size: 12px; }
            QListWidget#settingsNavigation {
                background: #171915;
                border: 0;
                padding: 8px 10px;
                outline: 0;
                min-width: 205px;
            }
            QListWidget#settingsNavigation::item {
                padding: 11px 12px;
                margin: 3px 0;
                border-radius: 10px;
                color: #aaa99f;
            }
            QListWidget#settingsNavigation::item:selected {
                background: #292b25;
                color: #f4f0e8;
                font-weight: 600;
            }
            QListWidget#settingsNavigation::item:hover:!selected {
                background: #22241f;
            }
            QListWidget#allowedFolders {
                color: #f4f0e8;
                background: #1b1d19;
                border: 1px solid rgba(242, 235, 221, 0.14);
                border-radius: 10px;
                padding: 4px;
            }
            QListWidget#allowedFolders::item { padding: 4px 6px; }
            QLineEdit, QComboBox, QSpinBox, QKeySequenceEdit {
                min-height: 34px;
                color: #f4f0e8;
                background: #1b1d19;
                border: 1px solid rgba(242, 235, 221, 0.14);
                border-radius: 9px;
                padding: 3px 9px;
                selection-background-color: #a94f35;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
            QKeySequenceEdit:focus {
                border: 1px solid #da7756;
            }
            QLineEdit::placeholder { color: #aaa99f; }
            QComboBox::drop-down {
                border: 0;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                color: #f4f0e8;
                background: #1b1d19;
                selection-background-color: #292b25;
                border: 1px solid rgba(242, 235, 221, 0.14);
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #4b4844;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #da7756;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 15px;
                margin: -6px 0;
                border-radius: 7px;
                background: #da7756;
            }
            QCheckBox { color: #f4f0e8; spacing: 9px; }
            QPushButton {
                min-height: 34px;
                color: #f4f0e8;
                border: 1px solid rgba(242, 235, 221, 0.14);
                border-radius: 9px;
                padding: 3px 12px;
                background: #1b1d19;
            }
            QPushButton:hover { background: #292b25; }
            QPushButton:pressed { background: #33352e; }
            QPushButton#primaryButton {
                color: #fff;
                background: #c15f3c;
                border-color: #c15f3c;
                font-weight: 600;
            }
            QPushButton#primaryButton:hover { background: #da7756; }
            QPushButton:disabled {
                color: #777a70;
                background: #171915;
                border-color: #292b25;
            }
            QPushButton#quietButton {
                border: 0;
                background: transparent;
                color: #f28c67;
            }
            QPushButton#backButton, QPushButton#homeResetButton {
                border: 0;
                background: transparent;
                color: #aaa99f;
                min-height: 0;
                padding: 5px 0;
                font-size: 10px;
            }
            QPushButton#homeResetButton {
                text-decoration: underline;
            }
            QWidget#settingsPage { background: #111310; }
            QLabel#pageEyebrow {
                color: #f28c67;
                font-size: 9px;
                font-weight: 700;
            }
            QWidget#eyebrowLine { background: #da7756; }
            QLabel#pageTitle {
                color: #f4f0e8;
                font-family: "__FONT_BOLD__";
                font-size: 36px;
                font-weight: 700;
            }
            QLabel#pageDescription { color: #aaa99f; font-size: 13px; }
            QWidget#settingCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1f211c, stop:1 #191b17
                );
                border: 1px solid rgba(242, 235, 221, 0.1);
                border-radius: 15px;
            }
            QLabel#cardTitle {
                color: #f4f0e8;
                font-family: "__FONT_BOLD__";
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#cardDescription {
                color: #aaa99f;
                font-size: 10px;
            }
            QLabel#cardIcon {
                color: #f28c67;
                background: rgba(218, 119, 86, 0.075);
                border: 1px solid rgba(218, 119, 86, 0.2);
                border-radius: 10px;
                font-size: 15px;
            }
            QLabel#fieldLabel {
                color: #e7e3da;
                font-family: "__FONT_BOLD__";
                font-size: 10px;
                font-weight: 700;
            }
            QLabel#fieldHint, QLabel#settingRowHelp {
                color: #92938a;
                font-size: 9px;
            }
            QWidget#settingRow {
                border-top: 1px solid rgba(242, 235, 221, 0.1);
            }
            QWidget#settingRow[first="true"] { border-top: 0; }
            QLabel#settingRowTitle {
                color: #e7e3da;
                font-family: "__FONT_BOLD__";
                font-size: 10px;
                font-weight: 700;
            }
            QWidget#privacyCallout {
                background: rgba(166, 116, 54, 0.07);
                border: 1px solid rgba(207, 162, 100, 0.19);
                border-radius: 10px;
            }
            QLabel#calloutMark { color: #e0ac6b; font-size: 13px; }
            QLabel#calloutText { color: #d8c29d; font-size: 10px; }
            QLabel#statusValue { color: #a8d5b4; font-size: 10px; }
            QLabel#rangeValue {
                color: #d8b39e;
                font-size: 10px;
            }
            QLabel#readonlyValue {
                min-height: 39px;
                padding: 0 11px;
                color: #d8d7cf;
                background: #171915;
                border: 1px solid rgba(242, 235, 221, 0.13);
                border-radius: 9px;
            }
            QWidget#toolRow { border-top: 1px solid rgba(242, 235, 221, 0.1); }
            QWidget#toolRow:first-child { border-top: 0; }
            QLabel#forbiddenText { color: #baa29a; font-size: 10px; }
            QScrollArea { border: 0; background: #111310; }
            QScrollBar:vertical {
                width: 10px;
                background: transparent;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                min-height: 28px;
                border-radius: 4px;
                background: #555b50;
            }
            QWidget#settingsFooter {
                background: #111310;
                border-top: 1px solid rgba(242, 235, 221, 0.1);
            }
            QWidget#settingsToolbar {
                background: #111310;
                border-bottom: 1px solid rgba(242, 235, 221, 0.1);
            }
            QWidget#orbitStage {
                border: 1px solid rgba(240, 235, 219, 0.09);
                border-radius: 26px;
            }
            QPushButton#orbitLink {
                color: #f4f0e8;
                text-align: right;
                border: 1px solid rgba(242, 235, 221, 0.12);
                border-radius: 13px;
                padding: 0;
                background: rgba(25, 27, 23, 245);
            }
            QPushButton#orbitLink:hover {
                border-color: rgba(218, 119, 86, 0.58);
                background: #26231e;
            }
            QPushButton#orbitLink[linked="true"] {
                border-color: rgba(218, 119, 86, 0.58);
                background: #26231e;
            }
            QPushButton#characterHotspot {
                min-height: 0;
                min-width: 0;
                padding: 0;
                border: 1px solid transparent;
                border-radius: 9px;
                background: transparent;
            }
            QPushButton#characterHotspot:hover,
            QPushButton#characterHotspot:focus {
                border-color: rgba(242, 140, 103, 0.72);
                background: rgba(218, 119, 86, 0.08);
            }
            QLabel#orbitIndex {
                color: #e68d6d;
                border: 1px solid rgba(218, 119, 86, 0.27);
                border-radius: 9px;
                background: rgba(218, 119, 86, 0.08);
                font-size: 9px;
            }
            QLabel#orbitTitle { color: #f4f0e8; font-size: 11px; font-weight: 650; }
            QLabel#orbitSubtitle, QLabel#stageNote { color: #85877e; font-size: 9px; }
            QLabel#orbitArrow { color: #a2a297; font-size: 13px; }
            QLabel#homeFooterNote { color: #777a70; font-size: 10px; }
            """
        self.setStyleSheet(
            stylesheet.replace("__FONT_REGULAR__", self._font_family).replace(
                "__FONT_BOLD__", self._font_bold_family
            )
        )

        root = QWidget()
        root.setObjectName("settingsRoot")
        root.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar = QWidget()
        topbar.setObjectName("topBar")
        topbar.setFixedHeight(74)
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(52, 0, 52, 0)
        topbar_layout.setSpacing(10)
        topbar_status = QLabel("●  يعمل على سطح المكتب")
        topbar_status.setObjectName("topStatus")
        brand_button = QWidget()
        brand_button.setObjectName("brandButton")
        brand_layout = QHBoxLayout(brand_button)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(9)
        brand_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        mark = EmberMark()
        brand_name = QLabel("ember")
        brand_name.setObjectName("brandName")
        divider = QWidget()
        divider.setFixedSize(1, 19)
        divider.setStyleSheet("background: rgba(242, 235, 221, 0.17);")
        brand_caption = QLabel("رفيق سطح المكتب")
        brand_caption.setObjectName("brandCaption")
        brand_caption.setStyleSheet("font-size: 12px;")
        brand_layout.addWidget(mark)
        brand_layout.addWidget(brand_name)
        brand_layout.addWidget(divider)
        brand_layout.addWidget(brand_caption)
        topbar_layout.addWidget(topbar_status)
        topbar_layout.addStretch(1)
        topbar_layout.addWidget(brand_button)
        root_layout.addWidget(topbar)

        self.screen_stack = QStackedWidget()
        self.screen_stack.setObjectName("screenStack")

        home = QWidget()
        home.setObjectName("homeView")
        home_layout = QVBoxLayout(home)
        home_layout.setContentsMargins(52, 0, 52, 18)
        home_layout.setSpacing(0)
        intro = QWidget()
        intro.setObjectName("homeIntro")
        intro.setFixedHeight(150)
        intro_layout = QHBoxLayout(intro)
        intro_layout.setContentsMargins(10, 0, 10, 0)
        intro_layout.setSpacing(24)
        awake_card = QWidget()
        awake_card.setObjectName("awakeCard")
        awake_card.setFixedSize(207, 64)
        awake_card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        awake_layout = QHBoxLayout(awake_card)
        awake_layout.setContentsMargins(13, 8, 13, 8)
        awake_layout.setSpacing(9)
        awake_dot = QLabel("●")
        awake_dot.setObjectName("awakeDot")
        awake_copy = QVBoxLayout()
        awake_copy.setSpacing(2)
        awake_main = QLabel("Ember صاحي")
        awake_main.setObjectName("awakeMain")
        awake_sub = QLabel("جاهز نضبطه سوا")
        awake_sub.setObjectName("awakeSub")
        awake_copy.addWidget(awake_main)
        awake_copy.addWidget(awake_sub)
        awake_spark = QLabel("✳")
        awake_spark.setObjectName("awakeSpark")
        awake_layout.addWidget(awake_dot)
        awake_layout.addLayout(awake_copy, 1)
        awake_layout.addWidget(awake_spark)
        intro_copy = QWidget()
        intro_copy_layout = QVBoxLayout(intro_copy)
        intro_copy_layout.setContentsMargins(0, 16, 0, 12)
        intro_copy_layout.setSpacing(2)
        home_title = QLabel("خلّي Ember <span style='color:#da7756'>شبهك.</span>")
        home_title.setObjectName("homeTitle")
        home_title.setTextFormat(Qt.TextFormat.RichText)
        home_title.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        home_description = QLabel(
            "اختار جزءًا من Ember عشان تضبط طريقة عمل رفيقك على سطح المكتب."
        )
        home_description.setObjectName("homeDescription")
        home_description.setAlignment(Qt.AlignmentFlag.AlignRight)
        intro_copy_layout.addWidget(home_title)
        intro_copy_layout.addWidget(home_description)
        intro_layout.addWidget(awake_card)
        intro_layout.addStretch(1)
        intro_layout.addWidget(intro_copy, 2)
        home_layout.addWidget(intro)

        self.home_stage = HomeStage(self._open_settings_page)
        home_layout.addWidget(self.home_stage)
        home_footer = QWidget()
        home_footer.setFixedHeight(53)
        home_footer_layout = QHBoxLayout(home_footer)
        home_footer_layout.setContentsMargins(0, 0, 0, 0)
        home_footer_layout.setSpacing(20)
        self.home_reset_button = QPushButton("إعادة ضبط المعاينة")
        self.home_reset_button.setObjectName("homeResetButton")
        self.home_reset_button.clicked.connect(self._reset_defaults)
        home_footer_note = QLabel(
            "نموذج تفاعلي  ·  التغييرات تُحفظ على جهازك عند الضغط على حفظ"
        )
        home_footer_note.setObjectName("homeFooterNote")
        home_footer_layout.addWidget(self.home_reset_button)
        home_footer_layout.addStretch(1)
        home_footer_layout.addWidget(home_footer_note)
        home_layout.addWidget(home_footer)
        self.screen_stack.addWidget(home)

        settings_screen = QWidget()
        settings_screen.setObjectName("settingsScreen")
        settings_screen_layout = QVBoxLayout(settings_screen)
        settings_screen_layout.setContentsMargins(0, 0, 0, 0)
        settings_screen_layout.setSpacing(0)
        settings_body = QWidget()
        settings_body_layout = QHBoxLayout(settings_body)
        settings_body_layout.setContentsMargins(0, 0, 0, 0)
        settings_body_layout.setSpacing(0)
        settings_body_layout.setDirection(QHBoxLayout.Direction.RightToLeft)

        sidebar = QWidget()
        sidebar.setObjectName("settingsSidebar")
        sidebar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        sidebar.setFixedWidth(248)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(13, 20, 13, 12)
        sidebar_layout.setSpacing(3)
        back_button = QPushButton("←  العودة إلى Ember")
        back_button.setObjectName("backButton")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.clicked.connect(self._show_home)
        sidebar_layout.addWidget(back_button)
        brand = QLabel("Ember")
        brand.setObjectName("settingsBrand")
        brand.setContentsMargins(10, 16, 10, 0)
        subtitle = QLabel("رفيق سطح المكتب")
        subtitle.setObjectName("settingsBrandSubtitle")
        subtitle.setContentsMargins(10, 0, 10, 16)
        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)

        self.navigation = QListWidget()
        self.navigation.setObjectName("settingsNavigation")
        self.navigation.setSpacing(2)
        self.pages = QStackedWidget()
        self._page_effects: list[QGraphicsOpacityEffect] = []
        self._page_animation: QPropertyAnimation | None = None
        for key, title, page_subtitle in PAGES:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setToolTip(page_subtitle)
            self.navigation.addItem(item)
            page = self._make_page(key, title, page_subtitle)
            effect = QGraphicsOpacityEffect(page)
            effect.setOpacity(1.0)
            page.setGraphicsEffect(effect)
            self._page_effects.append(effect)
            self.pages.addWidget(page)
        self.navigation.currentRowChanged.connect(self._switch_page)
        self.navigation.setCurrentRow(0)
        sidebar_layout.addWidget(self.navigation, 1)
        settings_body_layout.addWidget(sidebar)

        settings_content = QWidget()
        settings_content_layout = QVBoxLayout(settings_content)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)
        settings_content_layout.setSpacing(0)
        toolbar = QWidget()
        toolbar.setObjectName("settingsToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        toolbar_layout.setContentsMargins(34, 10, 34, 10)
        self.settings_breadcrumb = QLabel("التفضيلات  /  Gemini وواجهة API")
        self.settings_breadcrumb.setStyleSheet("color: #777a70; font-size: 10px;")
        toolbar_layout.addWidget(self.settings_breadcrumb)
        toolbar_layout.addStretch(1)
        self.reset_button = QPushButton("استعادة الافتراضي")
        self.reset_button.setObjectName("homeResetButton")
        self.reset_button.clicked.connect(self._reset_defaults)
        toolbar_layout.addWidget(self.reset_button)
        settings_content_layout.addWidget(toolbar)
        settings_content_layout.addWidget(self.pages, 1)
        settings_body_layout.addWidget(settings_content, 1)
        settings_screen_layout.addWidget(settings_body, 1)

        footer = QWidget()
        footer.setObjectName("settingsFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        footer_layout.setContentsMargins(22, 10, 22, 10)
        self.save_status = QLabel("")
        self.save_status.setObjectName("saveStatus")
        self.save_status.setStyleSheet("color: #aaa99f;")
        self.close_button = QPushButton("إغلاق")
        self.save_button = QPushButton("حفظ التغييرات")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._save)
        self.close_button.clicked.connect(self.close)
        footer_layout.addWidget(self.save_status, 1)
        footer_layout.addWidget(self.close_button)
        footer_layout.addWidget(self.save_button)
        settings_screen_layout.addWidget(footer)
        self.screen_stack.addWidget(settings_screen)
        root_layout.addWidget(self.screen_stack, 1)
        self.setCentralWidget(root)
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(1280, available.width())
            height = min(820, available.height() - 40)
            self.resize(max(760, width), max(580, height))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if hasattr(self, "home_stage"):
            self._fit_home_stage()

    def _fit_home_stage(self) -> None:
        target = min(
            550,
            max(390, min(round(self.width() * 0.40), self.height() - 340)),
        )
        self.home_stage.setFixedHeight(target)

    def _make_page(self, key: str, title: str, subtitle: str) -> QWidget:
        scroll = QScrollArea()
        scroll.setObjectName("settingsScrollArea")
        scroll.viewport().setStyleSheet("background-color: #111310;")
        scroll.setWidgetResizable(True)
        page = QWidget()
        page.setObjectName("settingsPage")
        page.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        page.setStyleSheet("QWidget#settingsPage { background-color: #111310; }")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(58, 34, 58, 36)
        layout.setSpacing(0)
        eyebrow, page_title, description = PAGE_PRESENTATION[key]
        eyebrow_row = QWidget()
        eyebrow_layout = QHBoxLayout(eyebrow_row)
        eyebrow_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        eyebrow_layout.setContentsMargins(0, 0, 0, 0)
        eyebrow_layout.setSpacing(9)
        line = QWidget()
        line.setObjectName("eyebrowLine")
        line.setFixedSize(22, 1)
        eyebrow_label = QLabel(f"{PAGES.index((key, title, subtitle)) + 1:02d}  {eyebrow}")
        eyebrow_label.setObjectName("pageEyebrow")
        eyebrow_layout.addWidget(line)
        eyebrow_layout.addWidget(eyebrow_label)
        eyebrow_layout.addStretch(1)
        layout.addWidget(eyebrow_row)
        layout.addSpacing(9)
        heading = QLabel(page_title)
        heading.setObjectName("pageTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        description_label = QLabel(description)
        description_label.setObjectName("pageDescription")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(heading)
        layout.addWidget(description_label)
        layout.addSpacing(25)
        if key == "gemini":
            self._build_gemini_page(layout)
        elif key == "voice":
            self._build_voice_page(layout)
        elif key == "behavior":
            self._build_behavior_page(layout)
        elif key == "permissions":
            self._build_permissions_page(layout)
        elif key == "memory":
            self._build_memory_page(layout)
        else:
            self._build_shortcuts_page(layout)
        layout.addSpacing(10)
        scroll.setWidget(page)
        return scroll

    def _section(self, layout: QVBoxLayout, title: str) -> QFormLayout:
        heading = QLabel(title)
        heading.setStyleSheet(
            "font-size: 16px; font-weight: 650; color: #f4f0e8; "
            "padding-top: 8px;"
        )
        layout.addWidget(heading)
        form = QFormLayout()
        form.setHorizontalSpacing(22)
        form.setVerticalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setFormAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        layout.addLayout(form)
        return form

    def _add_row(self, form: QFormLayout, label: str, widget: QWidget) -> None:
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(150)
        label_widget.setStyleSheet("color: #aaa99f;")
        form.addRow(label_widget, widget)

    def _add_note(self, layout: QVBoxLayout, text: str) -> None:
        note = QWidget()
        note.setObjectName("privacyCallout")
        note.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        row = QHBoxLayout(note)
        row.setContentsMargins(13, 11, 13, 11)
        row.setSpacing(10)
        mark = QLabel("◇")
        mark.setObjectName("calloutMark")
        copy = QLabel(text)
        copy.setObjectName("calloutText")
        copy.setWordWrap(True)
        copy.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(mark, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(copy, 1)
        layout.addWidget(note)

    def _note_card(self, layout: QVBoxLayout, text: str) -> None:
        card = QWidget()
        card.setObjectName("settingCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        self._add_note(card_layout, text)
        layout.addWidget(card)

    def _card(
        self,
        title: str,
        description: str,
        icon: str,
    ) -> tuple[QWidget, QVBoxLayout]:
        card = QWidget()
        card.setObjectName("settingCard")
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(20, 18, 20, 19)
        outer.setSpacing(13)
        heading = QWidget()
        heading_layout = QHBoxLayout(heading)
        heading_layout.setDirection(QHBoxLayout.Direction.RightToLeft)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.setSpacing(12)
        copy = QWidget()
        copy_layout = QVBoxLayout(copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(4)
        card_title = QLabel(title)
        card_title.setObjectName("cardTitle")
        card_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        card_description = QLabel(description)
        card_description.setObjectName("cardDescription")
        card_description.setWordWrap(True)
        card_description.setAlignment(Qt.AlignmentFlag.AlignRight)
        copy_layout.addWidget(card_title)
        copy_layout.addWidget(card_description)
        icon_label = QLabel(icon)
        icon_label.setObjectName("cardIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(32, 32)
        heading_layout.addWidget(copy, 1)
        heading_layout.addWidget(icon_label)
        outer.addWidget(heading)
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(12)
        outer.addLayout(content)
        return card, content

    def _grid(self, layout: QVBoxLayout) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(13)
        grid.setVerticalSpacing(13)
        layout.addLayout(grid)
        return grid

    def _field(
        self,
        layout: QVBoxLayout,
        label: str,
        control: QWidget,
        hint: str = "",
    ) -> None:
        field = QWidget()
        field.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        field_layout = QVBoxLayout(field)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(6)
        title = QLabel(label)
        title.setObjectName("fieldLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        field_layout.addWidget(title)
        field_layout.addWidget(control)
        if hint:
            help_text = QLabel(hint)
            help_text.setObjectName("fieldHint")
            help_text.setWordWrap(True)
            help_text.setAlignment(Qt.AlignmentFlag.AlignRight)
            field_layout.addWidget(help_text)
        layout.addWidget(field)

    def _setting_row(
        self,
        layout: QVBoxLayout,
        title: str,
        description: str,
        checked: bool,
        key: str,
    ) -> ToggleSwitch:
        row = QWidget()
        row.setObjectName("settingRow")
        row.setProperty("first", layout.count() == 0)
        row.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        row.setMinimumHeight(56)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 5, 0, 5)
        row_layout.setSpacing(14)
        copy = QWidget()
        copy_layout = QVBoxLayout(copy)
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(2)
        title_label = QLabel(title)
        title_label.setObjectName("settingRowTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        description_label = QLabel(description)
        description_label.setObjectName("settingRowHelp")
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        copy_layout.addWidget(title_label)
        copy_layout.addWidget(description_label)
        toggle = ToggleSwitch(title, row)
        toggle.setObjectName(key)
        toggle.setChecked(checked)
        row_layout.addWidget(copy, 1)
        row_layout.addWidget(toggle)
        layout.addWidget(row)
        self._controls[key] = toggle
        return toggle

    def _readonly_value(self, value: str) -> QLabel:
        label = QLabel(value)
        label.setObjectName("readonlyValue")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    def _build_gemini_page(self, layout: QVBoxLayout) -> None:
        grid = self._grid(layout)
        connection_card, connection = self._card(
            "اتصال Gemini",
            "شوية ذكاء يساعدك وقت ما تحتاجه.",
            "✳",
        )
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setObjectName("apiKeyEdit")
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.api_key_edit.setPlaceholderText("أدخل مفتاح Google AI Studio")
        self.api_key_edit.setMinimumWidth(0)
        self.show_key_button = QPushButton("إظهار")
        self.show_key_button.setObjectName("quietButton")
        self.show_key_button.clicked.connect(self._toggle_key_visibility)
        self.delete_key_button = QPushButton("حذف المفتاح")
        self.delete_key_button.setObjectName("quietButton")
        self.delete_key_button.clicked.connect(self._mark_key_for_deletion)
        self.key_status = QLabel("")
        key_row = QHBoxLayout()
        key_row.setDirection(QHBoxLayout.Direction.LeftToRight)
        key_row.setContentsMargins(0, 0, 0, 0)
        key_row.addWidget(self.api_key_edit, 1)
        key_row.addWidget(self.show_key_button)
        key_row.addWidget(self.delete_key_button)
        key_container = QWidget()
        key_container.setLayout(key_row)
        self._field(connection, "مفتاح Gemini API", key_container)
        self.key_status.setObjectName("fieldHint")
        connection.addWidget(self.key_status)
        self.connection_status = QLabel("")
        self.connection_status.setWordWrap(True)
        self.connection_status.setObjectName("fieldHint")
        connection.addWidget(self.connection_status)
        self.api_quota_warning = QLabel(
            "وصل مفتاح Gemini إلى حد الاستخدام أو الحصة. سيظهر هذا التحذير هنا حتى ينجح طلب API."
        )
        self.api_quota_warning.setObjectName("apiQuotaWarning")
        self.api_quota_warning.setWordWrap(True)
        self.api_quota_warning.setStyleSheet("color: #ffbf69;")
        self.api_quota_warning.hide()
        connection.addWidget(self.api_quota_warning)

        model_row = QHBoxLayout()
        model_row.setDirection(QHBoxLayout.Direction.LeftToRight)
        model_row.setContentsMargins(0, 0, 0, 0)
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.addItem("gemini-3.8-flash", "gemini-3.8-flash")
        self.models_refresh_button = QPushButton("قراءة النماذج")
        self.models_refresh_button.clicked.connect(self._load_available_models)
        self.test_button = QPushButton("اختبار الاتصال")
        self.test_button.setObjectName("testConnectionButton")
        self.test_button.clicked.connect(self._test_connection)
        model_row.addWidget(self.model_combo, 1)
        model_row.addWidget(self.models_refresh_button)
        model_row.addWidget(self.test_button)
        model_container = QWidget()
        model_container.setLayout(model_row)
        self._field(
            connection,
            "النموذج",
            model_container,
            "اختار النموذج المستخدم للمحادثة والأدوات.",
        )
        self.models_status = QLabel("")
        self.models_status.setObjectName("fieldHint")
        self.models_status.setWordWrap(True)
        connection.addWidget(self.models_status)

        self.language_combo = QComboBox()
        self.language_combo.addItem("تلقائي — نفس لغة كلامي", "auto")
        self.language_combo.addItem("العربية", "ar")
        self.language_combo.addItem("الإنجليزية", "en")
        self._field(connection, "لغة الرد", self.language_combo)
        grid.addWidget(connection_card, 0, 0)

        response_card, response = self._card(
            "طريقة كلام Ember",
            "خلي الردود مفيدة ولطيفة ومناسبة لفقاعة الكلام.",
            "◌",
        )
        self.same_language = self._setting_row(
            response,
            "الرد بنفس اللغة",
            "يفهم المصري والإنجليزي ويرد باللغة اللي استخدمتها.",
            self.settings.same_language,
            "same_language",
        )
        self.concise_replies = self._setting_row(
            response,
            "ردود مختصرة",
            "الرد يناسب فقاعة الكلام الصغيرة على سطح المكتب.",
            self.settings.concise_replies,
            "concise_replies",
        )
        grid.addWidget(response_card, 0, 1)
        self._note_card(
            layout,
            "معاينة آمنة للمفتاح: يُحفظ في سلسلة مفاتيح النظام، ولا يُكتب في ملف الإعدادات.",
        )

    def _build_voice_page(self, layout: QVBoxLayout) -> None:
        grid = self._grid(layout)
        voice_card, voice = self._card(
            "الردود الصوتية",
            "اختار صوت Ember لما يرد عليك بصوت مسموع.",
            "◖",
        )
        self.speak_answers = self._setting_row(
            voice,
            "نطق الردود",
            "قراءة الردود بصوت مسموع عند تفعيل الصوت.",
            self.settings.speak_answers,
            "speak_answers",
        )
        self.voice_combo = QComboBox()
        for voice_name, label in (
            ("Kore", "Kore · واضح ودافئ"),
            ("Puck", "Puck · مرح وحيوي"),
            ("Charon", "Charon · هادئ ومتزن"),
            ("Fenrir", "Fenrir"),
            ("Aoede", "Aoede"),
        ):
            self.voice_combo.addItem(label, voice_name)
        self._field(voice, "الصوت", self.voice_combo)
        self.voice_volume = self._slider(0, 100, "voice_volume")
        self._field(voice, "مستوى صوت الرد", self.voice_volume)
        self.preview_voice_button = QPushButton("معاينة الصوت")
        self.preview_voice_button.setEnabled(False)
        self.preview_voice_button.setToolTip(
            "إخراج الصوت غير متاح في إصدار سطح المكتب الحالي."
        )
        voice.addWidget(self.preview_voice_button)
        grid.addWidget(voice_card, 0, 0)

        sounds_card, sounds = self._card(
            "أصوات صغيرة",
            "أصوات قصيرة أصلية للحركة وردود الفعل.",
            "∿",
        )
        self.sounds_enabled = self._setting_row(
            sounds,
            "أصوات الشخصية",
            "نغمة قصيرة للرد، وأخرى للصحو والنوم.",
            self.settings.sounds_enabled,
            "sounds_enabled",
        )
        self.sound_volume = self._slider(0, 100, "sound_volume")
        self._field(sounds, "مستوى المؤثرات", self.sound_volume)
        grid.addWidget(sounds_card, 0, 1)

        language_card, language = self._card(
            "اللغة والخصوصية",
            "إعدادات الواجهة والتحدث في Ember.",
            "文",
        )
        self._field(
            language,
            "لغة الواجهة",
            self._readonly_value("العربية"),
        )
        self._field(
            language,
            "لغة التحدث",
            self._readonly_value("اكتشاف تلقائي · مصري وإنجليزي"),
        )
        self.wake_word_enabled = self._setting_row(
            language,
            "التنبيه الصوتي",
            "استماع محلي لكلمة Ember لفتح التسجيل تلقائيًا.",
            self.settings.wake_word_enabled,
            "wake_word_enabled",
        )
        self._add_note(
            language,
            "لا يُرسل صوت الاستعداد إلى الإنترنت. بعد قول Ember يبدأ تسجيل سؤالك، ثم يُرسل إلى Google عند انتهاء كلامك.",
        )
        grid.addWidget(language_card, 1, 0, 1, 2)
        self._add_note(
            voice,
            "نطق الردود الصوتية غير متاح بعد؛ يظل الرد النصي والمؤثرات المحلية متاحين حسب إعداداتك.",
        )

    def _build_behavior_page(self, layout: QVBoxLayout) -> None:
        grid = self._grid(layout)
        walking_card, walking = self._card(
            "المشي فوق النوافذ",
            "خلّي Ember يتمشى فوق الحافة العلوية للنوافذ المفتوحة.",
            "⌑",
        )
        self.stand_on_windows = self._setting_row(
            walking,
            "الوقوف على النوافذ المفتوحة",
            "يمشي فوق النوافذ ويقع عند تحريكها أو إغلاقها.",
            self.settings.stand_on_windows,
            "stand_on_windows",
        )
        grid.addWidget(walking_card, 0, 0)

        movement_card, movement = self._card(
            "الحركة والحجم",
            "اضبط الحركة بما يناسب شاشتك.",
            "↔",
        )
        self.walking_speed = self._slider(25, 200, "walking_speed", "%")
        self._field(movement, "سرعة المشي", self.walking_speed)
        self.display_scale = self._slider(
            35, 150, "display_scale", "%", scale=True
        )
        self._field(movement, "حجم الشخصية", self.display_scale)
        grid.addWidget(movement_card, 0, 1)

        rest_card, rest = self._card(
            "روتين النوم",
            "Ember بياخد راحة بعد فترة هدوء.",
            "☾",
        )
        sleep_control = self._slider(1, 180, "sleep_delay_minutes", " دقيقة")
        self.sleep_delay = sleep_control.findChild(QSlider)
        self._field(rest, "النوم بعد", sleep_control)
        self.sleep_corner = QComboBox()
        self.sleep_corner.addItem("أعلى الشاشة — مكان عشوائي", "top-random")
        self._field(rest, "ركن النوم المفضل", self.sleep_corner)
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItem("الشاشة الرئيسية", "primary")
        for screen in QApplication.screens():
            name = screen.name() or f"شاشة {self.monitor_combo.count()}"
            if name != "primary":
                self.monitor_combo.addItem(name, name)
        self._field(rest, "الشاشة", self.monitor_combo)
        self._add_note(
            rest,
            "Ember يصحى لما تقرّب بالماوس أو تضغط عليه. اختيار ركن النوم غير متاح بعد.",
        )
        grid.addWidget(rest_card, 1, 0, 1, 2)

    def _build_memory_page(self, layout: QVBoxLayout) -> None:
        card, card_layout = self._card(
            "ذكريات Ember",
            "تُحفظ على هذا الجهاز فقط، وتُرسل إلى Gemini فقط عندما يحتاجها الرد.",
            "◇",
        )
        self.memory_list = QListWidget()
        self.memory_list.setObjectName("memoryList")
        self.memory_list.setMinimumHeight(240)
        self.memory_list.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        card_layout.addWidget(self.memory_list)
        self.memory_status = QLabel()
        self.memory_status.setWordWrap(True)
        self.memory_status.setStyleSheet("color:#aaa99f;")
        card_layout.addWidget(self.memory_status)
        actions = QHBoxLayout()
        actions.addStretch(1)
        refresh = QPushButton("تحديث")
        refresh.clicked.connect(self._refresh_memories)
        self.delete_memory_button = QPushButton("حذف المحددة")
        self.delete_memory_button.clicked.connect(self._delete_selected_memory)
        actions.addWidget(refresh)
        actions.addWidget(self.delete_memory_button)
        card_layout.addLayout(actions)
        layout.addWidget(card)
        self._refresh_memories()

    def _refresh_memories(self) -> None:
        self.memory_list.clear()
        try:
            memories = self.memory_store.list_all()
        except (OSError, RuntimeError, sqlite3.Error) as error:
            self.memory_status.setText(f"تعذر قراءة الذاكرة: {error}")
            self.memory_status.setStyleSheet("color:#ff9f94;")
            self.delete_memory_button.setEnabled(False)
            return
        for memory_id, fact in memories:
            item = QListWidgetItem(fact)
            item.setData(Qt.ItemDataRole.UserRole, memory_id)
            self.memory_list.addItem(item)
        self.memory_status.setText(
            "لا توجد ذكريات محفوظة بعد."
            if not memories
            else f"عدد الذكريات المحفوظة: {len(memories)}."
        )
        self.memory_status.setStyleSheet("color:#aaa99f;")
        self.delete_memory_button.setEnabled(bool(memories))

    def _delete_selected_memory(self) -> None:
        item = self.memory_list.currentItem()
        if item is None:
            return
        answer = QMessageBox.question(
            self,
            "حذف ذكرى",
            "هل تريد حذف هذه الذكرى نهائيًا من هذا الجهاز؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        memory_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            removed = self.memory_store.remove(int(memory_id))
        except (OSError, RuntimeError, ValueError, sqlite3.Error) as error:
            self.memory_status.setText(f"تعذر حذف الذكرى: {error}")
            self.memory_status.setStyleSheet("color:#ff9f94;")
            return
        self._refresh_memories()
        if not removed:
            self.memory_status.setText("لم تعد هذه الذكرى موجودة.")

    def _build_permissions_page(self, layout: QVBoxLayout) -> None:
        grid = self._grid(layout)
        tools_card, tools_layout = self._card(
            "مستويات الصلاحيات",
            "الصلاحية",
            "◇",
        )
        self.permission_combos: dict[str, QComboBox] = {}
        self._permission_groups: list[tuple[QComboBox, tuple[str, ...]]] = []
        permission_groups = (
            (("open_app", "open_url"), "فتح تطبيق أو رابط", "تشغيل تطبيقات وفتح روابط"),
            (("list_windows", "close_window"), "إدارة النوافذ", "عرض عناوين النوافذ وإغلاق نافذة محددة بعد التحقق من اختفاء عنوانها"),
            (("set_volume", "media_control"), "الصوت والوسائط", "ضبط مستوى الصوت وتشغيل الوسائط"),
            (("repair_microphone",), "الميكروفون", "فحص مدخل الميكروفون وإصلاح كتمه أو مستوى الإدخال الصامت"),
            (("open_bluetooth_settings", "open_system_settings", "set_bluetooth_power"), "النظام وBluetooth", "فتح صفحات إعدادات محددة والتحقق من تشغيل Bluetooth أو إيقافه"),
            (("close_active_window",), "إغلاق النافذة", "إرسال طلب إغلاق للنافذة النشطة؛ لا يمكن تأكيد إغلاق التطبيقات الأخرى"),
            (("type_text", "press_keys", "click", "scroll"), "الكتابة والماوس", "إدخال النص والنقر والتمرير عند طلبك، بما في ذلك التحكم في إعدادات النظام"),
            (("read_clipboard", "write_clipboard"), "الوصول إلى الحافظة", "قراءة محتوى الحافظة أو الكتابة إليها"),
            (("create_file", "read_file"), "ملفات المجلدات المسموحة", "إنشاء أو قراءة الملفات بعد موافقتك"),
            (("run_shell_command", "run_terminal_command", "close_ember_terminal"), "أوامر الطرفية", "تشغيل أوامرك المحددة في نافذة Terminal مرئية، وفقط إغلاق نافذة Terminal التي فتحها Ember"),
            (("take_screenshot_and_describe",), "لقطات الشاشة", "لقطة عند الطلب أو مشاهدة مؤقتة بعد تفعيل الكاميرا"),
            (("remember_this",), "الذاكرة", "حفظ أو استرجاع الذكريات المحلية بعد طلبك"),
        )
        for names, title, description in permission_groups:
            row = QWidget()
            row.setObjectName("toolRow")
            row.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 7, 0, 7)
            row_layout.setSpacing(18)
            copy = QWidget()
            copy_layout = QVBoxLayout(copy)
            copy_layout.setContentsMargins(0, 0, 0, 0)
            copy_layout.setSpacing(2)
            tool_title = QLabel(title)
            tool_title.setObjectName("settingRowTitle")
            tool_help = QLabel(description)
            tool_help.setObjectName("settingRowHelp")
            tool_help.setWordWrap(True)
            copy_layout.addWidget(tool_title)
            copy_layout.addWidget(tool_help)
            combo = QComboBox()
            combo.addItem("تلقائي", "auto")
            combo.addItem("اسألني أولًا", "ask")
            combo.addItem("معطّل", "disabled")
            combo.setMinimumWidth(145)
            row_layout.addWidget(copy, 1)
            row_layout.addWidget(combo)
            tools_layout.addWidget(row)
            self._permission_groups.append((combo, names))
            for name in names:
                self.permission_combos[name] = combo
        grid.addWidget(tools_card, 0, 0, 1, 2)

        folders_card, folders_layout = self._card(
            "المجلدات المسموحة",
            "عمليات الملفات تفضل داخل المجلدات دي.",
            "⌂",
        )
        self.folders_list = QListWidget()
        self.folders_list.setObjectName("allowedFolders")
        self.folders_list.setMinimumHeight(104)
        self.folders_list.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        folder_buttons = QVBoxLayout()
        add_folder = QPushButton("إضافة مجلد")
        add_folder.clicked.connect(self._add_folder)
        remove_folder = QPushButton("إزالة المحدد")
        remove_folder.clicked.connect(self._remove_folder)
        folder_buttons.addWidget(add_folder)
        folder_buttons.addWidget(remove_folder)
        folder_buttons.addStretch(1)
        folders_row = QHBoxLayout()
        folders_row.addWidget(self.folders_list, 1)
        folders_row.addLayout(folder_buttons)
        folders_container = QWidget()
        folders_container.setLayout(folders_row)
        folders_layout.addWidget(folders_container)
        grid.addWidget(folders_card, 1, 0)

        forbidden_card, forbidden_layout = self._card(
            "ممنوع دائمًا",
            "وسائل حماية لا يتجاوزها أي تأكيد.",
            "⊘",
        )
        forbidden = QLabel(
            "أوامر مثل sudo وrm -rf وتهيئة الأقراص وملفات النظام وبيانات الآخرين "
            "وخانات كلمات المرور والوصول إلى مخزن المفاتيح تظل محظورة."
        )
        forbidden.setWordWrap(True)
        forbidden.setObjectName("forbiddenText")
        forbidden_layout.addWidget(forbidden)
        grid.addWidget(forbidden_card, 1, 1)

        self._note_card(
            layout,
            "عندما تطلب من Ember النظر إلى شاشتك، تُرسل لقطة الشاشة إلى Google لتحليلها؛ لا تُلتقط في الخلفية.",
        )
        grid.setRowStretch(2, 0)

    def _build_shortcuts_page(self, layout: QVBoxLayout) -> None:
        grid = self._grid(layout)
        hotkeys_card, hotkeys = self._card(
            "الاختصارات",
            "دخول سريع، وخروج أسرع.",
            "⌘",
        )
        self.emergency_hotkey = QKeySequenceEdit()
        self.emergency_hotkey.setObjectName("emergencyHotkey")
        self.emergency_hotkey.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._controls["emergency_hotkey"] = self.emergency_hotkey
        self._field(
            hotkeys,
            "الإيقاف الطارئ",
            self.emergency_hotkey,
            "يلغي الإجراء الحالي ويوقف كل الإدخال.",
        )
        self.ptt_hotkey = QKeySequenceEdit()
        self.ptt_hotkey.setObjectName("pushToTalkHotkey")
        self.ptt_hotkey.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._controls["push_to_talk_hotkey"] = self.ptt_hotkey
        self._field(
            hotkeys,
            "زر التحدث",
            self.ptt_hotkey,
            "اختياري كبديل للضغط المطوّل بزر الماوس اليمين.",
        )
        grid.addWidget(hotkeys_card, 0, 0)

        startup_card, startup = self._card(
            "عند تشغيل سطح المكتب",
            "اختار موعد ظهور Ember في جلستك.",
            "◉",
        )
        self.autostart = self._setting_row(
            startup,
            "تشغيل Ember عند تسجيل الدخول",
            "فتح Ember تلقائيًا عند تسجيل دخولك.",
            self.settings.autostart,
            "autostart",
        )
        grid.addWidget(startup_card, 0, 1)

        self._note_card(
            layout,
            "اختصار الإيقاف الطارئ متاح حتى أثناء استماع Ember أو تفكيره، ويلغي الإجراء الحالي ويوقف كل الإدخال. الاختصارات العامة غير مفعّلة بعد.",
        )

    def _slider(
        self,
        minimum: int,
        maximum: int,
        key: str,
        suffix: str = "%",
        scale: bool = False,
        register: bool = True,
    ) -> QWidget:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setObjectName(key)
        value = QLabel("")
        value.setObjectName("rangeValue")
        value.setMinimumWidth(46)
        value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        def update_label(raw_value: int) -> None:
            value.setText(f"{raw_value}{suffix}")

        slider.valueChanged.connect(update_label)
        row = QHBoxLayout()
        row.setDirection(QHBoxLayout.Direction.LeftToRight)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(value)
        row.addWidget(slider, 1)
        container = QWidget()
        container.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        container.setLayout(row)
        if register:
            self._controls[key] = (slider, scale)
            self._controls[f"{key}_label"] = value
        return container

    def _load_controls(self, value: AppSettings) -> None:
        model_index = self.model_combo.findData(value.model)
        if model_index < 0:
            self.model_combo.addItem(f"{value.model} — محفوظ", value.model)
            model_index = self.model_combo.count() - 1
        self.model_combo.setCurrentIndex(model_index)
        self.language_combo.setCurrentIndex(
            max(0, self.language_combo.findData(value.response_language))
        )
        for key, control in self._controls.items():
            if key.endswith("_label"):
                continue
            if isinstance(control, QCheckBox):
                control.setChecked(bool(getattr(value, key)))
            elif isinstance(control, QSpinBox):
                control.setValue(int(getattr(value, key)))
            elif isinstance(control, QKeySequenceEdit):
                sequence = getattr(value, key)
                control.setKeySequence(QKeySequence(sequence))
            elif isinstance(control, tuple) and isinstance(control[0], QSlider):
                slider, is_scale = control
                raw_value = getattr(value, key)
                slider.setValue(
                    round(float(raw_value) * 100) if is_scale else int(raw_value)
                )
        self.voice_combo.setCurrentIndex(
            max(0, self.voice_combo.findData(value.voice_name))
        )
        self.sleep_corner.setCurrentIndex(
            max(0, self.sleep_corner.findData(value.sleep_corner))
        )
        monitor_index = self.monitor_combo.findData(value.monitor)
        self.monitor_combo.setCurrentIndex(max(0, monitor_index))
        self.folders_list.clear()
        self.folders_list.addItems(list(value.allowed_folders))
        for combo, names in self._permission_groups:
            tiers = {value.tool_tiers.get(name, "ask") for name in names}
            selected = next(iter(tiers)) if len(tiers) == 1 else "mixed"
            if selected == "mixed" and combo.findData("mixed") < 0:
                combo.addItem("إعدادات مختلفة", "mixed")
            combo.setCurrentIndex(max(0, combo.findData(selected)))
        self._refresh_key_status()

    def _collect_settings(self) -> AppSettings:
        values: dict[str, object] = {}
        for key, control in self._controls.items():
            if key.endswith("_label"):
                continue
            if isinstance(control, QCheckBox):
                values[key] = control.isChecked()
            elif isinstance(control, QSpinBox):
                values[key] = control.value()
            elif isinstance(control, QKeySequenceEdit):
                values[key] = control.keySequence().toString(
                    QKeySequence.SequenceFormat.PortableText
                )
            elif isinstance(control, tuple) and isinstance(control[0], QSlider):
                slider, is_scale = control
                raw_value = slider.value()
                values[key] = raw_value / 100 if is_scale else raw_value

        tool_tiers = dict(self.settings.tool_tiers)
        for combo, names in self._permission_groups:
            selected_tier = str(combo.currentData())
            if selected_tier != "mixed":
                for name in names:
                    tool_tiers[name] = selected_tier

        values.update(
            model=str(self.model_combo.currentData()),
            response_language=str(self.language_combo.currentData()),
            voice_name=str(self.voice_combo.currentData()),
            sleep_corner=str(self.sleep_corner.currentData()),
            monitor=str(self.monitor_combo.currentData()),
            allowed_folders=tuple(
                self.folders_list.item(index).text()
                for index in range(self.folders_list.count())
            ),
            tool_tiers=tool_tiers,
        )
        return AppSettings(**values)

    def _toggle_key_visibility(self) -> None:
        visible = self.api_key_edit.echoMode() == QLineEdit.EchoMode.Password
        self.api_key_edit.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )
        self.show_key_button.setText("إخفاء" if visible else "إظهار")

    def _mark_key_for_deletion(self) -> None:
        self._delete_api_key = True
        self.api_key_edit.clear()
        self.api_key_edit.setPlaceholderText("سيُحذف المفتاح عند الحفظ")
        self.key_status.setText("سيُحذف المفتاح من سلسلة مفاتيح النظام عند الحفظ.")

    def _test_connection(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        try:
            api_key = self.api_key_edit.text().strip()
            if not api_key:
                api_key = self.key_store.get_key() or ""
        except SecretStorageError as exc:
            self._set_connection_status(str(exc), error=True)
            return
        if not api_key:
            self._set_connection_status(
                "أدخل مفتاح Google AI Studio أو احفظه أولًا.", error=True
            )
            return
        self.connection_status.setText("جارٍ اختبار الاتصال…")
        self.connection_status.setStyleSheet("color: #aaa99f;")
        self.test_button.setEnabled(False)
        self._worker = ConnectionWorker(
            api_key,
            str(self.model_combo.currentData()),
            self.connection_probe,
        )
        self._worker.result_ready.connect(self._on_connection_result)
        self._worker.finished.connect(self._on_connection_finished)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_connection_finished(self) -> None:
        self._worker = None

    def _on_connection_result(self, success: bool, message: str) -> None:
        self.test_button.setEnabled(True)
        self._set_connection_status(message, error=not success)

    def _set_connection_status(self, message: str, error: bool) -> None:
        self.connection_status.setText(message)
        color = "#ff9f94" if error else "#9bd3a5"
        self.connection_status.setStyleSheet(f"color: {color};")

    def set_api_quota_warning(self, visible: bool) -> None:
        self.api_quota_warning.setVisible(visible)

    def _save(self) -> None:
        value = self._collect_settings()
        entered_key = self.api_key_edit.text().strip()
        deleting_key = self._delete_api_key
        try:
            if self._delete_api_key:
                self.key_store.delete_key()
            if entered_key:
                self.key_store.set_key(entered_key)
            self.autostart_writer(value.autostart)
            self.store.save(value)
        except SecretStorageError as exc:
            self.key_status.setText(str(exc))
            self.key_status.setStyleSheet("color: #ff9f94;")
            QMessageBox.critical(self, "تعذر حفظ الإعدادات", str(exc))
            return
        except OSError as exc:
            QMessageBox.critical(self, "تعذر حفظ الإعدادات", str(exc))
            return
        self.settings = value
        self._delete_api_key = False
        if deleting_key and not entered_key:
            self.api_key_edit.clear()
            self.api_key_edit.setPlaceholderText("أدخل مفتاح Google AI Studio")
        self._refresh_key_status()
        self.save_status.setText("تم حفظ الإعدادات.")
        self.settings_applied.emit(value)

    def _reset_defaults(self) -> None:
        answer = QMessageBox.question(
            self,
            "إعادة الإعدادات الافتراضية",
            "سيتم إعادة تفضيلات Ember وحالة التشغيل التلقائي. "
            "مفتاح Gemini المحفوظ لن يُحذف. هل تريد المتابعة؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.autostart_writer(False)
            self.store.reset()
        except OSError as exc:
            QMessageBox.critical(self, "تعذر إعادة الإعدادات", str(exc))
            return
        self.settings = AppSettings()
        self._delete_api_key = False
        self.api_key_edit.clear()
        self._load_controls(self.settings)
        self.settings_applied.emit(self.settings)
        self.save_status.setText("تمت إعادة الإعدادات الافتراضية.")

    def _add_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "اختر مجلدًا مسموحًا", str(Path.home())
        )
        if path and not any(
            self.folders_list.item(i).text() == path
            for i in range(self.folders_list.count())
        ):
            self.folders_list.addItem(path)

    def _remove_folder(self) -> None:
        row = self.folders_list.currentRow()
        if row >= 0:
            self.folders_list.takeItem(row)

    def _get_stored_key(self) -> str | None:
        try:
            return self.key_store.get_key()
        except SecretStorageError as exc:
            self.key_status.setText(
                f"تعذر الوصول إلى سلسلة مفاتيح النظام: {exc}"
            )
            self.key_status.setStyleSheet("color: #9b382d;")
            return None

    def _refresh_key_status(self) -> None:
        stored_key = self._get_stored_key()
        if stored_key:
            if not self.api_key_edit.text() and not self._delete_api_key:
                self.api_key_edit.setText(stored_key)
            self.key_status.setText("المفتاح محفوظ في سلسلة مفاتيح النظام.")
            self.key_status.setStyleSheet("color: #9bd3a5;")
        elif not self.key_status.text().startswith("تعذر الوصول"):
            self.key_status.setText("لا يوجد مفتاح محفوظ.")
            self.key_status.setStyleSheet("color: #aaa99f;")

    def _switch_page(self, index: int) -> None:
        if index < 0 or index >= self.pages.count():
            return
        if hasattr(self, "settings_breadcrumb"):
            self.settings_breadcrumb.setText(
                f"التفضيلات  /  {PAGES[index][1]}"
            )
        self.pages.setCurrentIndex(index)
        effect = self._page_effects[index]
        if self._page_animation is not None:
            self._page_animation.stop()
        effect.setOpacity(0.78)
        animation = self._page_animation
        if animation is None:
            animation = QPropertyAnimation(effect, b"opacity", self)
            self._page_animation = animation
        else:
            animation.setTargetObject(effect)
        animation.setDuration(150)
        animation.setStartValue(0.78)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

    def _open_settings_page(self, page: str) -> None:
        index = next(index for index, (key, _title, _subtitle) in enumerate(PAGES) if key == page)
        self.screen_stack.setCurrentIndex(1)
        self.navigation.setCurrentRow(index)
        self._switch_page(index)
        if page == "gemini" and not self._models_loaded:
            self._load_available_models()
        elif page == "memory":
            self._refresh_memories()

    def _load_available_models(self) -> None:
        if self._models_worker is not None and self._models_worker.isRunning():
            return
        api_key = self.api_key_edit.text().strip()
        try:
            if not api_key:
                api_key = self.key_store.get_key() or ""
        except SecretStorageError as exc:
            self.models_status.setText(str(exc))
            self.models_status.setStyleSheet("color: #ff9f94;")
            return
        if not api_key:
            self.models_status.setText("أضف مفتاح Gemini لتحميل النماذج المتاحة.")
            self.models_status.setStyleSheet("color: #aaa99f;")
            return

        self.models_refresh_button.setEnabled(False)
        self.models_status.setText("جارٍ تحميل كل نماذج توليد المحتوى…")
        self.models_status.setStyleSheet("color: #aaa99f;")
        self._models_worker = ModelListWorker(api_key, self.model_list_probe)
        self._models_worker.models_ready.connect(self._on_models_loaded)
        self._models_worker.request_failed.connect(self._on_models_failed)
        self._models_worker.finished.connect(self._on_models_finished)
        self._models_worker.finished.connect(self._models_worker.deleteLater)
        self._models_worker.start()

    def _on_models_loaded(self, models: list[tuple[str, str]]) -> None:
        selected_model = str(self.model_combo.currentData() or self.settings.model)
        self.model_combo.clear()
        for model_id, display_name in models:
            self.model_combo.addItem(f"{display_name} — {model_id}", model_id)
        if self.model_combo.findData(selected_model) < 0:
            self.model_combo.addItem(
                f"{selected_model} — غير متاح في القائمة",
                selected_model,
            )
        self.model_combo.setCurrentIndex(self.model_combo.findData(selected_model))
        self._models_loaded = True
        self.models_status.setText(f"تم تحميل {len(models)} نموذجًا يدعم توليد الردود.")
        self.models_status.setStyleSheet("color: #9bd3a5;")

    def _on_models_failed(self, message: str) -> None:
        self.models_status.setText(f"تعذر تحميل النماذج: {message}")
        self.models_status.setStyleSheet("color: #ff9f94;")

    def _on_models_finished(self) -> None:
        self.models_refresh_button.setEnabled(True)
        self._models_worker = None

    def _show_home(self) -> None:
        self.screen_stack.setCurrentIndex(0)

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
