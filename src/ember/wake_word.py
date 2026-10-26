"""Local, opt-in desktop wake-word listening."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from zipfile import ZipFile

from PySide6.QtCore import (
    QByteArray,
    QBuffer,
    QIODevice,
    QObject,
    QStandardPaths,
    QThread,
    QTimer,
    Signal,
)
from PySide6.QtMultimedia import QAudio, QAudioDevice, QAudioFormat, QAudioSource, QMediaDevices


MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
MODEL_MAX_BYTES = 80 * 1024 * 1024
MODEL_MAX_UNPACKED_BYTES = 200 * 1024 * 1024
SAMPLE_RATE = 16_000


def is_wake_phrase(text: str) -> bool:
    return re.search(r"(?<![a-z])ember(?![a-z])", text.casefold()) is not None


def _model_directory() -> Path:
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    return Path(base or (Path.home() / ".local" / "share" / "Ember")) / "models"


def _model_is_ready(path: Path) -> bool:
    return (path / "am" / "final.mdl").is_file() and (
        path / "conf" / "mfcc.conf"
    ).is_file()


class _ModelLoader(QThread):
    model_ready = Signal(object)
    failed = Signal(str)
    status_changed = Signal(str)

    def run(self) -> None:
        try:
            model_path = self._ensure_model()
            if self.isInterruptionRequested():
                return
            from vosk import Model

            self.model_ready.emit(Model(str(model_path)))
        except InterruptedError:
            return
        except Exception as error:
            if not self.isInterruptionRequested():
                self.failed.emit(str(error))

    def _ensure_model(self) -> Path:
        root = _model_directory()
        root.mkdir(parents=True, exist_ok=True)
        target = root / MODEL_NAME
        if _model_is_ready(target):
            return target
        if target.exists():
            shutil.rmtree(target)

        self.status_changed.emit("جارٍ تنزيل نموذج الاستماع المحلي (نحو 40 م.ب)…")
        with tempfile.TemporaryDirectory(prefix="wake-", dir=root) as temporary:
            temporary_path = Path(temporary)
            archive_path = temporary_path / "model.zip"
            request = Request(
                MODEL_URL,
                headers={"User-Agent": "Ember-Desktop-Companion"},
            )
            downloaded = 0
            with urlopen(request, timeout=20) as response, archive_path.open("wb") as archive:
                while True:
                    if self.isInterruptionRequested():
                        raise InterruptedError("Model download cancelled.")
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > MODEL_MAX_BYTES:
                        raise ValueError("Wake-word model download exceeded its size limit.")
                    archive.write(chunk)

            extracted_path = temporary_path / "extracted"
            extracted_path.mkdir()
            with ZipFile(archive_path) as archive:
                entries = archive.infolist()
                if sum(entry.file_size for entry in entries) > MODEL_MAX_UNPACKED_BYTES:
                    raise ValueError("Wake-word model archive exceeded its size limit.")
                root_path = extracted_path.resolve()
                for entry in entries:
                    resolved = (extracted_path / entry.filename).resolve()
                    if not resolved.is_relative_to(root_path):
                        raise ValueError("Wake-word model archive contains an invalid path.")
                    if self.isInterruptionRequested():
                        raise InterruptedError("Model extraction cancelled.")
                archive.extractall(extracted_path)

            extracted_model = extracted_path / MODEL_NAME
            if not _model_is_ready(extracted_model):
                raise ValueError("Wake-word model archive is incomplete.")
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted_model.replace(target)
        return target


class WakeWordListener(QObject):
    """Recognize the word Ember locally without retaining idle microphone audio."""

    wake_word_detected = Signal()
    status_changed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._enabled = False
        self._paused = False
        self._loader: _ModelLoader | None = None
        self._model = None
        self._recognizer = None
        self._devices: list[QAudioDevice] = []
        self._next_device = 0
        self._audio_source: QAudioSource | None = None
        self._buffer: QBuffer | None = None
        self._releasing = False
        self._last_size = 0
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._poll)

    @property
    def is_listening(self) -> bool:
        return self._audio_source is not None

    def start(self) -> None:
        self._enabled = True
        self._paused = False
        if self._audio_source is not None:
            return
        if self._model is not None:
            self._start_audio()
            return
        if self._loader is not None:
            return
        self.status_changed.emit("جارٍ تجهيز الاستماع المحلي إلى «Ember»…")
        loader = _ModelLoader(self)
        self._loader = loader
        loader.model_ready.connect(self._model_loaded)
        loader.failed.connect(self._model_failed)
        loader.status_changed.connect(self.status_changed)
        loader.finished.connect(self._loader_finished)
        loader.start()

    def pause(self) -> None:
        if not self._enabled:
            return
        self._paused = True
        self._release_audio()
        self.status_changed.emit("الاستماع متوقف مؤقتًا")

    def stop(self) -> None:
        self._enabled = False
        self._paused = False
        if self._loader is not None and self._loader.isRunning():
            self._loader.requestInterruption()
        self._release_audio()
        self.status_changed.emit("الاستماع إلى كلمة التنبيه متوقف")

    def shutdown(self) -> None:
        self.stop()
        if self._loader is not None and self._loader.isRunning():
            self._loader.wait()

    def _model_loaded(self, model: object) -> None:
        self._model = model
        if self._enabled and not self._paused:
            self._start_audio()

    def _model_failed(self, message: str) -> None:
        self.status_changed.emit(f"تعذر تجهيز الاستماع المحلي: {message}")

    def _loader_finished(self) -> None:
        if self._loader is not None:
            self._loader.deleteLater()
            self._loader = None

    def _start_audio(self) -> None:
        if not self._enabled or self._paused or self._model is None:
            return
        try:
            from vosk import KaldiRecognizer

            self._recognizer = KaldiRecognizer(
                self._model,
                SAMPLE_RATE,
                json.dumps(["ember", "[unk]"]),
            )
        except Exception as error:
            self.status_changed.emit(f"تعذر بدء الاستماع المحلي: {error}")
            return

        available = list(QMediaDevices.audioInputs())
        default = QMediaDevices.defaultAudioInput()
        if default.isNull():
            self._devices = available
        else:
            default_id = bytes(default.id())
            self._devices = [default] + [
                device for device in available
                if bytes(device.id()) != default_id
            ]
        self._next_device = 0
        self._start_next_device()

    def _start_next_device(self) -> None:
        while self._next_device < len(self._devices):
            device = self._devices[self._next_device]
            self._next_device += 1
            audio_format = QAudioFormat()
            audio_format.setSampleRate(SAMPLE_RATE)
            audio_format.setChannelCount(1)
            audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            if not device.isFormatSupported(audio_format):
                continue
            buffer = QBuffer(QByteArray(), self)
            if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
                buffer.deleteLater()
                continue
            source = QAudioSource(device, audio_format, self)
            self._buffer = buffer
            self._audio_source = source
            source.stateChanged.connect(
                lambda state, current=source: self._audio_state_changed(
                    current, state
                )
            )
            source.start(buffer)
            if source.error() != QAudio.Error.NoError:
                self._release_audio()
                continue
            self._last_size = 0
            self._poll_timer.start()
            self.status_changed.emit("Ember يستمع محليًا لكلمة التنبيه")
            return
        self._recognizer = None
        self.status_changed.emit(
            "تعذر فتح أي ميكروفون. تحقق من إعدادات الإدخال والصلاحيات."
        )

    def _poll(self) -> None:
        source = self._audio_source
        buffer = self._buffer
        if source is None or buffer is None:
            return
        if source.error() in (
            QAudio.Error.OpenError,
            QAudio.Error.IOError,
            QAudio.Error.FatalError,
        ):
            self._release_audio()
            self._start_next_device()
            return

        data = bytes(buffer.data())
        chunk = data[self._last_size :]
        self._last_size = len(data)
        if self._last_size >= 256 * 1024:
            buffer.buffer().clear()
            buffer.seek(0)
            self._last_size = 0
        if not chunk or self._recognizer is None:
            return
        try:
            if self._recognizer.AcceptWaveform(chunk):
                text = json.loads(self._recognizer.Result()).get("text", "")
            else:
                text = json.loads(self._recognizer.PartialResult()).get(
                    "partial", ""
                )
        except Exception as error:
            self.status_changed.emit(f"تعذر تحليل الصوت محليًا: {error}")
            self.pause()
            return
        if is_wake_phrase(text):
            self.pause()
            self.status_changed.emit("سمع Ember كلمة التنبيه؛ جارٍ فتح التسجيل")
            self.wake_word_detected.emit()

    def _audio_state_changed(
        self, source: QAudioSource, _state: QAudio.State
    ) -> None:
        if source is not self._audio_source or self._releasing:
            return
        if source.error() in (
            QAudio.Error.OpenError,
            QAudio.Error.IOError,
            QAudio.Error.FatalError,
        ):
            self._release_audio()
            self._start_next_device()

    def _release_audio(self) -> None:
        self._poll_timer.stop()
        self._releasing = True
        if self._audio_source is not None:
            self._audio_source.stop()
            self._audio_source.deleteLater()
            self._audio_source = None
        if self._buffer is not None:
            self._buffer.close()
            self._buffer.deleteLater()
            self._buffer = None
        self._last_size = 0
        self._releasing = False
