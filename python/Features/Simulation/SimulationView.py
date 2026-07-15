from Features.Simulation import (
    SimulationController,
    SimulationPresenter,
    SimulationInteractor,
    SimulationViewModel,
)


class SimulationView:
    """The view of the simulation feature to hold its GUI logic."""

    _controller: SimulationController
    _presenter: SimulationPresenter
    _interactor: SimulationInteractor
    _view_model: SimulationViewModel

    def __init__(
        self,
        controller: SimulationController,
        presenter: SimulationPresenter,
        interactor: SimulationInteractor,
        view_model: SimulationViewModel,
    ) -> None:
        """Create a SimulationView wired to <controller>, <presenter>,
        <interactor>, and rendering <view_model>."""
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._view_model = view_model
