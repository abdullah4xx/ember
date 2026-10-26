import json
import sys
from types import SimpleNamespace

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Signal
from PySide6.QtMultimedia import QAudio

from ember import wake_word


def test_wake_phrase_matches_word_boundaries_and_punctuation() -> None:
    assert wake_word.is_wake_phrase("Ember!")
    assert wake_word.is_wake_phrase("Hey, EMBER?")
    assert not wake_word.is_wake_phrase("remember")
    assert not wake_word.is_wake_phrase("embers")


def test_listener_falls_back_when_default_microphone_cannot_open(
    qapp, monkeypatch
) -> None:
    class FakeDevice:
        def __init__(self, device_id: bytes) -> None:
            self.device_id = device_id

        def id(self) -> bytes:
            return self.device_id

        def isNull(self) -> bool:
            return False

        def isFormatSupported(self, _audio_format) -> bool:
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

        def start(self, _buffer) -> None:
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

    class FakeRecognizer:
        def __init__(self, *_args) -> None:
            pass

    monkeypatch.setitem(
        sys.modules,
        "vosk",
        SimpleNamespace(KaldiRecognizer=FakeRecognizer),
    )
    monkeypatch.setattr(
        wake_word,
        "QMediaDevices",
        SimpleNamespace(
            defaultAudioInput=lambda: default_device,
            audioInputs=lambda: [default_device, fallback_device],
        ),
    )
    monkeypatch.setattr(wake_word, "QAudioSource", make_source)

    listener = wake_word.WakeWordListener()
    listener._model = object()
    statuses = []
    listener.status_changed.connect(statuses.append)
    listener.start()

    assert [source.device for source in sources] == [
        default_device,
        fallback_device,
    ]
    assert listener.is_listening
    assert statuses[-1] == "Ember يستمع محليًا لكلمة التنبيه"
    listener.shutdown()
    listener.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def test_listener_opens_recording_when_wake_word_is_recognized(qapp) -> None:
    listener = wake_word.WakeWordListener()
    listener._enabled = True
    listener._recognizer = SimpleNamespace(
        AcceptWaveform=lambda _chunk: False,
        PartialResult=lambda: json.dumps({"partial": "Ember!"}),
    )
    class FakeBuffer:
        def data(self) -> bytes:
            return b"\0\0" * 800

        def close(self) -> None:
            pass

        def deleteLater(self) -> None:
            pass

    class FakeSource:
        def error(self) -> QAudio.Error:
            return QAudio.Error.NoError

        def stop(self) -> None:
            pass

        def deleteLater(self) -> None:
            pass

    buffer = FakeBuffer()
    listener._buffer = buffer
    listener._audio_source = FakeSource()
    detected = []
    listener.wake_word_detected.connect(lambda: detected.append(True))

    listener._poll()

    assert detected == [True]
    assert listener._paused
    listener.shutdown()
    listener.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()
