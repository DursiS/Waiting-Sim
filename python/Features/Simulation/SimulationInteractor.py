from dataclasses import dataclass

from Data import AccessWaitRulesInterface
from Features.Simulation import SimulationOutputBoundry
from Features.Simulation.SimulationInputBoundry import SimulationInputBoundry


class SimulationInteractor(SimulationInputBoundry):
    """Orchestrates simulation business logic."""

    _dao: AccessWaitRulesInterface
    _presenter: SimulationOutputBoundry

    def __init__(
        self, dao: AccessWaitRulesInterface, presenter: SimulationOutputBoundry
    ) -> None:
        """Create a SimulationInteractor using <dao> for wait rule data and
        <presenter> to report simulation results."""
        self._dao = dao
        self._presenter = presenter

    @dataclass
    class StepData:
        """Data collected from moving one station over."""

        station_from_id: int
        station_to_id: int
        rule: str
        wait_time: float
        step: int
        trial: int

    def _step(self, rand_arrival: bool) -> StepData:
        """Arrive randomly at a station, get on the first train that arrives
        and report the data in <data>."""
        raise NotImplementedError

    def _format_output_data(
        self, simulation_hist: list[list]
    ) -> dict[tuple[int, int], float]:
        """Digest raw StepData across trials and format it into
        a grid of just the essential information we need to present."""
        return {
            (0, 0): self._average_wait_time(simulation_hist),
            (0, 1): self._most_visited_station(simulation_hist),
            (0, 2): self._last_station_visited(simulation_hist),
            (1, 0): self._average_error(simulation_hist),
            (1, 1): self._average_versus_expected(simulation_hist),
            (1, 2): self._wait_time_distribution(simulation_hist),
        }

    def execute_simulation(
        self, trials: int, steps: int, rand_arrival: bool
    ) -> dict[tuple[int, int], float]:
        """Execute a new simulation."""
        self._presenter.say_executing_simulation(trials, steps, rand_arrival)

        simulation_history = []
        for i in range(trials):
            trial_history = []
            for j in range(steps):
                trial_history.append(self._step(rand_arrival))
            simulation_history.append(trial_history)

        self._presenter.say_done_trials()

        return self._format_output_data(simulation_history)
