import pygame

from Features.Gamble import (
    GambleController,
    GamblePresenter,
    GambleInteractor,
    GambleViewModel,
)


class GambleView:
    """The gamble screen: renders the current question from the view model and
    submits typed answers to the controller. A finished round is replayed with
    Enter; Escape quits back to the menu."""

    _controller: GambleController
    _presenter: GamblePresenter
    _interactor: GambleInteractor
    _view_model: GambleViewModel
    _running: bool
    _buffer: str

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
        self._running = True
        self._buffer = ""

        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Waiting-Sim")
        self._controller.handle_start()
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Listen for keypresses, feed answers to the controller, and redraw."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)

            self._view_model.draw(self._screen, self._buffer)
            pygame.display.flip()
            self._clock.tick(60)

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Type into the current answer, submit it, replay, or quit."""
        if event.key == pygame.K_ESCAPE:
            self._running = False
        elif self._view_model.prompt:
            if event.key == pygame.K_RETURN:
                self._controller.handle_answer(self._buffer)
                self._buffer = ""
            elif event.key == pygame.K_BACKSPACE:
                self._buffer = self._buffer[:-1]
            elif event.unicode.isprintable():
                self._buffer += event.unicode
        elif event.key == pygame.K_RETURN:
            self._view_model.clear_messages()
            self._controller.handle_start()
