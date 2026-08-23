from app.view_facade import ViewFacade
from features.metro.inner import WorldDataAccess
from features.metro.inner import MetroInteractor
from features.metro.outer.play import (
    MetroController,
    MetroPresenter,
    MetroView,
    MetroViewModel,
)
from features.metro.inner import MetroSimulationInteractor
from features.metro.outer.simulation import (
    MetroSimulationController,
    MetroSimulationPresenter,
    MetroSimulationView,
    MetroSimulationViewModel,
)
from features.flying.outer import (
    FlyingController,
    FlyingPresenter,
    FlyingView,
    FlyingViewModel,
)


class WaitingSimulatorBuilder:
    """A waiting-simulator app to play it as a game or
    simulate as many trials as you like and see metrics about
    those trials."""

    view_facade: ViewFacade

    def __init__(self) -> None:
        self.view_facade = ViewFacade(
            metro_view_factory=self.build_metro,
            simulation_view_factory=self.build_simulation,
            flying_view_factory=self.build_flying,
        )

    def build_flying(self) -> FlyingView:
        """Build a new FlyingView that simulates and rolls out a bird's flight."""
        flying_view_model = FlyingViewModel()
        flying_presenter = FlyingPresenter(flying_view_model)
        flying_controller = FlyingController(flying_presenter)
        return FlyingView(
            controller=flying_controller,
            view_model=flying_view_model,
        )

    def build_metro(self) -> MetroView:
        """Build a new MetroView; it fills the map itself when a game starts."""
        metro_view_model = MetroViewModel()
        metro_presenter = MetroPresenter(metro_view_model)
        metro_interactor = MetroInteractor(
            dao=WorldDataAccess(),
            presenter=metro_presenter,
        )
        metro_controller = MetroController(metro_interactor)
        metro_view = MetroView(
            controller=metro_controller,
            presenter=metro_presenter,
            interactor=metro_interactor,
            view_model=metro_view_model,
        )
        return metro_view

    def build_simulation(self) -> MetroSimulationView:
        """Build a new MetroSimulationView."""
        sim_view_model = MetroSimulationViewModel()
        sim_presenter = MetroSimulationPresenter(sim_view_model)
        sim_interactor = MetroSimulationInteractor(
            dao=WorldDataAccess(),
            presenter=sim_presenter,
        )
        sim_controller = MetroSimulationController(sim_interactor)
        simulation_view = MetroSimulationView(
            controller=sim_controller,
            presenter=sim_presenter,
            interactor=sim_interactor,
            view_model=sim_view_model,
        )
        return simulation_view
