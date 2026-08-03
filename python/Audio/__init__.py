import os

import pygame

_SOUND_DIR = os.path.dirname(__file__)
_SOUND_FILES = {
    "ding": "ding.wav",
    "soft_ding": "soft_ding.wav",
    "error": "error.wav",
    "click": "click.wav",
}

_sounds: dict[str, "pygame.mixer.Sound"] = {}
_ready: bool = False


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


def play(name: str) -> None:
    """Play the loaded effect <name>, or do nothing if audio is unavailable."""
    if not _ready:
        init()
    sound = _sounds.get(name)
    if sound is not None:
        sound.play()
