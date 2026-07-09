import sys

from Adapters import Controller, Presenter
from Framework import DAO
from Framework.ViewModel import ViewModel
from UseCases.Interactor import Interactor
import tkinter as tk


class View:
    """The view of the app to hold all GUI logic."""

    _controller: Controller
    _presenter: Presenter
    _interactor: Interactor
    _busy: bool

    def __init__(
        self, controller: Controller, presenter: Presenter, interactor: Interactor
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._busy = False

        self.root = tk.Tk()
        self.root.bind("p", self.on_play)
        self.root.bind("q", self.on_quit)
        self.root.bind("c", self.on_continue)
        self.root.mainloop()

    def new_controller(self) -> Controller:
        """Return a single new controller."""
        presenter = Presenter()
        interactor = Interactor(
            dao=DAO(),
            presenter=presenter,
        )
        return Controller(interactor)

    def on_play(self, event: tk.Event) -> None:  # action listener
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
            view = ViewModel(stations, curr_station, messages)
            view.run()
        finally:
            self._busy = False

    def on_quit(self, event: tk.Event) -> None:
        """Action Listener to quit"""
        if self._busy:
            return
        self._busy = True
        try:
            sys.exit()
        finally:
            self._busy = False

    def on_continue(self, event: tk.Event) -> None:
        """Action Listener to quit"""
        if self._busy:
            return
        self._busy = True
        try:
            controller = self.new_controller()
            stations, curr_station, messages = controller.handle_continue_game()
            view = ViewModel(stations, curr_station, messages)
            view.run()
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
        dai=DAO(),
        presenter=presenter,
    )
    view = View(
        controller=Controller(interactor),
        presenter=presenter,
        interactor=interactor,
    )
    # Nothing past this line will run until the app exits, keep above
