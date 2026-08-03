"""Regenerate the effect .wav files in this package.

Dev tool (needs numpy); the runtime only loads the .wav files it writes.
Run from the python/ directory:  python -m Audio._generate
"""
import os
import wave

import numpy as np

RATE = 44100
DIR = os.path.dirname(__file__)


def _partials(freq_amps: list[tuple[float, float]], seconds: float,
              decay: float, attack: float = 0.004) -> np.ndarray:
    """Sum decaying sine partials into one note with a soft attack."""
    t = np.linspace(0, seconds, int(RATE * seconds), endpoint=False)
    wave_data = np.zeros_like(t)
    for freq, amp in freq_amps:
        wave_data += amp * np.sin(2 * np.pi * freq * t)
    envelope = np.exp(-t / decay)
    ramp = np.clip(t / attack, 0, 1)
    return wave_data * envelope * ramp


def _write(name: str, samples: np.ndarray, peak: float) -> None:
    """Normalise <samples> to <peak> of full scale and write a 16-bit mono wav."""
    samples = samples / (np.max(np.abs(samples)) or 1.0) * peak
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767).astype("<i2")
    path = os.path.join(DIR, name)
    with wave.open(path, "w") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(pcm.tobytes())
    print("wrote", path)


def ding() -> np.ndarray:
    """Bright two-note completion bell (a rising fifth)."""
    low = _partials([(784, 1.0), (1568, 0.4), (2352, 0.15)], 0.32, 0.22)
    high = _partials([(1175, 1.0), (2350, 0.4), (3525, 0.15)], 0.55, 0.30)
    note = np.zeros(len(low) + len(high) - int(RATE * 0.06))
    note[: len(low)] += low
    note[len(low) - int(RATE * 0.06):] += high
    return note


def soft_ding() -> np.ndarray:
    """Quiet, short, high chime for arriving at a station."""
    return _partials([(1319, 1.0), (2637, 0.25)], 0.26, 0.09)


def error() -> np.ndarray:
    """Low dissonant descending buzz for an invalid entry."""
    first = _partials([(233, 1.0), (233 * 3, 0.25), (220, 0.6)], 0.12, 0.10)
    second = _partials([(175, 1.0), (175 * 3, 0.25), (165, 0.6)], 0.16, 0.10)
    return np.concatenate([first, second])


def click() -> np.ndarray:
    """Short crisp UI tick for a menu key press."""
    tone = _partials([(1250, 1.0), (2500, 0.3)], 0.045, 0.013, attack=0.0008)
    tick = np.random.default_rng(0).normal(0, 1, len(tone)) * np.exp(
        -np.linspace(0, 0.045, len(tone)) / 0.004
    )
    return tone + 0.25 * tick


if __name__ == "__main__":
    _write("ding.wav", ding(), 0.55)
    _write("soft_ding.wav", soft_ding(), 0.24)
    _write("error.wav", error(), 0.45)
    _write("click.wav", click(), 0.35)
