import random
from dataclasses import dataclass
from datetime import timedelta

from Data import AccessWaitRulesInterface
from Entities import Player, Station, World
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
        self._world = self._new_world()

    def _instantiate_station(self, record: dict) -> Station:
        """Build a Station from the wait rules entry <record>."""
        station = Station(
            name=record["name"],
            rule_name=record["rule_name"],
            rule=record["rule"],
            times_visited=record["times_visited"],
            waited_at=record["waited_at"],
            coordinates=record["coordinates"],
            end=record["end"],
        )
        station.set_id(record["id"])
        return station

    def _new_world(self) -> World:
        """Return a world built from the current map's station records."""
        world = World()
        world.add_stations(
            [self._instantiate_station(record) for record in self._dao.get_records()]
        )
        return world

    def _output_grid_data(
        self, simulation_hist: list[list]
    ) -> dict[tuple[int, int], float]:
        """Digest raw StepData across trials and format it into
        a grid of just the essential information we need to present."""
        return {
            (0, 0): self._average_wait_time(simulation_hist),
            (0, 1): self._most_visited_station(simulation_hist),
            # (0, 2): self._last_station_distribution(simulation_hist),
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
        times = []
        for neighbour in self._world.adjacent_stations(player.station):
            seconds = self._dao.sample_rule(neighbour.id)
            if rand_arrival:
                arrival = random.uniform(0, seconds) / 2
                while seconds < arrival:
                    seconds = self._dao.sample_rule(neighbour.id)
                seconds -= arrival
            times.append((neighbour, seconds))

        while min(times) == 0:
            times[times.index(min(times))] = 10**10
        fastest_index = times.index(min(times))
        fastest = times[fastest_index]

        directions = ("N", "E", "S", "W")
        destination = directions[fastest_index].toString()
        player.station = self._world.neighbor(player.station, destination)

        return StepData(
            from_station=player.station,
            to_station=getattr(player.station, destination),
            wait_time=fastest,
            step_i=step_i,
            trial_i=trial_i,
        )

    def n_step_transition_p(self, _from: Station, _to: Station, n: int) -> None:
        """Return the probability of being at <_to> within <n> steps
        starting at <_from>."""
        raise NotImplementedError
