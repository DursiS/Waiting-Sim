from Data.AccessWaitRules import AccessWaitRules
from App.View import View
from Features.Game.GameController import GameController
from Features.Game.GamePresenter import GamePresenter
from Features.Game.GameInteractor import GameInteractor


if __name__ == "__main__":

    presenter = GamePresenter()
    interactor = GameInteractor(
        dao=AccessWaitRules(),
        presenter=presenter,
    )
    view = View(
        controller=GameController(interactor),
        presenter=presenter,
        interactor=interactor,
    )
    # Nothing past this line will run until the app exits, keep above
