import threading
from typing import Callable

import pygame

import Audio
from Features.Simulation import (
    SimulationController,
    SimulationPresenter,
    SimulationInteractor,
    SimulationViewModel,
)


INPUT_BG_COLOR = (0, 0, 0)
INPUT_TEXT_COLOR = (255, 255, 255)


class SimulationView:
    """The view of the simulation feature to hold its GUI logic."""

    _controller: SimulationController
    _presenter: SimulationPresenter
    _interactor: SimulationInteractor
    _view_model: SimulationViewModel
    _running: bool
    _busy: bool
    _input_mode: str | None
    _input_buffer: str
    _pending_name: str
    _pending_map_id: int
    _pending_trials: int
    _pending_steps: int

    def __init__(
        self,
        controller: SimulationController,
        presenter: SimulationPresenter,
        interactor: SimulationInteractor,
        view_model: SimulationViewModel,
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._running = True
        self._busy = False
        self._input_mode = None
        self._input_buffer = ""
        self._pending_name = ""
        self._pending_map_id = 0
        self._pending_trials = 0
        self._pending_steps = 0

        self._view_model = view_model
        self._clock = pygame.time.Clock()
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
                        self.on_simulate()
                    elif event.key == pygame.K_q:
                        self.on_quit()

            if self._screen.get_size() != (
                self._view_model.width,
                self._view_model.height,
            ):
                self._screen = pygame.display.set_mode(
                    (self._view_model.width, self._view_model.height)
                )
            self._view_model.draw(self._screen)
            if self._input_mode is not None:
                self._draw_input_prompt()
            pygame.display.flip()
            self._clock.tick(60)

    def _run_in_background(self, action: Callable[[], None]) -> None:
        """Run <action> in a daemon thread so the draw loop keeps streaming
        the presenter's updates in real time instead of freezing on the run."""
        if self._busy:
            return
        self._busy = True

        def worker() -> None:
            try:
                action()
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _draw_input_prompt(self) -> None:
        """Draw the field currently being typed into over the current view."""
        if self._input_mode == "map":
            ids = "/".join(str(m) for m in self._controller.get_map_ids())
            label = f"Map id ({ids})"
        else:
            label = {
                "name": "Name",
                "trials": "Number of trials",
                "steps": "Steps per trial",
            }.get(self._input_mode, "")
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
        """Advance the input flow when the field being typed into is submitted."""
        if self._input_mode == "name":
            self._pending_name = self._input_buffer or "Player1"
            self._input_mode = "map"
            self._input_buffer = ""
        elif self._input_mode == "map":
            if not self._input_buffer.isdigit():
                Audio.play("error")
                return
            if int(self._input_buffer) not in self._controller.get_map_ids():
                Audio.play("error")
                return
            self._pending_map_id = int(self._input_buffer)
            self._input_mode = "trials"
            self._input_buffer = ""
        elif self._input_mode == "trials":
            if not self._input_buffer.isdigit() or int(self._input_buffer) == 0:
                Audio.play("error")
                return
            self._pending_trials = int(self._input_buffer)
            self._input_mode = "steps"
            self._input_buffer = ""
        elif self._input_mode == "steps":
            if not self._input_buffer.isdigit() or int(self._input_buffer) == 0:
                Audio.play("error")
                return
            self._pending_steps = int(self._input_buffer)
            self._input_mode = None
            self._input_buffer = ""

            self._run_in_background(
                lambda: self._controller.handle_simulation(
                    self._pending_name,
                    self._pending_map_id,
                    self._pending_trials,
                    self._pending_steps,
                )
            )

    def on_simulate(self) -> None:
        """Action Listener to start a new simulation"""
        if self._busy:
            return
        self._input_mode = "name"
        self._input_buffer = ""

    def on_quit(self) -> None:
        """Action Listener to quit"""
        self._running = False
