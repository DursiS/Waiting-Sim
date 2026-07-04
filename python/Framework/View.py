from Adapters import Controller, Presenter
from Framework import WaitRules
from Framework.Database import DEFAULT_STATIONS
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
        self.root.bind("p", self.on_play_selected)
        # self.root.bind("t", self.on_trial_selected)
        # self.root.bind("s", self.on_simulation_selected)
        self.root.mainloop()

    def workflow(self):
        """View methods workflow:

        Controller waits for action
        -> calls Interactor
        -> which calls Presenter to display
        """
        raise NotImplementedError

    def on_play_selected(self, event: tk.Event) -> None:  # action listener
        """Action Listener to play"""
        if self._busy:
            return
        self._busy = True
        try:
            name = self.prompt_for_name()
            station_id = self.prompt_for_station()
            self._controller.handle_new_game(name, station_id)
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

    view = View(
        controller=Controller(),
        presenter=Presenter(),
        interactor=Interactor(gateway=WaitRules(DEFAULT_STATIONS)),
    )
    # Nothing past this line will run until the app exits, keep above
