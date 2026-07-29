import random
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from numpy import dtype, float64, ndarray
from scipy import integrate, stats
from scipy.stats._distn_infrastructure import rv_frozen

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

    def _probability_faster_wait_time(
        self, station1_id: int, station2_id: int
    ) -> float:
        """Return the probability station1's train will arrive
        before station2's."""
        station1 = self._world.get_station_by_id(station1_id)
        station2 = self._world.get_station_by_id(station2_id)
        return self._probability_is_fastest(station1.rule, station2.rule)

    def _probability_is_fastest(self, rule_j: rv_frozen, others: list[rv_frozen]) -> float:
        """P(X_j < every rule in <others>) by conditioning on X_j = t,
         then the survival probabilities multiply."""
        if self._is_discrete(rule_j):
            return float(sum(rule_j.pmf(t) * np.prod([r.sf(t) for r in others])
                             for t in self._discrete_support(rule_j)))
        lower, upper = self._continuous_bounds(rule_j)
        return float(integrate.quad(
            lambda t: rule_j.pdf(t) * np.prod([r.sf(t) for r in others]), lower, upper)[0])

    def _fundamental_matrix(self) -> tuple[np.ndarray, list[Station]]:
        """Return (N, transient) with N[i][j] = expected visits to transient j
        before reaching the end, starting from i."""
        transient = [s for s in self._world.get_stations() if not s.end]
        index = {s.id: k for k, s in enumerate(transient)}
        Q = np.zeros((len(transient), len(transient)))
        for s in transient:
            neighbours = self._world.adjacent_stations(s)
            rules = [nb.rule for nb in neighbours]
            for k, nb in enumerate(neighbours):
                if nb.id in index:
                    Q[index[s.id], index[nb.id]] = self._probability_is_fastest(
                        rules[k], rules[:k] + rules[k + 1:])
        return np.linalg.inv(np.eye(len(transient)) - Q), transient

    def _is_discrete(self, rule: rv_frozen) -> bool:
        """Return whether the frozen distribution <rule> is discrete."""
        return isinstance(rule.dist, stats.rv_discrete)

    def _discrete_support(self, rule: rv_frozen) -> range:
        """Return the integer support of discrete <rule>, capped at a far
        quantile where it is unbounded."""
        low, high = rule.support()
        if not np.isfinite(low):
            low = rule.ppf(1e-12)
        if not np.isfinite(high):
            high = rule.ppf(1 - 1e-12)
        return range(int(low), int(high) + 1)

    def _continuous_bounds(self, rule: rv_frozen) -> tuple[float, float]:
        """Return practical integration limits spanning <rule>'s density."""
        return float(rule.ppf(1e-12)), float(rule.ppf(1 - 1e-12))

    def _n_step_transition_matrix(
        self, _from: Station, n: int
    ) -> ndarray[tuple[int], dtype[float64]]:
        """Return the probability of being at <_to> within <n> steps
        starting at <_from>."""
        MAX_SIZE = 7
        i = _from.id
        Q = np.zeros(MAX_SIZE)
        adjacent_ids = [station.id for station in self._world.adjacent_stations(_from)]

        for j in range(0, MAX_SIZE):
            if j in adjacent_ids:
                Q[i, j] = np.prod(
                    [self._probability_faster_wait_time(i, j) for j in adjacent_ids]
                )
        return np.linalg.matrix_power(Q, n)

    def
