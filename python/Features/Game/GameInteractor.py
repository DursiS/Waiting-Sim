import random
from datetime import timedelta

from Entities import (
    Bet,
    BetLog,
    GameInputData,
    GameOutputData,
    Station,
    World,
    Player,
    Line,
)
from Entities.Game import TurnResult
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
    _last_game: tuple | None
    _log: BetLog
    _admin: Player
    _curr_path: list[int]
    _all_paths: list[tuple[int, ...]] | None
    _p_memo: dict[tuple[int, int], float]

    def __init__(
        self, dao: WorldDataAccessInterface, presenter: GameOutputBoundry
    ) -> None:

        self._dao = dao
        self._presenter = presenter
        self._world = self._load_new_world()
        self._last_game = None
        self._log = BetLog()
        self._admin = Player(None)
        self._curr_path = []
        self._all_paths = None
        self._p_memo = {}

    def execute(
        self,
        player: Player | None,
        inputData: GameInputData,
    ) -> None:
        """Run the game described by <inputData> and, when gambling, settle its
        bets against the outcome, then present the finished state."""
        game = self._setup_game(
            player,
            inputData.name,
            inputData.map_id,
            inputData.rand_arrival,
            inputData.gamble,
            inputData.raw_bets,
            inputData.animate,
        )
        if inputData.gamble:
            self._payoff(self._last_game[0], self._admin, game)

        self._presenter.present_game_state(game)

    def _setup_game(
        self,
        player: Player | None,
        name: str,
        map_id: int,
        rand_arrival: bool,
        gamble: bool,
        raw_bets: list | None,
        animate: bool = True,
    ) -> GameOutputData:
        """Set up and run a Game to the end, presenting each turn and the
        finished result. When gambling the bets are placed and locked before the
        first turn, so every turn can report their updated probabilities."""
        self._load_map(map_id)
        if player is None:
            player = Player(
                name=name,
                starting_station=self._instantiate_station(
                    self._dao.get_record(self._world.starting_station().id)
                ),
            )
        self._last_game = (player, name, map_id, rand_arrival, gamble)
        self._curr_path = []
        self._all_paths = None
        self._p_memo = {}

        phase_id, bets = -1, ()
        if gamble:
            phase_id = self._log.new_betting_phase()
            self._load_bets(phase_id, raw_bets)
            self._log.complete_phase(phase_id)
            bets = self._log.get_bets(phase_id)

        self._presenter.present_game_setup(
            self._world.get_stations(),
            self._view_roads(),
            player.station,
            gamble,
            animate,
        )
        self._presenter.present_bets(
            [
                (
                    bet.id(),
                    bet.get_end_steps(),
                    self._p(bet.get_end_steps(), player.station),
                )
                for bet in bets
            ]
        )

        turn_results = []
        while not player.station.end:
            turn_results.append(self._game_turn(player, rand_arrival, bets))
            self._presenter.present_game_turn(turn_results[-1])

        return GameOutputData(
            phase_id=phase_id,
            turn_results=turn_results,
            gamble=gamble,
            rand_arrival=rand_arrival,
            payout=0.0,
        )

    def execute_restart(self) -> GameOutputData | None:
        """Replay the current game's map, name and random-arrival setting."""
        if self._last_game is None:
            return None
        _, name, map_id, rand_arrival, gamble = self._last_game
        game = self._setup_game(None, name, map_id, rand_arrival, gamble, None)
        self._presenter.present_game_state(game)
        return game

    def _payoff(self, player: Player, admin: Player, game: GameOutputData) -> float:
        """Handle the accounting of who needs to be paid
        and how much given the outcome of the game."""
        n = game.phase_id
        self._log.complete_phase(n)
        bets = self._log.get_bets(n)
        payoff = 0.0
        for bet in bets:
            payoff += bet.payout(game)
        player.balance += payoff
        admin.balance -= payoff
        game.payout = payoff
        game.bet_results = [bet.result() for bet in bets]
        return payoff

    def _game_turn(
        self, player: Player, rand_arrival: bool, bets: tuple[Bet, ...]
    ) -> TurnResult:
        """Run one turn of the game, extending the walked path and reporting the
        updated probability of each bet."""

        steps_taken = len(self._curr_path) - 1 if self._curr_path else 0
        probabilities = {
            bet.id(): self._p(bet.get_end_steps() - steps_taken, player.station)
            for bet in bets
        }

        wait_times = self._sample_neighbours(player, rand_arrival)
        t_waited, destination = self._fastest(wait_times)
        t_travel = self._time_spent_traveling(player, destination)

        _from = player.station
        player.move(self._instantiate_station(self._dao.get_record(destination.id)))
        _to = player.station
        self._save_player(player, rand_arrival)

        if not self._curr_path:
            self._curr_path.append(_from.id)
        self._curr_path.append(_to.id)

        return TurnResult(
            _to,
            _from,
            t_travel,
            t_waited,
            probabilities,
        )

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

    # ========
    # Getters & Setters
    # =======

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self._dao.map_ids()

    def get_balance(self) -> float:
        """Return the balance the next game's player bets with."""
        if self._last_game is not None:
            return self._last_game[0].balance
        return Player(None).balance

    def _get_spawn_station_id(self) -> int:
        """Return the id of the station farthest from the map's end.

        Ties are broken by the lowest id so a map spawns deterministically."""
        distances = self._get_distances_from(self._get_end_station_id())
        farthest = max(distances.values())
        return min(sid for sid, dist in distances.items() if dist == farthest)

    def _get_end_station_id(self) -> int:
        """Return the id of the map's end station."""
        for record in self._dao.get_records():
            if record["end"]:
                return record["id"]
        raise ValueError("map has no end station")

    def _get_distances_from(self, start_id: int) -> dict[int, int]:
        """Return the step distance to every reachable station."""
        distances = {start_id: 0}
        queue = [start_id]
        while queue:
            current = queue.pop(0)
            for neighbor_id in self._get_adjacent_ids(current):
                if neighbor_id not in distances:
                    distances[neighbor_id] = distances[current] + 1
                    queue.append(neighbor_id)
        return distances

    def _get_adjacent_ids(self, station_id: int) -> list[int]:
        """Return the ids of the stations adjacent on the grid."""
        station = self._world.station_at(
            tuple(self._dao.get_record(station_id)["coordinates"])
        )
        return [neighbor.id for neighbor in self._world.adjacent_stations(station)]

    # ========
    # Gambling
    # ========

    # def _paths(self, station: Station) -> list[tuple[int, ...]]:
    #     """Return every directed path from <station> to the end of the currently
    #     loaded world, each a tuple of station ids. Follows the one-way roads, so
    #     an acyclic map yields a finite set of paths."""
    #     if station.end:
    #         return [(station.id,)]
    #     paths = []
    #     for road in self._world.roads_from(station):
    #         neighbour = self._world.get_station_by_id(road.to_id())
    #         for tail in self._paths(neighbour):
    #             paths.append((station.id,) + tail)
    #     return paths
    #
    # def _conditioned_paths(
    #     self, total_paths: list[tuple[int, ...]], curr_path: list[int]
    # ) -> list[tuple[int, ...]]:
    #     """Return the paths from <total_paths> consistent with the walk so far
    #     -- those that keep <curr_path> as a prefix."""
    #     prefix = tuple(curr_path)
    #     depth = len(prefix)
    #     return [path for path in total_paths if tuple(path[:depth]) == prefix]

    def _p(self, remaining: int, station: Station) -> float:
        """Return the probability of reaching the end in exactly <remaining> more
        steps from <station>, as a random walk over the outgoing roads.

        Each branch is weighted by its transition probability (uniform for now),
        so paths that share a prefix are not over-counted -- they are not
        independent. Base case: standing on the end wins with 0 steps left. The
        result depends only on the map, so it is memoised for the game."""
        if station.end:
            return 1.0 if remaining == 0 else 0.0
        if remaining <= 0:
            return 0.0
        key = (remaining, station.id)
        if key in self._p_memo:
            return self._p_memo[key]
        successors = [
            self._world.get_station_by_id(road.to_id())
            for road in self._world.roads_from(station)
        ]
        # TODO: Weight = probability of transitioning
        weight = 1.0 / len(successors) if successors else 0.0
        result = sum(weight * self._p(remaining - 1, s) for s in successors)
        self._p_memo[key] = result
        return result

    def _create_bet(self, player: Player, amount: float, end_steps: int) -> Bet | None:
        """Build a bet on <end_steps>, or None if the stake or count is
        invalid."""
        if amount <= 0 or amount > player.balance:
            return None
        if end_steps <= 0:
            return None
        return Bet(self._payoff_factor(end_steps, player), amount, end_steps)

    def _payoff_factor(self, end_steps: int, player: Player) -> float:
        """Return the profit multiple paid on a winning bet -- the fair odds
        shaved by the house edge -- so a stake returns stake * factor as profit
        on a win."""
        p = self._p(end_steps, player.station)
        # TODO: remove later the if/else
        fair_value = 1 / p if p != 0 else 1 / 2
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

    # =========
    # Computers
    # =========

    def _compute_map_ev(self) -> tuple[float, float]:
        """Return the map's total expected wait and the std dev of that total.

        Stations are treated as independent, so the variance of the total is
        the sum of variances and its std dev is the root of that sum."""
        total_expectation = 0.0
        total_variance = 0.0
        for record in self._dao.get_records():
            total_expectation += self._dao.get_expectation(record["id"])
            total_variance += self._dao.get_std_dev(record["id"]) ** 2
        return total_expectation, total_variance**0.5

    def _compute_risks(self) -> list[tuple[str, float]]:
        """Return the name and 95th-percentile risk wait of every station."""

        def f(station_id):
            """Return the risk of one station"""
            return self._dao.get_expectation(station_id) + Z_95 * self._dao.get_std_dev(
                station_id
            )

        return [(record["name"], f(record["id"])) for record in self._dao.get_records()]

    def _compute_map_risk(self) -> float:
        """Return the map's 95th-percentile risk wait time for the total."""
        total_expectation, total_std_dev = self._compute_map_ev()
        return total_expectation + Z_95 * total_std_dev

    def _compute_neighbour_evs(
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

    # =======
    # Loaders
    # =======

    def _load_new_world(self) -> World:
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

    def _load_map(self, map_id: int) -> None:
        """Switch to map <map_id>, rebuild the world and show it."""
        self._dao.load_map(map_id)
        self._world = self._load_new_world()

    def _load_bets(self, phase_id: int, raw_bets: list) -> None:
        """Load the interval bets under <phase_id>: for each
        {"low", "high", "amount"} entry, place one bet per integer step count in
        [low, high], so their win probabilities sum to the interval's. Invalid
        bets are dropped by _create_bet."""
        player = self._last_game[0]
        for raw in raw_bets or []:
            for end_steps in range(raw["low"], raw["high"] + 1):
                bet = self._create_bet(player, raw["amount"], end_steps)
                if bet is not None:
                    self._log.add_bet(phase_id, bet)

    # =====
    # idk
    # =====

    def _sample_neighbours(
        self, player: Player, rand_arrival: bool
    ) -> list[tuple[Station, float]]:
        """Sample the ride time to each station one road leads to from here."""
        result = []
        for road in self._world.roads_from(player.station):
            neighbour = self._world.get_station_by_id(road.to_id())
            seconds = self._dao.sample_rule(neighbour.id)
            if rand_arrival:
                arrival = random.uniform(0, seconds) / 2
                while seconds < arrival:
                    seconds = self._dao.sample_rule(neighbour.id)
                seconds -= arrival
            result.append((neighbour, seconds))
        return result
