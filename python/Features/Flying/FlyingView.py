import math
import threading

import pygame

from Features.Flying.FlyingController import FlyingController
from Features.Flying.FlyingViewModel import FlyingViewModel


ROLLOUT_SECONDS = 18
FLAP_FRAMES = 6
INPUT_BG_COLOR = (10, 22, 38)
INPUT_BORDER_COLOR = (120, 150, 185)
TEXT_COLOR = (245, 249, 255)
HINT_COLOR = (200, 220, 240)


class FlyingView:
    """The flight screen. The player types a flight duration in minutes; the
    flight is simulated in the background, then its trajectory is rolled out over
    the sky at 60fps with a bird flapping at the newest point. Q or Escape quits
    at any time."""

    _controller: FlyingController
    _view_model: FlyingViewModel
    _running: bool
    _phase: str
    _busy: bool
    _buffer: str
    _points_per_frame: int
    _frame: int

    def __init__(
        self, controller: FlyingController, view_model: FlyingViewModel
    ) -> None:
        self._controller = controller
        self._view_model = view_model
        self._running = True
        self._phase = "input"
        self._busy = False
        self._buffer = ""
        self._points_per_frame = 0
        self._frame = 0

        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Thingamabob Simulator")
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Read input, roll out the flight, and redraw at 60 frames a second."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)

            self._advance()
            self._draw()
            pygame.display.flip()
            self._clock.tick(60)

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Type the duration during input; while flying, R toggles the raw flight
        line and Q quits; Escape quits at any time."""
        if event.key == pygame.K_ESCAPE:
            self._running = False
        elif self._phase == "input":
            if event.key == pygame.K_RETURN:
                self._submit()
            elif event.key == pygame.K_BACKSPACE:
                self._buffer = self._buffer[:-1]
            elif event.unicode.isprintable():
                self._buffer += event.unicode
        elif event.key == pygame.K_q:
            self._running = False
        elif event.key == pygame.K_r:
            self._view_model.toggle_raw()

    def _submit(self) -> None:
        """Launch the flight if the typed duration is a positive number."""
        try:
            minutes = float(self._buffer)
        except ValueError:
            return
        if minutes <= 0:
            return
        self._phase = "flying"
        self._run_in_background(lambda: self._controller.handle_fly(minutes))

    def _run_in_background(self, action) -> None:
        """Simulate the flight off the draw thread so input stays responsive."""
        self._busy = True

        def worker() -> None:
            try:
                action()
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _advance(self) -> None:
        """Roll out the next slice of the flight and beat the bird's wings."""
        if self._phase != "flying" or not self._view_model.ready():
            return
        if self._points_per_frame == 0:
            total = len(self._view_model.flight_hist)
            self._points_per_frame = max(1, math.ceil(total / (ROLLOUT_SECONDS * 60)))
        if not self._view_model.done():
            self._view_model.reveal(self._points_per_frame)
            self._frame += 1
            if self._frame % FLAP_FRAMES == 0:
                self._view_model.set_wing(not self._view_model.wing_up)

    def _draw(self) -> None:
        """Draw the scene, then whichever prompt or hint the phase calls for."""
        self._view_model.draw(self._screen)
        if self._phase == "input":
            self._draw_prompt()
        elif not self._view_model.ready():
            self._draw_center("Taking off...")
        elif not self._view_model.done():
            self._draw_hint("Q  quit      R  toggle raw flight")

    def _draw_prompt(self) -> None:
        """Draw the flight-duration input box centred over the sky."""
        font = pygame.font.SysFont(None, 34)
        text = font.render(
            f"Flight duration (minutes): {self._buffer}_", True, TEXT_COLOR
        )
        box = text.get_rect().inflate(40, 26)
        box.center = (self._screen.get_width() // 2, self._screen.get_height() // 2)
        pygame.draw.rect(self._screen, INPUT_BG_COLOR, box, border_radius=8)
        pygame.draw.rect(self._screen, INPUT_BORDER_COLOR, box, width=1, border_radius=8)
        self._screen.blit(text, text.get_rect(center=box.center))
        self._draw_hint("Esc to quit")

    def _draw_center(self, message: str) -> None:
        """Draw <message> centred over the sky on a black block so it stands
        out against the background."""
        font = pygame.font.SysFont(None, 34)
        text = font.render(message, True, TEXT_COLOR)
        box = text.get_rect().inflate(48, 30)
        box.center = (self._screen.get_width() // 2, self._screen.get_height() // 2)
        pygame.draw.rect(self._screen, (0, 0, 0), box, border_radius=8)
        self._screen.blit(text, text.get_rect(center=box.center))

    def _draw_hint(self, message: str) -> None:
        """Draw <message> as a hint along the bottom of the screen."""
        font = pygame.font.SysFont(None, 24)
        text = font.render(message, True, HINT_COLOR)
        self._screen.blit(
            text,
            text.get_rect(
                midbottom=(self._screen.get_width() // 2, self._screen.get_height() - 12)
            ),
        )
