import math

import pygame

from Data import Audio


PANEL_TOP = 16
PANEL_HEIGHT = 34
MARGIN_RIGHT = 20
PANEL_PAD_X = 12
ICON_W = 18
GAP = 10
TRACK_W = 132
TRACK_H = 6
KNOB_R = 8

PANEL_COLOR = (28, 31, 40)
PANEL_BORDER_COLOR = (58, 63, 78)
TRACK_BG_COLOR = (54, 58, 70)
FILL_COLOR = (240, 210, 110)
KNOB_COLOR = (250, 232, 178)
KNOB_RING_COLOR = (255, 244, 210)
KNOB_BORDER_COLOR = (26, 27, 33)
ICON_COLOR = (206, 212, 224)
MUTE_COLOR = (150, 120, 120)
TEXT_COLOR = (206, 212, 224)


class VolumeSlider:
    """A compact volume control for the main menu: a speaker icon, a rounded
    track with a gold fill and knob, and a percentage. Drag the track to set
    the volume; click the speaker to mute or restore it. It reads and writes
    the shared Audio master volume, so every effect (and future music) obeys."""

    _dragging: bool
    _muted_from: float | None

    def __init__(self) -> None:
        """Create the slider bound to the shared Audio master volume."""
        self._dragging = False
        self._muted_from = None
        self._font = pygame.font.SysFont(None, 22)

    def _geometry(self, screen_width: int) -> dict:
        """Return the laid-out rects/points, right-aligned to <screen_width>."""
        pct_w = self._font.size("100%")[0]
        center_y = PANEL_TOP + PANEL_HEIGHT // 2
        pct_right = screen_width - MARGIN_RIGHT - PANEL_PAD_X
        track_right = pct_right - pct_w - GAP
        track_left = track_right - TRACK_W
        icon_right = track_left - GAP
        icon_left = icon_right - ICON_W
        panel = pygame.Rect(
            icon_left - PANEL_PAD_X,
            PANEL_TOP,
            (pct_right - (icon_left - PANEL_PAD_X)) + PANEL_PAD_X,
            PANEL_HEIGHT,
        )
        return {
            "center_y": center_y,
            "track": pygame.Rect(track_left, center_y - TRACK_H // 2, TRACK_W, TRACK_H),
            "icon_left": icon_left,
            "pct_right": pct_right,
            "panel": panel,
            "hit": pygame.Rect(
                track_left - KNOB_R, center_y - 13, TRACK_W + 2 * KNOB_R, 26
            ),
            "icon_hit": pygame.Rect(icon_left - 3, center_y - 12, ICON_W + 6, 24),
        }

    def handle_event(self, event: pygame.event.Event, screen_width: int) -> None:
        """Update the volume from a mouse event on the slider or speaker icon."""
        geo = self._geometry(screen_width)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if geo["icon_hit"].collidepoint(event.pos):
                self._toggle_mute()
            elif geo["hit"].collidepoint(event.pos):
                self._dragging = True
                self._set_from_x(event.pos[0], geo["track"])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_from_x(event.pos[0], geo["track"])

    def _set_from_x(self, mouse_x: int, track: pygame.Rect) -> None:
        """Set the volume from the mouse x-position along <track>."""
        fraction = (mouse_x - track.left) / track.width
        Audio.set_volume(max(0.0, min(1.0, fraction)))
        self._muted_from = None

    def _toggle_mute(self) -> None:
        """Mute the audio, or restore the volume it had before muting."""
        if Audio.get_volume() > 0:
            self._muted_from = Audio.get_volume()
            Audio.set_volume(0.0)
        else:
            Audio.set_volume(self._muted_from or 0.5)
            self._muted_from = None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the slider in the top-right corner of <screen>."""
        geo = self._geometry(screen.get_width())
        volume = Audio.get_volume()

        pygame.draw.rect(
            screen, PANEL_COLOR, geo["panel"], border_radius=PANEL_HEIGHT // 2
        )
        pygame.draw.rect(
            screen,
            PANEL_BORDER_COLOR,
            geo["panel"],
            width=1,
            border_radius=PANEL_HEIGHT // 2,
        )

        track = geo["track"]
        pygame.draw.rect(screen, TRACK_BG_COLOR, track, border_radius=TRACK_H // 2)
        knob_x = int(track.left + volume * track.width)
        if knob_x > track.left:
            fill = pygame.Rect(track.left, track.top, knob_x - track.left, track.height)
            pygame.draw.rect(screen, FILL_COLOR, fill, border_radius=TRACK_H // 2)

        knob_center = (knob_x, geo["center_y"])
        pygame.draw.circle(screen, KNOB_COLOR, knob_center, KNOB_R)
        pygame.draw.circle(screen, KNOB_BORDER_COLOR, knob_center, KNOB_R, 1)
        pygame.draw.circle(screen, KNOB_RING_COLOR, knob_center, KNOB_R - 3, 1)

        self._draw_speaker(screen, geo["icon_left"], geo["center_y"], volume)

        pct = self._font.render(f"{round(volume * 100)}%", True, TEXT_COLOR)
        screen.blit(pct, pct.get_rect(midright=(geo["pct_right"], geo["center_y"])))

    def _draw_speaker(
        self, screen: pygame.Surface, left: int, center_y: int, volume: float
    ) -> None:
        """Draw the speaker glyph, with sound waves when audible or a mute mark
        when silenced."""
        body = [
            (left, center_y - 3),
            (left + 4, center_y - 3),
            (left + 10, center_y - 9),
            (left + 10, center_y + 9),
            (left + 4, center_y + 3),
            (left, center_y + 3),
        ]
        pygame.draw.polygon(screen, ICON_COLOR, body)

        if volume <= 0:
            x = left + 13
            pygame.draw.line(
                screen, MUTE_COLOR, (x, center_y - 5), (x + 6, center_y + 5), 2
            )
            pygame.draw.line(
                screen, MUTE_COLOR, (x + 6, center_y - 5), (x, center_y + 5), 2
            )
            return

        waves = 1 if volume < 0.5 else 2
        for i in range(waves):
            radius = 5 + i * 5
            rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            rect.center = (left + 8, center_y)
            pygame.draw.arc(screen, ICON_COLOR, rect, -math.pi / 4, math.pi / 4, 2)
