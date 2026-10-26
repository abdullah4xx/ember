"""Small, cacheable pixel-art sound cues synthesized from simple waveforms."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import random
import struct
import wave
from io import BytesIO


@dataclass(frozen=True)
class SoundCue:
    notes: tuple[float, ...]
    duration: float
    waveform: str = "sine"
    noise: float = 0.0


SOUND_CUES = {
    "pet": SoundCue((660, 990, 784), 0.24),
    "send": SoundCue((620, 880, 1040), 0.18, "triangle"),
    "walk": SoundCue((320, 280), 0.12, "triangle"),
    "jump": SoundCue((420, 760, 1040), 0.22),
    "fall": SoundCue((700, 540, 350), 0.28, "triangle"),
    "listen": SoundCue((600, 880), 0.2),
    "think": SoundCue((440, 554, 659), 0.32),
    "talk": SoundCue((520, 680, 580), 0.18),
    "point": SoundCue((740, 980), 0.15),
    "happy": SoundCue((523, 659, 784, 1047), 0.38),
    "landing": SoundCue((180, 125, 260), 0.26, "triangle", 0.24),
    "cling": SoundCue((310, 480, 390), 0.21, "triangle"),
    "yawn": SoundCue((340, 260, 220), 0.44, "sine"),
    "sit": SoundCue((390, 330), 0.18, "triangle"),
    "surprised": SoundCue((520, 1120), 0.2),
    "confused": SoundCue((390, 330, 370), 0.32),
    "throw": SoundCue((920, 650, 420), 0.24, "triangle", 0.1),
    "approved": SoundCue((523, 659, 880), 0.3),
    "denied": SoundCue((320, 230), 0.25, "triangle"),
    "opened": SoundCue((580, 770, 960), 0.28),
    "celebrate": SoundCue((523, 659, 784, 988, 1175), 0.48),
}


def render_sound(name: str, sample_rate: int = 24_000) -> bytes:
    cue = SOUND_CUES[name]
    sample_count = round(cue.duration * sample_rate)
    phase = 0.0
    noise = random.Random(list(SOUND_CUES).index(name) + 31)
    pcm = bytearray()
    for index in range(sample_count):
        progress = index / max(1, sample_count - 1)
        segment = min(len(cue.notes) - 1, int(progress * len(cue.notes)))
        segment_progress = progress * len(cue.notes) - segment
        start_frequency = cue.notes[segment]
        end_frequency = cue.notes[min(segment + 1, len(cue.notes) - 1)]
        frequency = start_frequency + (end_frequency - start_frequency) * (
            segment_progress * 0.45
        )
        phase += 2 * math.pi * frequency / sample_rate
        fundamental = math.sin(phase)
        if cue.waveform == "triangle":
            tone = 2 / math.pi * math.asin(fundamental)
        elif cue.waveform == "square":
            tone = 1.0 if fundamental >= 0 else -1.0
        else:
            tone = fundamental + math.sin(phase * 2.01) * 0.16
        attack = min(1.0, index / max(1, round(sample_rate * 0.008)))
        envelope = attack * (1.0 - progress) ** 1.8
        sample = tone * envelope + noise.uniform(-1.0, 1.0) * cue.noise * envelope
        pcm.extend(struct.pack("<h", round(max(-1.0, min(1.0, sample)) * 24_000)))

    output = BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(pcm)
    return output.getvalue()


def generate_sound_files(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in SOUND_CUES:
        path = directory / f"{name}.wav"
        if not path.is_file():
            path.write_bytes(render_sound(name))
        files[name] = path
    return files
