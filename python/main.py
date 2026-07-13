from Framework import AccessWaitRules
from Framework.View import View
from Interface_Adapters import GameController, GamePresenter
from UseCases.Game.GameInteractor import GameInteractor


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
