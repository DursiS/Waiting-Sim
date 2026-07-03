from Adapters import Controller, Presenter
from Framework import WaitRules
from UseCases.Interactor import Interactor


class View:
    """The view of the app to hold all GUI logic."""

    controller: Controller
    presenter: Presenter
    interactor: Interactor

    def __init__(
        self, controller: Controller, presenter: Presenter, interactor: Interactor
    ) -> None:
        self.controller = controller
        self.presenter = presenter
        self.interactor = interactor

    def workflow(self):
        """View methods workflow:

        Controller waits for action
        -> calls Interactor
        -> which calls Presenter to display
        """
        raise NotImplementedError




if __name__ == "__main__":
    view = View(
        controller=Controller(),
        presenter=Presenter(),
        interactor=Interactor(gateway=WaitRules()),
    )
