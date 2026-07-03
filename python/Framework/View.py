from Adapters import Controller, Presenter
from Framework import WaitRules
from Framework.Database import DEFAULT_STATIONS
from UseCases.Interactor import Interactor


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

    def workflow(self):
        """View methods workflow:

        Controller waits for action
        -> calls Interactor
        -> which calls Presenter to display
        """
        raise NotImplementedError

    def on_play_selected(self) -> None:  # action listener
        """Action Listener to play"""
        if self._busy:
            return
        self._busy = True
        try:
            self._controller.handle_new_game()
        finally:
            self._busy = False

    def on_trial_selected(self) -> None:
        """Action Listener for trial"""
        if self._busy:
            return
        self._busy = True
        try:
            self._controller.handle_trial()
        finally:
            self._busy = False

    def on_simulation_selected(self) -> None:
        """Action Listener for simulation"""
        if self._busy:
            return
        self._busy = True
        try:
            self._controller.handle_simulation()
        finally:
            self._busy = False


if __name__ == "__main__":
    view = View(
        controller=Controller(),
        presenter=Presenter(),
        interactor=Interactor(gateway=WaitRules(DEFAULT_STATIONS)),
    )
