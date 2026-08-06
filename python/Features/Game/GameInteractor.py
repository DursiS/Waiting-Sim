import random
from datetime import timedelta

from Entities import Bet, BetLog, GameState, Station, World, Player, Line
from Entities.TurnResult import TurnResult
from Features.Game import GameInputBoundry, GameOutputBoundry
from Data import WorldDataAccessInterface

HOUSE_DEFLATOR = 0.95
MAX_PATHS = 10**5
Z_95 = 1.645
LENGTH_TRAVEL_FACTOR = 0.01


class GameInteractor(GameInputBoundry):
    """Orchestrates business logic"""

    _world: World
    _dao: WorldDataAccessInterface
    _presenter: GameOutputBoundry
    _last_game = None | tuple
    _log: BetLog

    def __init__(
        self, dao: WorldDataAccessInterface, presenter: GameOutputBoundry
    ) -> None:

        self._dao = dao
        self._presenter = presenter
        self._world = self._new_world()
        self._last_game = None

    def execute_game(
        self,
        player: Player | None,
        name: str,
        map_id: int,
        rand_arrival: bool,
        gamble: bool,
    ) -> GameState:
        """Set up and run a Game."""
        self._load_map(map_id)
        if player is None:
            player = Player(
                name=name,
                starting_station=self._instantiate_station(
                    self._dao.get_record(self._spawn_station_id())
                ),
            )

        turn_results = []
        while not player.station.end:
            turn_results.append(self._game_turn(player, rand_arrival))
            self._presenter.present_game_turn(turn_results[-1])

        _last_game = player, map_id, rand_arrival

        game = GameState(
            phase_id=-1,
            turn_results=turn_results,  # end_steps = len(turn_results) btw
        )
        if gamble:
            self._payout(game)
        return game

    def execute_restart(self) -> None:
        """Replay the current game's map, name and random-arrival setting."""
        if self._last_game is None:
            return
        player, map_id, rand_arrival, gamble = self._last_game
        self.execute_new_game(player, map_id, rand_arrival, False)

    def _game_turn(self, player: Player, rand_arrival: bool) -> None:
        """Run one turn of the game, feeding the presenter as it goes."""

        wait_times = self._neighbour_wait_times(player, rand_arrival)
        t_waited, destination = self._fastest(wait_times)
        t_travel = self._time_spent_traveling(player, destination)

        _from = player.station
        player.move(self._instantiate_station(self._dao.get_record(destination.id)))
        _to = player.station
        self._save_player(player, rand_arrival)

        return TurnResult(_to, _from, t_travel, t_waited)

    def _paths(self) -> list[int]:
        """Return a list of all possible paths to the end of
        the world currently loaded in, representing stations as their ids."""

        # vectorize
        raise NotImplementedError

    def _conditioned_paths(
        self, total_paths: list[int], curr_path: list[int]
    ) -> list[int]:
        """Return a list of all possible paths left given our current
        path so far."""

        # vectorize
        raise NotImplementedError

    def _event_probability(self, curr_path: list[int]) -> float:
        """Return the probability the bet's event occurs. Placeholder p = 1/2
        until wired to the map's wait distributions."""
        total_paths = self._paths()
        valid_paths = self._conditioned_paths(total_paths, curr_path)
        return len(valid_paths) / len(total_paths)

    def _payout(self, game: GameState) -> float:
        """Handle the accounting of who needs to be paid
        and how much given the outcome of the game."""
        n = game.phase_id
        self._log.complete_phase(n)
        payout = 0.0
        for bet in self._log.get_bets(n):
            payout += bet.payout(game)
        return payout

    def _create_bet(self, player: Player, amount: float, end_steps: int) -> Bet | None:
        """Build a bet on <end_steps>, or None if the stake or count is
        invalid."""
        if amount <= 0 or amount > player.balance:
            return None
        if end_steps <= 0:
            return None
        return Bet(self._house_payoff_factor(end_steps), amount, None, end_steps)

    def _house_payoff_factor(self, end_steps: int) -> float:
        """Return the profit multiple paid on a winning bet -- the fair odds
        shaved by the house edge -- so a stake returns stake * factor as profit
        on a win."""
        p = 1 / 2
        fair_value = 1 / p
        house_value = fair_value * HOUSE_DEFLATOR
        return house_value - 1

    def _fastest(
        self, wait_times: list[tuple[Station, float]]
    ) -> tuple[timedelta, Station]:
        """Return the shortest ride as a (wait, destination station) pair."""
        destination, seconds = min(wait_times, key=lambda pair: pair[1])
        return timedelta(seconds=seconds), destination

    def _time_spent_traveling(self, player: Player, destination: Station) -> timedelta:
        """Return the time in seconds spent travelling from the player's
        current station to their destination."""
        roads_from = self._world.roads_from(player.station)
        for road in roads_from:
            if road.to_id() == destination.id:
                s = road.length * LENGTH_TRAVEL_FACTOR
                return timedelta(seconds=s)
        return timedelta(seconds=1)

    def _best_highscore(self, rand_arrival: bool) -> dict | None:
        """Return the lowest-time completion of the current map for the given
        random-arrival setting, or None."""
        highscores = self._dao.get_highscores(self._dao.current_map_id(), rand_arrival)
        return min(highscores, key=lambda entry: entry["time"]) if highscores else None

    def _save_player(self, player: Player, rand_arrival: bool) -> None:
        """Persist <player> with their map and random-arrival choice."""
        data = player.convert_to_data()
        data["map_id"] = self._dao.current_map_id()
        data["rand_arrival"] = rand_arrival
        self._dao.save_player(data)

    def _station_expectations(self) -> list[tuple[str, float, float]]:
        """Return the name, expected wait and std dev of every station."""
        return [
            (
                record["name"],
                self._dao.get_expectation(record["id"]),
                self._dao.get_std_dev(record["id"]),
            )
            for record in self._dao.get_records()
        ]

    def _get_map_expectation(self) -> tuple[float, float]:
        """Return the map's total expected wait and the std dev of that total.

        Stations are treated as independent, so the variance of the total is
        the sum of variances and its std dev is the root of that sum."""
        total_expectation = 0.0
        total_variance = 0.0
        for record in self._dao.get_records():
            total_expectation += self._dao.get_expectation(record["id"])
            total_variance += self._dao.get_std_dev(record["id"]) ** 2
        return total_expectation, total_variance**0.5

    def _station_risks(self) -> list[tuple[str, float]]:
        """Return the name and 95th-percentile risk wait of every station."""

        def f(station_id):
            """Return the risk of one station"""
            return self._dao.get_expectation(station_id) + Z_95 * self._dao.get_std_dev(
                station_id
            )

        return [(record["name"], f(record["id"])) for record in self._dao.get_records()]

    def _map_risk(self) -> float:
        """Return the map's 95th-percentile risk wait time for the total."""
        total_expectation, total_std_dev = self._get_map_expectation()
        return total_expectation + Z_95 * total_std_dev

    def _load_map(self, map_id: int) -> None:
        """Switch to map <map_id>, rebuild the world and show it."""
        self._dao.load_map(map_id)
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

    def _view_roads(self) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """Return each road as an ordered (from, to) pair of grid coordinates
        for the view to draw as a one-way lane."""
        return [
            (line._from.coordinates, line._to.coordinates)
            for lines in self._world.get_lines(None).values()
            for line in lines
        ]

    def _spawn_station_id(self) -> int:
        """Return the id of the station farthest from the map's end.

        Ties are broken by the lowest id so a map spawns deterministically."""
        distances = self._distances_from(self._end_station_id())
        farthest = max(distances.values())
        return min(sid for sid, dist in distances.items() if dist == farthest)

    def _end_station_id(self) -> int:
        """Return the id of the map's end station."""
        for record in self._dao.get_records():
            if record["end"]:
                return record["id"]
        raise ValueError("map has no end station")

    def _distances_from(self, start_id: int) -> dict[int, int]:
        """Return the step distance to every reachable station."""
        distances = {start_id: 0}
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            for neighbor_id in self._adjacent_ids(current):
                if neighbor_id not in distances:
                    distances[neighbor_id] = distances[current] + 1
                    queue.append(neighbor_id)
        return distances

    def _adjacent_ids(self, station_id: int) -> list[int]:
        """Return the ids of the stations adjacent on the grid."""
        station = self._world.station_at(
            tuple(self._dao.get_record(station_id)["coordinates"])
        )
        return [neighbor.id for neighbor in self._world.adjacent_stations(station)]

    def _new_world(self) -> World:
        """Return a world built from the current map's station records, wiring
        up each station's roads as one-way lines between the built stations."""
        world = World()
        stations = [
            self._instantiate_station(record) for record in self._dao.get_records()
        ]
        world.add_stations(stations)
        by_id = {station.id: station for station in stations}
        for record in self._dao.get_records():
            for road in record["roads"]:
                world.add_line(
                    Line(
                        _from=by_id[record["id"]],
                        _to=by_id[road["to"]],
                        length=road["length"],
                    )
                )
        return world

    def _neighbour_expected_times(
        self, player: Player, rand_arrival: bool
    ) -> list[tuple[Station, float]]:
        """Return each adjacent station paired with its expected ride time."""
        result = []
        for neighbour in self._world.adjacent_stations(player.station):
            expectation = self._dao.get_expectation(neighbour.id)
            if rand_arrival:
                expectation -= random.uniform(0, expectation) / 2
            result.append((neighbour, expectation))
        return result

    def _neighbour_wait_times(
        self, player: Player, rand_arrival: bool
    ) -> list[tuple[Station, float]]:
        """Sample each adjacent station's ride time with that station."""
        result = []
        for neighbour in self._world.adjacent_stations(player.station):
            seconds = self._dao.sample_rule(neighbour.id)
            if rand_arrival:
                arrival = random.uniform(0, seconds) / 2
                while seconds < arrival:
                    seconds = self._dao.sample_rule(neighbour.id)
                seconds -= arrival
            result.append((neighbour, seconds))
        return result
