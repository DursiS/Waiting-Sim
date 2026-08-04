import threading

import pygame

import Audio
from Features.Gamble import (
    GambleController,
    GamblePresenter,
    GambleInteractor,
    GambleViewModel,
)


class GambleView:
    """The gamble screen. In the betting phase it renders the betting view
    model and submits typed answers; once betting ends it renders the automatic
    game view model while the game plays out in the background. Restart returns
    to a fresh betting phase; Escape (or Quit) leaves to the menu."""

    _controller: GambleController
    _presenter: GamblePresenter
    _interactor: GambleInteractor
    _view_model: GambleViewModel
    _running: bool
    _buffer: str
    _game_started: bool

    def __init__(
        self,
        controller: GambleController,
        presenter: GamblePresenter,
        interactor: GambleInteractor,
        view_model: GambleViewModel,
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._view_model = view_model
        self._game_view_model = interactor.game_view_model()
        self._running = True
        self._buffer = ""
        self._game_started = False

        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Waiting-Sim")
        self._controller.handle_start()
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Listen for keypresses, drive the flow, and redraw each frame."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)

            self._maybe_start_game()
            self._draw()
            pygame.display.flip()
            self._clock.tick(60)

    def _maybe_start_game(self) -> None:
        """Once betting flips to the game phase, play the game in a background
        thread so its animation does not freeze the frame loop."""
        if self._view_model.phase == "game" and not self._game_started:
            self._game_started = True
            threading.Thread(target=self._interactor.run_game, daemon=True).start()

    def _draw(self) -> None:
        """Draw whichever view model the current phase calls for, resizing the
        window to fit it."""
        if self._view_model.phase == "game":
            self._fit(self._game_view_model.width, self._game_view_model.height)
            self._game_view_model.draw(self._screen)
        else:
            self._fit(self._view_model.width, self._view_model.height)
            self._view_model.draw(self._screen, self._buffer)

    def _fit(self, width: int, height: int) -> None:
        """Resize the window to (<width>, <height>) only if it isn't already."""
        if self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Restart, quit, or (in betting) type and submit the current answer.

        While a game is playing out no key does anything, so the player cannot
        restart or quit to dodge a bet; the controls only work once the outcome
        has been revealed in the payoff phase."""
        if self._view_model.phase == "game":
            if self._game_view_model.bet_result is None:
                return
            if event.key == pygame.K_r:
                self._restart()
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self._quit()
            return

        if event.key == pygame.K_ESCAPE:
            self._quit()
        elif self._view_model.prompt:
            if event.key == pygame.K_RETURN:
                self._controller.handle_answer(self._buffer)
                self._buffer = ""
            elif event.key == pygame.K_BACKSPACE:
                self._buffer = self._buffer[:-1]
            elif event.unicode.isprintable():
                self._buffer += event.unicode

    def _restart(self) -> None:
        """Return to a fresh betting phase, cancelling any running game."""
        self._buffer = ""
        self._game_started = False
        self._view_model.clear_messages()
        self._controller.handle_start()

    def _quit(self) -> None:
        """Leave the gamble screen with a quit sound."""
        Audio.play("quit")
        self._running = False
