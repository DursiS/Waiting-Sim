from app.view_facade import ViewFacade
from features.metro.inner import WorldDataAccess
from features.metro.inner import MetroInteractor
from features.metro.inner import MetroInputData
from features.metro.inner import Player
from features.metro.inner import MetroOptionSelectionInteractor
from features.metro.outer.play import (
    MetroController,
    MetroPresenter,
    MetroView,
    MetroViewModel,
)
from features.metro.outer.selection import (
    MetroOptionSelectionController,
    MetroOptionSelectionView,
    MetroOptionSelectionViewModel,
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
            metro_view_factory=self.build_metro_option_selection,
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

    def build_metro_option_selection(self) -> MetroOptionSelectionView:
        """Build the Metro entry screen where the player picks a mode and inputs,
        then launches the chosen game with that request."""
        dao = WorldDataAccess()
        controller = MetroOptionSelectionController(MetroOptionSelectionInteractor(dao))
        view_model = MetroOptionSelectionViewModel(dao.map_ids(), Player(None).balance)
        return MetroOptionSelectionView(
            controller=controller,
            view_model=view_model,
            play_view_factory=self.build_metro_play,
        )

    def build_metro_play(self, request: MetroInputData) -> MetroView:
        """Build a MetroView that immediately plays out <request>."""
        metro_view_model = MetroViewModel()
        metro_presenter = MetroPresenter(metro_view_model)
        metro_interactor = MetroInteractor(
            dao=WorldDataAccess(),
            presenter=metro_presenter,
        )
        metro_controller = MetroController(metro_interactor)
        return MetroView(
            request=request,
            controller=metro_controller,
            presenter=metro_presenter,
            interactor=metro_interactor,
            view_model=metro_view_model,
        )
