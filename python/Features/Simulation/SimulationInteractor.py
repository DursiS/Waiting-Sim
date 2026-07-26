import random
from dataclasses import dataclass
from datetime import timedelta

from Data import AccessWaitRulesInterface
from Entities import Player, Station
from Entities.StepData import StepData
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

    def _format_output_data(
        self, simulation_hist: list[list]
    ) -> dict[tuple[int, int], float]:
        """Digest raw StepData across trials and format it into
        a grid of just the essential information we need to present."""
        return {
            (0, 0): self._average_wait_time(simulation_hist),
            (0, 1): self._most_visited_station(simulation_hist),
            (0, 2): self._last_station_distribution(simulation_hist),
            (1, 0): self._average_error_from_mean(simulation_hist),
            (1, 1): self._average_random_wait_time(simulation_hist),
        }

    def execute_simulation(
        self, trials: int, steps: int, rand_arrival: bool
    ) -> dict[tuple[int, int], float]:
        """Execute a new simulation."""
        self._presenter.clear_messages()
        self._presenter.say_executing_simulation(trials, steps, rand_arrival)

        simulation_history = []
        for i in range(trials):
            trial_history = []
            for j in range(steps):
                trial_history.append(self._step(rand_arrival, j, i))
            simulation_history.append(trial_history)

        self._presenter.say_done_trials()

        return self._format_output_data(simulation_history)

    def _step(
        self, player: Player, rand_arrival: bool, step_i: int, trial_i: int
    ) -> StepData:
        """Arrive randomly at a station, get on the first train that arrives
        and report the data in <data>."""
        directions = ("N", "S", "W", "E")
        times = []
        for record in self._dao.get_records():
            train_arrival = self._dao.sample_rule(record["id"])
            if rand_arrival:
                player_arrival = random.uniform(0, train_arrival) / 2
                while train_arrival < player_arrival:
                    train_arrival = self._dao.sample_rule(record["id"])
                train_arrival -= player_arrival
            else:
                times.append(self._dao.sample_rule(record["id"]))

        while min(times) != 0:
            times[times.index(min(times))] = 10**10
        fastest_index = times.index(min(times))
        fastest = times[fastest_index]

        destination = directions[fastest_index].toString()
        player.station = getattr(player.station, destination)

        return StepData(
            from_station=player.station,
            to_station=getattr(player.station, destination),
            wait_time=fastest,
            step_i=step_i,
            trial_i=trial_i,
        )
