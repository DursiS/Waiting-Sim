import time

import numpy as np
from numpy import dtype, float64, ndarray
from scipy import integrate, stats
from scipy.stats._distn_infrastructure import rv_frozen

from .transition import Transition
from .world_builder import WorldBuilder
from .world_data_access_interface import WorldDataAccessInterface
from .player import Player
from .station import Station
from .world import World
from .step_data import StepData
from .metro_simulation_output_boundry import MetroSimulationOutputBoundry
from .metro_simulation_input_boundry import MetroSimulationInputBoundry

SIMULATION_NAME = "SIMULATION"
RESIDUAL_BATCH_SIZE = 8192
MAX_MATRIX_SIZE = 8


class MetroSimulationInteractor(MetroSimulationInputBoundry):
    """Orchestrates simulation business logic."""

    _dao: WorldDataAccessInterface
    _presenter: MetroSimulationOutputBoundry
    _residual_pool: dict[tuple, list[float]]
    _world_builder: WorldBuilder
    _transition: Transition

    def __init__(
        self, dao: WorldDataAccessInterface, presenter: MetroSimulationOutputBoundry
    ) -> None:
        """Create a MetroSimulationInteractor using <dao> for wait rule data and
        <presenter> to report simulation results."""
        self._dao = dao
        self._presenter = presenter
        self._residual_pool = {}
        self._world_builder = WorldBuilder()
        self._world = self._new_world()
        self._transition = Transition(self._world)

    def execute_simulation(self, trials: int, map_id: int) -> None:
        """Execute a new simulation on the map with id <map_id>: run <trials>
        walks from the spawn over the roads until each reaches the end."""
        self._dao.load_map(map_id)
        self._world = self._new_world()
        self._transition = Transition(self._world)
        spawn = self._spawn_station()
        player = Player(name=SIMULATION_NAME, starting_station=spawn)

        self._presenter.show_loading(True)
        runtime_start = time.perf_counter()
        sim_history = self._simulate(trials, player, spawn, False)
        rand_arrival_sim_history = self._simulate(trials, player, spawn, True)
        runtime_end = time.perf_counter()
        self._presenter.show_loading(False)

        output = self._get_simulation_output(
            sim_history,
            rand_arrival_sim_history,
            spawn,
            runtime_end - runtime_start,
        )
        self._presenter.show_results(output)

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
        """Return a world (with roads) built from the current map's records."""
        return self._world_builder.build_world(self._dao)

    def _get_simulation_output(
        self,
        simulation_hist: list[list[StepData]],
        rand_arrival_sim_history: list[list[StepData]],
        _from: Station,
        runtime: float,
    ) -> dict:
        """Digest raw StepData across trials and format it into
        a grid of just the essential information we need to present."""
        expected_wait_times = self._expected_wait_times()
        return {
            (0, 0): self._average_wait_time(simulation_hist),
            (0, 1): self._average_wait_time(rand_arrival_sim_history),
            (0, 2): round(runtime, 3),
            (1, 0): self._most_visited_station(simulation_hist),
            (1, 1): self._residual_squared_distribution(
                simulation_hist, expected_wait_times
            ),
            (2, 0): self._transition.n_step_transition_matrix(),
            (2, 1): self._fundamental_matrix(),
        }

    def _expected_wait_times(self) -> dict[int, float]:
        """Return each station's expected wait time on the loaded map, keyed by
        station id, from the station's own rule."""
        return {station.id: station.mean() for station in self._world.get_stations()}

    def _average_wait_time(self, simulation_hist: list[list[StepData]]) -> float:
        """Return the average wait-time per step across every trial."""
        gross_wait_time = 0.0
        num_steps = 0
        for trial in simulation_hist:
            for step_data in trial:
                gross_wait_time += step_data.wait_time
            num_steps += len(trial)
        return round(gross_wait_time / num_steps, 2) if num_steps else 0.0

    def _most_visited_station(self, simulation_hist: list[list[StepData]]) -> Station:
        """Return the most visited Station from the simulation."""
        count = {}
        stations = {}
        for trial in simulation_hist:
            for i, step_data in enumerate(trial):
                if i == 0:
                    if step_data.from_station.id not in count:
                        count[step_data.from_station.id] = 1
                        stations[step_data.from_station.id] = step_data.from_station
                    count[step_data.from_station.id] += 1
                    if step_data.to_station.id not in count:
                        count[step_data.to_station.id] = 1
                    count[step_data.to_station.id] += 1
                    stations[step_data.to_station.id] = step_data.to_station
                else:
                    if step_data.to_station.id not in count:
                        count[step_data.to_station.id] = 1
                    count[step_data.to_station.id] += 1
                    stations[step_data.from_station.id] = step_data.from_station

        return stations[max(count, key=count.get)]

    def _residual_squared_distribution(
        self,
        simulation_hist: list[list[StepData]],
        expected_wait_times: dict[int, float],
    ) -> tuple[float, float]:
        """Return the average error from theoretical E_t and error std. dev
        assuming no random_arrival"""
        errors = []
        for trial in simulation_hist:
            for step_data in trial:
                E_t = expected_wait_times[step_data.to_station.id]
                errors.append((step_data.wait_time - E_t) ** 2)

        errors = np.array(errors)
        errors_squared = errors**2
        mu = errors.mean()
        std = errors_squared.mean() - mu**2
        return mu, std

    def _simulate(
        self, trials: int, player: Player, spawn: Station, rand_arrival: bool
    ) -> list[list[StepData]]:
        """Run <trials> walks from <spawn> over the roads until each reaches the
        end, returning the per-step data of every trial."""
        simulation_history = []
        for i in range(trials):
            player.station = spawn
            trial_history = []
            step_i = 0
            while not player.station.end:
                trial_history.append(self._step(rand_arrival, player, step_i, i))
                step_i += 1
            simulation_history.append(trial_history)
        return simulation_history

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self._dao.map_ids()

    def _spawn_station(self) -> Station:
        """Return the map's start station, the source of the directed graph."""
        return self._world.starting_station()

    def _distances_from(self, start_id: int) -> dict[int, int]:
        """Return the step distance from <start_id> to every
        reachable station."""
        distances = {start_id: 0}
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            station = self._world.get_station_by_id(current)
            for neighbour in self._world.adjacent_stations(station):
                if neighbour.id not in distances:
                    distances[neighbour.id] = distances[current] + 1
                    queue.append(neighbour.id)
        return distances

    def _step(
        self, rand_arrival: bool, player: Player, step_i: int, trial_i: int
    ) -> StepData:
        """Arrive at a station, get on the first train that arrives and report
        the data in <data>. With <rand_arrival> the passenger arrives at a
        uniformly random moment, so each train's wait is its length-biased
        residual rather than a full sampled interval."""
        from_station = player.station
        times = []
        for road in self._world.roads_from(from_station):
            neighbour = self._world.get_station_by_id(road.to_id())
            if rand_arrival:
                seconds = self._random_arrival_wait(
                    self._dao.get_record(neighbour.id)["rule"]
                )
            else:
                seconds = self._dao.sample_rule(neighbour.id)
            times.append((neighbour, seconds))

        destination, fastest = min(times, key=lambda pair: pair[1])
        player.station = destination

        return StepData(
            from_station=from_station,
            to_station=destination,
            wait_time=fastest,
            step_i=step_i,
            trial_i=trial_i,
        )

    def _random_arrival_wait(self, rule: rv_frozen) -> float:
        """Return one length-biased residual wait for <rule>, served from a
        vectorized batch cached per distribution so scipy's per-sample overhead
        is paid once a batch rather than once a wait."""
        key = (rule.dist.name, rule.args, tuple(sorted(rule.kwds.items())))
        pool = self._residual_pool.get(key)
        if not pool:
            pool = self._draw_residual_batch(rule)
            self._residual_pool[key] = pool
        return pool.pop()

    def _draw_residual_batch(self, rule: rv_frozen) -> list[float]:
        """Draw a batch of length-biased waits at once, then wait a
        uniform fraction of the kept gap."""
        upper = float(rule.ppf(1 - 1e-9))
        residuals: list[float] = []
        while not residuals:
            gaps = rule.rvs(size=RESIDUAL_BATCH_SIZE).astype(float)
            kept = gaps[np.random.uniform(0, upper, gaps.size) <= gaps]
            residuals = np.random.uniform(0, kept).tolist()
        return residuals

    def _fundamental_matrix(self) -> tuple[np.ndarray, list[Station]]:
        """Return (N, transient) with N[i][j] = expected visits to transient j
        before reaching the end, starting from state i."""
        return self._transition.fundamental_matrix()

    def _ids_to_stations(self) -> dict[int, Station]:
        """Return the loaded map's stations keyed by their id."""
        return {station.id: station for station in self._world.get_stations()}

    def _n_step_transition_matrix(
        self, _from: Station, _to: Station, n: int = 1
    ) -> ndarray[tuple[int, int], dtype[float64]]:
        """Return the probability of being at <_to> within <n> steps
        starting at <_from>."""
        return self._transition.n_step_transition_matrix(n)
