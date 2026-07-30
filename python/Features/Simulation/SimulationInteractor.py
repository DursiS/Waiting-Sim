import numpy as np
from numpy import dtype, float64, ndarray
from scipy import integrate, stats
from scipy.stats._distn_infrastructure import rv_frozen

from Data import AccessWaitRulesInterface
from Entities import Player, Station, World
from Entities.StepData import StepData
from Features.Simulation import SimulationOutputBoundry
from Features.Simulation.SimulationInputBoundry import SimulationInputBoundry

SIMULATION_NAME = "SIMULATION"
RESIDUAL_BATCH_SIZE = 8192


class SimulationInteractor(SimulationInputBoundry):
    """Orchestrates simulation business logic."""

    _dao: AccessWaitRulesInterface
    _presenter: SimulationOutputBoundry
    _residual_pool: dict[tuple, list[float]]

    def __init__(
        self, dao: AccessWaitRulesInterface, presenter: SimulationOutputBoundry
    ) -> None:
        """Create a SimulationInteractor using <dao> for wait rule data and
        <presenter> to report simulation results."""
        self._dao = dao
        self._presenter = presenter
        self._residual_pool = {}
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
        self,
        simulation_hist: list[list[StepData]],
        rand_arrival_sim_history: list[list[StepData]],
        steps: int,
        _from: Station,
    ) -> dict:
        """Digest raw StepData across trials and format it into
        a grid of just the essential information we need to present."""
        expected_wait_times = self._expected_wait_times()
        return {
            (0, 0): self._average_wait_time(simulation_hist, steps),
            (0, 1): self._average_wait_time(rand_arrival_sim_history, steps),
            (1, 0): self._most_visited_station(simulation_hist),
            (1, 1): self._residual_squared_distribution(
                simulation_hist, expected_wait_times
            ),
            (2, 0): self._n_step_transition_matrix(_from, steps),
            (2, 1): self._fundamental_matrix(),
        }

    def _expected_wait_times(self) -> dict[int, float]:
        """Return each station's expected wait time on the loaded map, keyed by
        station id, from the station's own rule."""
        return {station.id: station.E_t() for station in self._world.get_stations()}

    def _average_wait_time(
        self, simulation_hist: list[list[StepData]], steps: int
    ) -> tuple[float, float]:
        """Return the average wait-time across steps with std. dev
        assuming no random-arrival."""
        gross_wait_time = 0
        for trial in simulation_hist:
            for step_data in trial:
                gross_wait_time += step_data.wait_time
        num_steps = len(simulation_hist) * steps
        raise np.round(gross_wait_time / num_steps, 2)

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

        return stations[np.argmax(count)]

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
        self, trials: int, steps: int, player: Player, rand_arrival: bool
    ) -> list[list[StepData]]:
        """Return the results of a simulation."""
        simulation_history = []
        for i in range(trials):
            trial_history = []
            for j in range(steps):
                trial_history.append(self._step(rand_arrival, player, j, i))
            simulation_history.append(trial_history)
        return simulation_history

    def execute_simulation(self, trials: int, steps: int, map_id: int) -> None:
        """Execute a new simulation on the map with id <map_id>."""
        self._dao.load_map(map_id)
        self._world = self._new_world()
        spawn = self._spawn_station()

        self._presenter.clear_messages()
        self._presenter.say_executing_simulation(trials, steps)
        self._presenter.show_loading(True)
        player = Player(name=SIMULATION_NAME, starting_station=spawn)

        sim_history = self._simulate(trials, steps, player, False)
        rand_arrival_sim_history = self._simulate(trials, steps, player, True)

        self._presenter.show_loading(False)
        self._presenter.say_done_trials()
        self._presenter.show_results(
            self._output_grid_data(
                sim_history,
                rand_arrival_sim_history,
                steps,
                spawn,
            )
        )

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self._dao.map_ids()

    def _spawn_station(self) -> Station:
        """Return the station farthest from the map's end, matching the game
        spawn, so a trial starts as deep in the network as possible."""
        end_id = next(s.id for s in self._world.get_stations() if s.end)
        distances = self._distances_from(end_id)
        farthest = max(distances.values())
        spawn_id = min(sid for sid, dist in distances.items() if dist == farthest)
        return self._world.get_station_by_id(spawn_id)

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
        times = []
        for neighbour in self._world.adjacent_stations(player.station):
            if rand_arrival:
                seconds = self._random_arrival_wait(
                    self._dao.get_record(neighbour.id)["rule"]
                )
            else:
                seconds = self._dao.sample_rule(neighbour.id)
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

    def _probability_faster_wait_time(
        self, station1_id: int, station2_id: int
    ) -> float:
        """Return the probability station1's train will arrive
        before station2's."""
        station1 = self._world.get_station_by_id(station1_id)
        station2 = self._world.get_station_by_id(station2_id)
        return self._probability_is_fastest(
            station1.rule,
            station2.rule,
        )

    def _probability_is_fastest(
        self, rule_j: rv_frozen, others: list[rv_frozen]
    ) -> float:
        """P(X_j < every rule in <others>) by conditioning on X_j = t,
        then the survival probabilities multiply."""
        if self._is_discrete(rule_j):
            return float(
                sum(
                    rule_j.pmf(t) * np.prod([r.sf(t) for r in others])
                    for t in self._discrete_support(rule_j)
                )
            )
        lower, upper = self._continuous_bounds(rule_j)
        return float(
            integrate.quad(
                lambda t: rule_j.pdf(t) * np.prod([r.sf(t) for r in others]),
                lower,
                upper,
            )[0]
        )

    def _fundamental_matrix(self) -> tuple[np.ndarray, list[Station]]:
        """Return (N, transient) with N[i][j] = expected visits to transient j
        before reaching the end, starting from state i."""
        transient = [s for s in self._world.get_stations() if not s.end]
        index = {station.id: k for k, station in enumerate(transient)}
        Q = np.zeros((len(transient), len(transient)))
        for station in transient:
            neighbours = self._world.adjacent_stations(station)
            rules = [neighbour.rule for neighbour in neighbours]
            for k, neighbour in enumerate(neighbours):
                if neighbour.id in index:
                    Q[index[station.id], index[neighbour.id]] = (
                        self._probability_is_fastest(
                            rules[k], rules[:k] + rules[k + 1 :]
                        )
                    )
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
