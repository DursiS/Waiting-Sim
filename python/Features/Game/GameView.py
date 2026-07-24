import pygame

from Features.Game import (
    GameController,
    GamePresenter,
    GameViewModel,
    GameInteractor,
)


INPUT_BG_COLOR = (0, 0, 0)
INPUT_TEXT_COLOR = (255, 255, 255)


class GameView:
    """The view of the app to hold all GUI logic."""

    _controller: GameController
    _presenter: GamePresenter
    _interactor: GameInteractor
    _view_model: GameViewModel
    _running: bool
    _busy: bool
    _input_mode: str | None
    _input_buffer: str
    _pending_name: str
    _pending_station_id: int

    def __init__(
        self,
        controller: GameController,
        presenter: GamePresenter,
        interactor: GameInteractor,
        view_model: GameViewModel,
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._running = True
        self._busy = False
        self._input_mode = None
        self._input_buffer = ""
        self._pending_name = ""
        self._pending_station_id = 0

        self._view_model = view_model
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Waiting-Sim")
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Listen for keypresses, do the according actions, and redraw."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    if self._input_mode is not None:
                        self._handle_text_input(event)
                    elif event.key == pygame.K_p:
                        self.on_play()
                    elif event.key == pygame.K_q:
                        self.on_quit()
                    elif event.key == pygame.K_c:
                        self.on_continue()

            self._view_model.draw(self._screen)
            if self._input_mode is not None:
                self._draw_input_prompt()
            pygame.display.flip()

    def _draw_input_prompt(self) -> None:
        """Draw the field currently being typed into over the current view."""
        labels = {
            "name": "Name",
            "station": "Starting station id",
            "arrival": "Random arrival? (y/n)",
        }
        label = labels.get(self._input_mode, "")
        font = pygame.font.SysFont(None, 28)
        text = font.render(f"{label}: {self._input_buffer}_", True, INPUT_TEXT_COLOR)
        box = text.get_rect(topleft=(20, 20)).inflate(20, 10)
        pygame.draw.rect(self._screen, INPUT_BG_COLOR, box)
        self._screen.blit(text, (box.x + 10, box.y + 5))

    def _handle_text_input(self, event: pygame.event.Event) -> None:
        """Handle a keypress while a field is being typed into."""
        if event.key == pygame.K_RETURN:
            self._submit_input()
        elif event.key == pygame.K_BACKSPACE:
            self._input_buffer = self._input_buffer[:-1]
        elif event.unicode.isprintable():
            self._input_buffer += event.unicode

    def _submit_input(self) -> None:
        """Advance the input flow when the field
        being typed into is submitted."""
        if self._input_mode == "name":
            self._pending_name = self._input_buffer or "Player1"
            self._input_mode = "station"
            self._input_buffer = ""
        elif self._input_mode == "station":
            if not self._input_buffer.isdigit():
                return
            self._pending_station_id = int(self._input_buffer)
            self._input_mode = "arrival"
            self._input_buffer = ""
        elif self._input_mode == "arrival":
            if self._input_buffer.lower() not in ("y", "n"):
                return
            rand_arrival = self._input_buffer.lower() == "y"
            self._input_mode = None
            self._input_buffer = ""

            self._controller.handle_new_game(
                self._pending_name, self._pending_station_id, rand_arrival
            )

    def on_play(self) -> None:  # action listener
        """Action Listener to play"""
        if self._busy:
            return
        self._input_mode = "name"
        self._input_buffer = ""

    def on_quit(self) -> None:
        """Action Listener to quit"""
        if self._busy:
            return
        self._busy = True
        try:
            self._running = False
        finally:
            self._busy = False

    def on_continue(self) -> None:
        """Action Listener to continue"""
        if self._busy:
            return
        self._busy = True
        try:
            self._controller.handle_continue_game()
        finally:
            self._busy = False
