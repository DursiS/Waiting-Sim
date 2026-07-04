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
            self._controller.handle_new_game()
        finally:
            self._busy = False

    # def on_trial_selected(self, event: tk.Event) -> None:
    #     """Action Listener for trial"""
    #     if self._busy:
    #         return
    #     self._busy = True
    #     try:
    #         self._controller.handle_trial()
    #     finally:
    #         self._busy = False
    #
    # def on_simulation_selected(self, event: tk.Event) -> None:
    #     """Action Listener for simulation"""
    #     if self._busy:
    #         return
    #     self._busy = True
    #     try:
    #         self._controller.handle_simulation()
    #     finally:
    #         self._busy = False


if __name__ == "__main__":

    view = View(
        controller=Controller(),
        presenter=Presenter(),
        interactor=Interactor(gateway=WaitRules(DEFAULT_STATIONS)),
    )
    # Nothing past this line will run until the app exits, keep above
