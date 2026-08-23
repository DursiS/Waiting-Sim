import os

import pygame

_SOUND_DIR = os.path.dirname(__file__)
_SOUND_FILES = {
    "ding": "ding.wav",
    "soft_ding": "soft_ding.wav",
    "error": "error.wav",
    "click": "click.wav",
    "victory": "victory.wav",
    "lose": "lose.wav",
    "quit": "quit.wav",
}

_sounds: dict[str, "pygame.mixer.Sound"] = {}
_ready: bool = False
_volume: float = 0.7


def init() -> None:
    """Start the audio mixer and load the effects once, degrading silently to
    no sound when no audio device is available."""
    global _ready
    if _ready:
        return
    _ready = True
    try:
        pygame.mixer.init()
    except pygame.error:
        return
    for name, filename in _SOUND_FILES.items():
        path = os.path.join(_SOUND_DIR, filename)
        if not os.path.exists(path):
            continue
        try:
            _sounds[name] = pygame.mixer.Sound(path)
        except pygame.error:
            pass
    set_volume(_volume)


def get_volume() -> float:
    """Return the master volume (0.0 muted .. 1.0 full) all audio obeys."""
    return _volume


def set_volume(volume: float) -> None:
    """Set the master volume every effect -- and any future music -- plays at.

    Each effect keeps its own baked-in relative loudness; this scales them all
    together, so the balance between a loud ding and a soft chime is kept."""
    global _volume
    _volume = max(0.0, min(1.0, volume))
    for sound in _sounds.values():
        sound.set_volume(_volume)
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(_volume)


def play(name: str) -> None:
    """Play the loaded effect <name>, or do nothing if audio is unavailable."""
    if not _ready:
        init()
    sound = _sounds.get(name)
    if sound is not None:
        sound.set_volume(_volume)
        sound.play()
