from Data import AccessWaitRulesInterface
from Features.Simulation import SimulationPresenter
from Features.Simulation.SimulationInputBoundry import SimulationInputBoundry


class SimulationInteractor(SimulationInputBoundry):
    """Orchestrates simulation business logic."""

    _dao: AccessWaitRulesInterface
    _presenter: SimulationPresenter

    def __init__(
        self, dao: AccessWaitRulesInterface, presenter: SimulationPresenter
    ) -> None:
        """Create a SimulationInteractor using <dao> for wait rule data and
        <presenter> to report simulation results."""
        self._dao = dao
        self._presenter = presenter

    def execute_simulation(self, trials: int, steps: int, rand_arrival: bool) -> None:
        """Execute a new simulation."""
