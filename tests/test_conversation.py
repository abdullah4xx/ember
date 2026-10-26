from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import wave

from PySide6.QtCore import QEventLoop, QIODevice, QObject, QPoint, QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QMouseEvent, QTextCursor
from PySide6.QtMultimedia import QAudio, QAudioFormat
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from ember.conversation import (
    AskBubble,
    ChimePlayer,
    ConversationWindow,
    GeminiReplyWorker,
    MicrophoneCapture,
    ScreenWatchWorker,
    detect_conversation_language,
    pcm_to_wav,
    response_language,
)
import ember.conversation as conversation_module
from ember.sounds import SOUND_CUES, render_sound


def test_language_detection_prefers_the_dominant_script() -> None:
    assert detect_conversation_language("مرحبا، كيف الحال؟") == "ar"
    assert detect_conversation_language("Hello, how are you?") == "en"
    assert response_language("What is this?", "ar") == "ar"
    assert response_language("مرحبا", "auto") == "ar"
    assert response_language("Hello", "ar", same_language=True) == "en"
    assert response_language("Hello", "auto", same_language=False) == "ar"


def test_pcm_conversion_creates_mono_16_bit_wav() -> None:
    audio = pcm_to_wav(b"\x01\x00" * 1600, 16_000, 1)

    with wave.open(BytesIO(audio), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16_000
        assert wav_file.getnframes() == 1600


def test_chime_player_uses_bundled_chimes_and_generated_sound_palette(
    qapp, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(
        conversation_module.QStandardPaths,
        "writableLocation",
        lambda _location: str(tmp_path),
    )
    player = ChimePlayer()

    assert {
        name: Path(effect.source().toLocalFile()).name
        for name, effect in player._effects.items()
        if name in ChimePlayer.SOUND_FILES
    } == ChimePlayer.SOUND_FILES
    assert set(SOUND_CUES).issubset(player._effects)
    assert len(SOUND_CUES) > 15
    assert all(
        (tmp_path / "sounds" / f"{name}.wav").is_file()
        for name in SOUND_CUES
    )
    assert all(
        (Path(__file__).parents[1] / "src" / "ember" / "assets" / filename).is_file()
        for filename in ChimePlayer.SOUND_FILES.values()
    )


def test_procedural_sound_cues_are_distinct_and_valid_wav_files() -> None:
    sounds = {
        name: render_sound(name)
        for name in SOUND_CUES
    }

    assert len(set(sounds.values())) == len(sounds)
    assert all(data.startswith(b"RIFF") and data[8:12] == b"WAVE" for data in sounds.values())


def test_gemini_worker_sends_history_and_returns_text() -> None:
    requests = []

    class FakeModels:
        def generate_content(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(text="A clear reply")

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    worker = GeminiReplyWorker(
        "test-key",
        "test-model",
        "Follow up",
        "en",
        history=(("user", "Earlier question"), ("assistant", "Earlier answer")),
        concise_replies=False,
        client_factory=FakeClient,
    )
    replies = []
    errors = []
    worker.reply_ready.connect(
        lambda answer, _auto_language: replies.append(answer)
    )
    worker.request_failed.connect(errors.append)

    worker.run()

    assert not errors
    assert replies == ["A clear reply"]
    assert requests[0]["model"] == "test-model"
    request_content = "\n".join(requests[0]["contents"])
    assert "Earlier question" in request_content
    assert "Earlier answer" in request_content
    assert "Follow up" in request_content
    assert "Give a useful explanation with enough detail." in request_content
    assert requests[0]["config"].tool_config.function_calling_config.mode == "AUTO"
    function_names = {
        declaration.name
        for tool in requests[0]["config"].tools
        for declaration in tool.function_declarations
    }
    assert {
        "repair_microphone",
        "set_bluetooth_power",
        "list_windows",
        "close_window",
    }.issubset(function_names)
    instruction = requests[0]["config"].system_instruction
    assert "repair_microphone before giving general advice" in instruction
    assert "Never claim closure unless" in instruction


def test_gemini_worker_hands_desktop_function_calls_to_the_gui() -> None:
    requests = []
    function_call = conversation_module.types.FunctionCall(
        name="open_app", args={"app_name": "Chrome"}
    )
    model_turn = conversation_module.types.Content(
        role="model",
        parts=[conversation_module.types.Part(function_call=function_call)],
    )

    class FakeModels:
        def generate_content(self, **kwargs):
            requests.append(kwargs)
            if len(requests) == 1:
                return SimpleNamespace(
                    text=None,
                    function_calls=[function_call],
                    candidates=[SimpleNamespace(content=model_turn)],
                )
            return SimpleNamespace(text="تم فتح Chrome.", function_calls=None)

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    worker = GeminiReplyWorker(
        "test-key",
        "test-model",
        "افتح كروم",
        "ar",
        client_factory=FakeClient,
    )
    replies = []
    errors = []
    calls = []
    worker.reply_ready.connect(lambda answer, _auto: replies.append(answer))
    worker.request_failed.connect(errors.append)

    def resolve_tool(request_id, name, args):
        calls.append((name, args))
        worker.resolve_tool_call(request_id, {"text": "تم فتح Chrome."})

    worker.tool_requested.connect(resolve_tool)
    worker.run()

    assert not errors
    assert replies == ["تم فتح Chrome."]
    assert calls == [("open_app", {"app_name": "Chrome"})]
    assert len(requests) == 2
    assert requests[1]["contents"][-1].role == "user"
    assert (
        requests[1]["contents"][-1]
        .parts[0]
        .function_response.response["result"]
        == "تم فتح Chrome."
    )


def test_gemini_worker_surfaces_quota_errors_in_the_selected_language() -> None:
    class QuotaError(Exception):
        status_code = 429

    class FakeModels:
        def generate_content(self, **_kwargs):
            raise QuotaError()

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    worker = GeminiReplyWorker(
        "test-key",
        "test-model",
        "سؤال",
        "ar",
        client_factory=FakeClient,
    )
    errors = []
    worker.request_failed.connect(errors.append)

    worker.run()

    assert errors == ["وصل مفتاح Gemini إلى حد الاستخدام أو الحصة. جرّب لاحقًا."]


def test_gemini_worker_includes_only_user_selected_attachments() -> None:
    requests = []

    class FakeModels:
        def generate_content(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(text="Reviewed")

    class FakeClient:
        def __init__(self, **_kwargs):
            self.models = FakeModels()

    worker = GeminiReplyWorker(
        "test-key",
        "test-model",
        "Review this",
        "en",
        client_factory=FakeClient,
        attachments=(("notes.txt", "text/plain", b"selected content"),),
    )

    worker.run()

    parts = requests[0]["contents"]
    assert "notes.txt" in parts[1]
    assert parts[2].inline_data.data == b"selected content"
    assert parts[2].inline_data.mime_type == "text/plain"


def test_screen_watch_sends_frames_only_while_enabled(qapp) -> None:
    captured = []
    requests = []

    class FakeModels:
        def generate_content(self, **kwargs):
            requests.append(kwargs)
            return SimpleNamespace(text="A browser window is visible.")

    class FakeClient:
        def __init__(self, **kwargs):
            assert "http_options" in kwargs
            self.models = FakeModels()

    def capture(stop_event):
        captured.append(True)
        return {"image": b"frame"}

    worker = ScreenWatchWorker(
        "test-key",
        "test-model",
        capture,
        client_factory=FakeClient,
    )
    observed = []
    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(loop.quit)

    def stop_after_observation(text):
        observed.append(text)
        worker.stop()
        loop.quit()

    worker.observation_ready.connect(stop_after_observation)

    worker.start()
    timeout.start(3000)
    loop.exec()
    assert worker.wait(1000)

    assert captured == [True]
    assert len(requests) == 1
    assert observed == ["A browser window is visible."]


def test_conversation_messages_follow_language_direction_and_start_at_top(qapp) -> None:
    window = ConversationWindow()
    window.set_language("ar")
    arabic_message = window.add_message("أهلًا", "ar", is_user=True)
    window.set_language("en")
    english_message = window.add_message("Hello", "en", is_user=False)

    assert window.title_label.text() == "A little chat"
    assert window.centralWidget().layoutDirection() == Qt.LayoutDirection.LeftToRight
    assert arabic_message.layoutDirection() == Qt.LayoutDirection.RightToLeft
    assert english_message.layoutDirection() == Qt.LayoutDirection.LeftToRight
    assert arabic_message.findChild(QLabel, "messageText").text() == "أهلًا"
    assert window.home_button._return_home
    assert not window.screen_watch_button.icon().isNull()
    assert window.screen_watch_button.size().width() == 34
    assert isinstance(window.connection_button, QLabel)
    assert window.home_button.size().width() == 42
    assert (
        window.home_button.accessibleName()
        == "Return to Ember and close the conversation"
    )
    assert window.thread_layout.itemAt(0).widget() is arabic_message
    assert arabic_message.copy_button.text() == ""
    assert arabic_message.copy_button.accessibleName() == "نسخ"
    assert arabic_message.forward_button.accessibleName() == "إعادة توجيه"
    assert not arabic_message.copy_button.icon().isNull()
    assert not arabic_message.forward_button.icon().isNull()

    voice_message = window.add_message("", "ar", is_user=True, voice=True)
    voice_message.set_voice_language("en")
    assert voice_message.layoutDirection() == Qt.LayoutDirection.LeftToRight
    assert voice_message.sender_label.text() == "You"
    assert voice_message.message_label.text() == "Voice question"

    window.close()


def test_long_unbroken_message_tokens_wrap_without_changing_copied_text(qapp) -> None:
    long_url = "https://example.com/" + "verylongsegment" * 12
    window = ConversationWindow()
    message = window.add_message(long_url, "en", is_user=False)

    assert "\u200b" in message.message_label.text()
    message.copy_button.click()
    assert qapp.clipboard().text() == long_url
    window.close()


def test_wrapped_reply_bubble_keeps_all_text_inside_its_height(qapp) -> None:
    window = ConversationWindow()
    window.resize(480, 620)
    window.show()
    message = window.add_message(
        "This is a normal reply that should wrap across several lines "
        "without cutting off its final line at the bottom of the bubble. "
        "More details: https://example.com/" + "longsegment" * 10,
        "en",
        is_user=False,
    )
    qapp.processEvents()
    QTest.qWait(50)

    assert message.message_label.height() >= message.message_label.heightForWidth(
        message.message_label.width()
    )
    assert message.height() >= message.sizeHint().height()
    assert "\u200b" in message.message_label.text()

    window.close()


def test_message_actions_copy_and_forward_an_editable_quote(qapp) -> None:
    window = ConversationWindow()
    window.show()
    qapp.processEvents()
    message = window.add_message("رد قابل لإعادة التوجيه", "ar", is_user=False)

    message.copy_button.click()
    assert qapp.clipboard().text() == "رد قابل لإعادة التوجيه"

    message.forward_button.click()
    qapp.processEvents()
    assert window.question_edit.text() == "«رد قابل لإعادة التوجيه»"
    window.close()


def test_attachment_picker_sends_only_allowlisted_files(qapp, tmp_path, monkeypatch) -> None:
    text_file = tmp_path / "notes.txt"
    text_file.write_text("selected content", encoding="utf-8")
    monkeypatch.setattr(
        conversation_module.QFileDialog,
        "getOpenFileNames",
        lambda *_args: ([str(text_file)], ""),
    )
    window = ConversationWindow()

    window._select_attachments()

    attachments = window.take_pending_attachments()
    assert attachments == (("notes.txt", "text/plain", b"selected content"),)
    assert not window._pending_attachments
    window.close()


def test_conversation_has_a_bottom_composer_and_ember_close_button(qapp) -> None:
    window = ConversationWindow()
    submitted = []
    dismissed = []
    window.question_submitted.connect(submitted.append)
    window.dismissed.connect(lambda: dismissed.append(True))
    window.show()
    qapp.processEvents()

    assert window.question_edit.placeholderText() == "اكتب رسالتك إلى Ember…"
    window.question_edit.setText("سؤال جديد")
    window.question_send_button.click()
    assert submitted == ["سؤال جديد"]
    assert window.question_edit.text() == ""

    window.home_button.click()
    assert dismissed == [True]
    assert not window.isVisible()


def test_question_bubble_explains_empty_and_overlong_questions(qapp) -> None:
    bubble = AskBubble()
    bubble.set_language("en")
    bubble._send()
    assert bubble.status_label.text() == "Write a question first."

    bubble.editor.setPlainText("x" * 1201)
    bubble._send()
    assert bubble.status_label.text() == "Shorten the question to 1200 characters or fewer."


def test_question_bubble_enter_sends_and_shift_enter_adds_a_line(qapp) -> None:
    bubble = AskBubble()
    bubble.show()
    bubble.editor.setFocus()
    submitted = []
    feedback = []
    bubble.message_submitted.connect(submitted.append)
    bubble.send_feedback.connect(lambda: feedback.append(True))
    bubble.editor.setPlainText("first")
    bubble.editor.moveCursor(QTextCursor.MoveOperation.End)

    QTest.keyClick(bubble.editor, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    assert bubble.editor.toPlainText() == "first\n"

    bubble.editor.insertPlainText("second")
    QTest.keyClick(bubble.editor, Qt.Key.Key_Return)
    assert feedback == [True]
    assert submitted == []
    assert bubble.editor.isEnabled() is False
    assert bubble._send_animation is not None
    QTest.qWait(190)
    assert submitted == ["first\nsecond"]
    assert not bubble.isVisible()
    bubble.close()


def test_question_bubble_close_button_is_orange_and_dismisses(qapp) -> None:
    bubble = AskBubble()
    bubble.show()
    dismissed = []
    bubble.dismissed.connect(lambda: dismissed.append(True))

    assert bubble.close_button.text() == "★"
    assert "color:#ff913f" in bubble.styleSheet()
    assert "background:transparent" in bubble.styleSheet()
    assert bubble.close_button.accessibleName() == "إغلاق"
    bubble.close_button.click()
    assert dismissed == []
    QTest.qWait(190)
    assert dismissed == [True]
    assert not bubble.isVisible()
    bubble.close()


def test_chat_and_question_windows_have_rounded_transparent_corners(qapp) -> None:
    chat = ConversationWindow()
    chat.resize(420, 540)
    chat.show()
    bubble = AskBubble()
    bubble.resize(330, 205)
    bubble.show()
    qapp.processEvents()

    for window in (chat, bubble):
        mask = window.mask()
        assert not mask.contains(QPoint(0, 0))
        assert mask.contains(QPoint(window.width() // 2, window.height() // 2))

    chat.close()
    bubble.close()


def test_chat_header_drag_moves_the_frameless_window(qapp) -> None:
    chat = ConversationWindow()
    chat.show()
    qapp.processEvents()
    start = chat.pos()
    press = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(20, 12),
        QPointF(start + QPoint(20, 12)),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    qapp.sendEvent(chat.title_label, press)
    move = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(40, 32),
        QPointF(start + QPoint(40, 32)),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    qapp.sendEvent(chat.title_label, move)
    release = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(40, 32),
        QPointF(start + QPoint(40, 32)),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    qapp.sendEvent(chat.title_label, release)

    assert chat.pos() == start + QPoint(20, 20)
    chat.close()


def test_gemini_status_dot_distinguishes_verified_and_failed_connections(qapp) -> None:
    chat = ConversationWindow()

    chat.update_connection_status("checking")
    checking_color = chat.connection_button.styleSheet()
    assert "d5a45b" in checking_color
    assert chat.connection_button.toolTip() == "جارٍ التحقق من اتصال Gemini"

    chat.update_connection_status("connected")
    assert "9bc7a1" in chat.connection_button.styleSheet()
    assert chat.connection_button.toolTip() == "Gemini متصل ويستجيب"

    chat.update_connection_status("error")
    assert "e46e62" in chat.connection_button.styleSheet()
    assert chat.connection_button.toolTip() == "يوجد خطأ في اتصال Gemini"
    chat.close()


def test_microphone_capture_opens_a_writable_buffer_and_reports_device_errors(
    qapp, monkeypatch
) -> None:
    class FakeDevice:
        def id(self) -> bytes:
            return b"default"

        def isNull(self) -> bool:
            return False

        def isFormatSupported(self, _audio_format: QAudioFormat) -> bool:
            return True

    class FakeAudioSource(QObject):
        stateChanged = Signal(QAudio.State)

        def __init__(self, _device, _audio_format, parent) -> None:
            super().__init__(parent)
            self.current_error = QAudio.Error.NoError
            self.buffer_is_writable = False

        def start(self, buffer) -> None:
            self.buffer_is_writable = buffer.isWritable()

        def error(self) -> QAudio.Error:
            return self.current_error

        def stop(self) -> None:
            return None

    device = FakeDevice()
    sources = []

    def make_source(*args):
        source = FakeAudioSource(*args)
        sources.append(source)
        return source

    monkeypatch.setattr(
        conversation_module,
        "QMediaDevices",
        SimpleNamespace(
            defaultAudioInput=lambda: device,
            audioInputs=lambda: [device],
        ),
    )
    monkeypatch.setattr(conversation_module, "QAudioSource", make_source)
    capture = MicrophoneCapture()
    failures = []
    capture.recording_failed.connect(failures.append)

    capture.start("en")

    assert sources[0].buffer_is_writable
    sources[0].current_error = QAudio.Error.OpenError
    sources[0].stateChanged.emit(QAudio.State.StoppedState)

    assert failures == [
        "Microphone access failed. Check privacy permissions and the selected input device."
    ]
    assert capture._audio_source is None
    assert capture._buffer is None


def test_microphone_capture_tries_another_input_when_default_fails(
    qapp, monkeypatch
) -> None:
    class FakeDevice:
        def __init__(self, device_id: bytes) -> None:
            self._id = device_id

        def id(self) -> bytes:
            return self._id

        def isNull(self) -> bool:
            return False

        def isFormatSupported(self, _audio_format: QAudioFormat) -> bool:
            return True

    default_device = FakeDevice(b"default")
    fallback_device = FakeDevice(b"fallback")
    sources = []

    class FakeAudioSource(QObject):
        stateChanged = Signal(QAudio.State)

        def __init__(self, device, _audio_format, parent) -> None:
            super().__init__(parent)
            self.device = device
            self.current_error = QAudio.Error.NoError

        def start(self, buffer) -> None:
            assert buffer.isWritable()
            if self.device is default_device:
                self.current_error = QAudio.Error.OpenError

        def error(self) -> QAudio.Error:
            return self.current_error

        def stop(self) -> None:
            return None

    def make_source(*args):
        source = FakeAudioSource(*args)
        sources.append(source)
        return source

    monkeypatch.setattr(
        conversation_module,
        "QMediaDevices",
        SimpleNamespace(
            defaultAudioInput=lambda: default_device,
            audioInputs=lambda: [default_device, fallback_device],
        ),
    )
    monkeypatch.setattr(conversation_module, "QAudioSource", make_source)
    capture = MicrophoneCapture()
    failures = []
    capture.recording_failed.connect(failures.append)

    capture.start("ar")

    assert [source.device for source in sources] == [
        default_device,
        fallback_device,
    ]
    assert capture._audio_source is sources[1]
    assert failures == []
    capture.cancel()
