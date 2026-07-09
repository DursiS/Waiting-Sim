import pygame

from Adapters import Controller, Presenter
from Framework import DAO
from Framework.ViewModel import BG_COLOR, ViewModel
from UseCases.Interactor import Interactor


DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 400


class View:
    """The view of the app to hold all GUI logic."""

    _controller: Controller
    _presenter: Presenter
    _interactor: Interactor
    _view_model: ViewModel | None
    _running: bool
    _busy: bool

    def __init__(
        self, controller: Controller, presenter: Presenter, interactor: Interactor
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._view_model = None
        self._running = True
        self._busy = False

        pygame.init()
        self._screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT))
        pygame.display.set_caption("Waiting Sim")
        self.keydown_loop()
        pygame.quit()

    def new_controller(self) -> Controller:
        """Return a single new controller."""
        presenter = Presenter()
        interactor = Interactor(
            dao=DAO(),
            presenter=presenter,
        )
        return Controller(interactor)

    def keydown_loop(self) -> None:
        """Listen for keypresses, do the according actions, and redraw."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.on_play()
                    elif event.key == pygame.K_q:
                        self.on_quit()
                    elif event.key == pygame.K_c:
                        self.on_continue()

            if self._view_model is not None:
                self._view_model.draw(self._screen)
            else:
                self._screen.fill(BG_COLOR)
            pygame.display.flip()

    def _show(self, stations, curr_station, messages) -> None:
        """Build a ViewModel from the latest turn and resize the window to fit it."""
        self._view_model = ViewModel(stations, curr_station, messages)
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )

    def on_play(self) -> None:  # action listener
        """Action Listener to play"""
        if self._busy:
            return
        self._busy = True
        try:
            name = self.prompt_for_name()
            station_id = self.prompt_for_station()

            controller = self.new_controller()
            stations, curr_station, messages = controller.handle_new_game(
                name, station_id
            )
            self._show(stations, curr_station, messages)
        finally:
            self._busy = False

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
            controller = self.new_controller()
            stations, curr_station, messages = controller.handle_continue_game()
            self._show(stations, curr_station, messages)
        finally:
            self._busy = False

    def prompt_for_name(self) -> str:
        """Prompt for a player's name."""
        try:
            result = input("Name: ")
        except ValueError:
            result = self.prompt_for_name()
        return result

    def prompt_for_station(self) -> int:
        """Prompt for a starting station id."""
        try:
            result = int(input("Starting station id: "))
        except ValueError:
            result = self.prompt_for_station()
        return result

    def prompt_travel_choice(self) -> int:
        """Prompt for the next station id to travel to."""
        try:
            result = int(input("Travel to station id: "))
        except ValueError:
            result = self.prompt_travel_choice()
        return result


if __name__ == "__main__":

    presenter = Presenter()
    interactor = Interactor(
        dao=DAO(),
        presenter=presenter,
    )
    view = View(
        controller=Controller(interactor),
        presenter=presenter,
        interactor=interactor,
    )
    # Nothing past this line will run until the app exits, keep above
