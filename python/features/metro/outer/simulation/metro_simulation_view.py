import threading
import traceback
from typing import Callable

import pygame

from app import audio
from .metro_simulation_controller import MetroSimulationController
from .metro_simulation_presenter import MetroSimulationPresenter
from .metro_simulation_view_model import MetroSimulationViewModel
from features.metro.inner import MetroSimulationInteractor


class MetroSimulationView:
    """The simulation screen. Given a request from the option-selection screen,
    it runs the trials in a background thread while the draw loop streams the
    presenter's results, then Q returns to the option-selection screen."""

    _name: str
    _map_id: int
    _trials: int
    _controller: MetroSimulationController
    _presenter: MetroSimulationPresenter
    _interactor: MetroSimulationInteractor
    _view_model: MetroSimulationViewModel
    _running: bool
    _busy: bool

    def __init__(
        self,
        name: str,
        map_id: int,
        trials: int,
        controller: MetroSimulationController,
        presenter: MetroSimulationPresenter,
        interactor: MetroSimulationInteractor,
        view_model: MetroSimulationViewModel,
    ) -> None:
        self._name = name
        self._map_id = map_id
        self._trials = trials
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
        self._start_simulation()
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Listen for keypresses and redraw the results each frame."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_q,
                    pygame.K_ESCAPE,
                ):
                    self.on_quit()

            if self._screen.get_size() != (
                self._view_model.width,
                self._view_model.height,
            ):
                self._screen = pygame.display.set_mode(
                    (self._view_model.width, self._view_model.height)
                )
            self._view_model.draw(self._screen)
            pygame.display.flip()
            self._clock.tick(60)

    def _start_simulation(self) -> None:
        """Run the requested simulation in the background."""
        self._run_in_background(
            lambda: self._controller.handle_simulation(
                self._name, self._map_id, self._trials
            )
        )

    def _run_in_background(self, action: Callable[[], None]) -> None:
        """Run <action> in a daemon thread so the draw loop keeps streaming the
        presenter's updates instead of freezing on the run."""
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

    def on_quit(self) -> None:
        """Leave the simulation screen back to the option-selection screen."""
        audio.play("quit")
        self._running = False
