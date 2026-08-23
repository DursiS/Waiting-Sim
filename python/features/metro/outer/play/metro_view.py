import threading
import traceback
from typing import Callable

import pygame

from app import audio
from .metro_controller import MetroController
from .metro_presenter import MetroPresenter
from .metro_view_model import MetroViewModel
from features.metro.inner import MetroInteractor, MetroInputData


class MetroView:
    """The game screen. Given a ready request from the option-selection screen,
    the whole game plays out in a background thread so the 60fps draw loop keeps
    streaming the presenter's turn-by-turn updates in real time. Once a finished
    game is on screen R restarts it with the same request and Q returns to the
    option-selection screen. While a game is playing no control key does
    anything, so a gamble cannot be dodged by restarting or quitting mid-game."""

    _request: MetroInputData
    _controller: MetroController
    _presenter: MetroPresenter
    _interactor: MetroInteractor
    _view_model: MetroViewModel
    _running: bool
    _busy: bool

    def __init__(
        self,
        request: MetroInputData,
        controller: MetroController,
        presenter: MetroPresenter,
        interactor: MetroInteractor,
        view_model: MetroViewModel,
    ) -> None:
        self._request = request
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._view_model = view_model
        self._running = True
        self._busy = False

        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Thingamabob Simulator")
        self._start_game()
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Listen for keypresses, drive the controls, and redraw the rail map
        each frame."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)

            self._draw()
            pygame.display.flip()
            self._clock.tick(60)

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Restart or quit once the game has finished; ignore keys mid-game."""
        if self._busy:
            return
        if self._view_model.game_over:
            if event.key == pygame.K_r:
                self.on_restart()
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.on_quit()

    def _draw(self) -> None:
        """Draw the rail map for the current game state."""
        self._fit(self._view_model.width, self._view_model.height)
        self._view_model.draw(self._screen)

    def _fit(self, width: int, height: int) -> None:
        """Resize the window to (<width>, <height>) only if it isn't already."""
        if self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))

    def _run_in_background(self, action: Callable[[], None]) -> None:
        """Run <action> in a daemon thread so the draw loop keeps streaming the
        presenter's updates in real time instead of freezing on the game."""
        if self._busy:
            return
        self._busy = True

        def worker() -> None:
            try:
                action()
            except Exception:
                traceback.print_exc()
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _start_game(self) -> None:
        """Play the requested game in the background."""
        request = self._request
        self._run_in_background(
            lambda: self._controller.handle_play(
                None,
                request.name,
                request.map_id,
                request.rand_arrival,
                request.gamble,
                request.raw_bets,
                request.animate,
            )
        )

    def on_quit(self) -> None:
        """Leave the game screen back to the option-selection screen."""
        audio.play("quit")
        self._running = False

    def on_restart(self) -> None:
        """Replay the finished game with the same request."""
        self._run_in_background(self._controller.handle_restart)
