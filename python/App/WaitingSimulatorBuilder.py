from App import ViewFacade
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

    def __init__(self) -> None:
        self.view_facade = ViewFacade(
            game_view_factory=self.build_game,
            simulation_view_factory=self.build_simulation,
        )

    def build_game(self) -> GameView:
        """Build a new GameView."""
        game_view_model = GameViewModel()
        game_presenter = GamePresenter(game_view_model)
        game_interactor = GameInteractor(
            dao=AccessWaitRules(),
            presenter=game_presenter,
        )
        game_controller = GameController(game_interactor)
        game_view_model.set_stations(game_controller.get_stations())
        game_view = GameView(
            controller=game_controller,
            presenter=game_presenter,
            interactor=game_interactor,
            view_model=game_view_model,
        )
        return game_view

    def build_simulation(self) -> SimulationView:
        """Build a new SimulationView."""
        sim_view_model = SimulationViewModel()
        sim_presenter = SimulationPresenter(sim_view_model)
        sim_interactor = SimulationInteractor(
            dao=AccessWaitRules(),
            presenter=sim_presenter,
        )
        sim_controller = SimulationController(sim_interactor)
        simulation_view = SimulationView(
            controller=sim_controller,
            presenter=sim_presenter,
            interactor=sim_interactor,
            view_model=sim_view_model,
        )
        return simulation_view
