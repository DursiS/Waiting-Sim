from App import ViewFacade, ViewModelFacade
from Data import AccessWaitRules
from Features.Game import (
    GameController,
    GameInteractor,
    GamePresenter,
    GameView,
    GameViewModel,
)
from Features.Simulation import (
    SimulationController,
    SimulationInteractor,
    SimulationPresenter,
    SimulationView,
    SimulationViewModel,
)


class WaitingSimulatorBuilder:
    """A waiting-simulator app to play it as a game or
    simulate as many trials as you like and see metrics about
    those trials."""

    view_facade: ViewFacade
    view_model_facade: ViewModelFacade

    def __init__(self) -> None:

        self.view_model_facade = ViewModelFacade(
            simulation_view_model=SimulationViewModel(),
        )
        self.view_facade = ViewFacade(
            self.view_model_facade,
            game_view_factory=self.build_game,
        )

    def build_game(self) -> GameView:
        """Build a new GameView."""
        game_presenter = GamePresenter()
        game_interactor = GameInteractor(
            dao=AccessWaitRules(),
            presenter=game_presenter,
        )
        game_controller = GameController(game_interactor)
        game_view_model = GameViewModel(game_controller.get_stations())
        game_view = GameView(
            controller=game_controller,
            presenter=game_presenter,
            interactor=game_interactor,
            view_model=game_view_model,
        )
        return game_view

    def build_simulator(self) -> SimulationView:
        """Build a new SimulationView."""
        sim_presenter = SimulationPresenter()
        sim_interactor = SimulationInteractor(
            dao=AccessWaitRules(),
            presenter=sim_presenter,
        )
        sim_controller = SimulationController(sim_interactor)
        sim_view_model = SimulationViewModel()
        simulation_view = SimulationView(
            controller=sim_controller,
            presenter=sim_presenter,
            interactor=sim_interactor,
            view_model=sim_view_model,
        )
        return simulation_view
