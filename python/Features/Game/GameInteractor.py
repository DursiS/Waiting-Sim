import random
from datetime import timedelta

from Entities import Station, World, Player
from Features.Game import GameInputBoundry, GameOutputBoundry
from Data import AccessWaitRulesInterface

Z_95 = 1.645


class GameInteractor(GameInputBoundry):
    """Orchestrates business logic"""

    _world: World
    _dao: AccessWaitRulesInterface
    _presenter: GameOutputBoundry
    _last_game: tuple[str, int, bool] | None

    def __init__(
        self, dao: AccessWaitRulesInterface, presenter: GameOutputBoundry
    ) -> None:

        self._dao = dao
        self._presenter = presenter
        self._world = self._new_world()
        self._last_game = None

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

    def _fastest(
        self, wait_times: list[tuple[Station, float]]
    ) -> tuple[timedelta, Station]:
        """Return the shortest ride as a (wait, destination station) pair."""
        destination, seconds = min(wait_times, key=lambda pair: pair[1])
        return timedelta(seconds=seconds), destination

    def _named(
        self, wait_times: list[tuple[Station, float]]
    ) -> list[tuple[str, float]]:
        """Label each neighbour-wait pair with its station name for display."""
        return [(station.name, seconds) for station, seconds in wait_times]

    def _game_turn(self, player: Player, rand_arrival: bool) -> None:
        """Run one turn of the game, feeding the presenter as it goes."""
        self._presenter.clear_messages()
        expected = self._neighbour_expected_times(player, rand_arrival)
        self._presenter.say_expected_times(self._named(expected))

        wait_times = self._neighbour_wait_times(player, rand_arrival)
        self._presenter.say_waiting()
        self._presenter.show_loading(True)

        t_waited, destination = self._fastest(wait_times)
        player.wait(t_waited)

        self._presenter.show_loading(False)
        self._presenter.say_sequenced_wait_times(self._named(wait_times))
        self._presenter.say_time_waited(t_waited, destination.name)

        if t_waited.total_seconds() >= self._station_risk(destination.id):
            self._presenter.say_percentile_wait()

        idx = player.station.id
        self._dao[idx]["times_visited"] += 1
        self._dao[idx]["waited_at"] += t_waited

        player.move(self._instantiate_station(self._dao.get_record(destination.id)))

        self._presenter.show_player_station(player.station)
        self._presenter.show_total_wait(player.time_waited.total_seconds())
        self._presenter.show_best_highscore(self._best_highscore(rand_arrival))

        if player.station.end:
            self._win(player, rand_arrival)
        else:
            self._save_player(player, rand_arrival)
            self._presenter.prompt_to_continue()

    def _best_highscore(self, rand_arrival: bool) -> dict | None:
        """Return the lowest-time completion of the current map for the given
        random-arrival setting, or None."""
        highscores = self._dao.get_highscores(self._dao.current_map_id(), rand_arrival)
        return min(highscores, key=lambda entry: entry["time"]) if highscores else None

    def _win(self, player: Player, rand_arrival: bool) -> None:
        """End the game: record the highscore and clear the save."""
        total_wait = player.time_waited.total_seconds()
        self._dao.save_highscore(
            self._dao.current_map_id(), rand_arrival, player.name, total_wait
        )
        self._dao.erase_player_data()
        self._presenter.say_reached_end(total_wait)

    def _save_player(self, player: Player, rand_arrival: bool) -> None:
        """Persist <player> with their map and random-arrival choice."""
        data = player.convert_to_data()
        data["map_id"] = self._dao.current_map_id()
        data["rand_arrival"] = rand_arrival
        self._dao.save_player(data)

    def execute_new_game(
        self,
        name: str,
        map_id: int,
        rand_arrival: bool,
    ) -> None:
        """Set up a game on <map_id> and explain it, leaving the first turn to
        a continue."""
        self._last_game = (name, map_id, rand_arrival)
        self._load_map(map_id)
        self._present_wait_stats()
        spawn = self._instantiate_station(
            self._dao.get_record(self._spawn_station_id())
        )
        player = Player(name=name, starting_station=spawn)

        self._save_player(player, rand_arrival)
        self._presenter.show_player_station(spawn)
        self._presenter.show_total_wait(player.time_waited.total_seconds())
        self._presenter.show_best_highscore(self._best_highscore(rand_arrival))
        self._presenter.clear_messages()
        self._presenter.say_explanation()
        self._presenter.prompt_to_continue()

    def _present_wait_stats(self) -> None:
        """Feed the presenter the map's per-station and total wait statistics."""
        self._presenter.clear_wait_stats()
        self._presenter.show_station_expectations(self._station_expectations())
        total_expectation, total_std_dev = self._map_expectation()
        self._presenter.show_map_expectation(total_expectation, total_std_dev)
        self._presenter.show_station_risks(self._station_risks())
        self._presenter.show_map_risk(self._map_risk())

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

    def _map_expectation(self) -> tuple[float, float]:
        """Return the map's total expected wait and the std dev of that total.

        Stations are treated as independent, so the variance of the total is
        the sum of variances and its std dev is the root of that sum."""
        total_expectation = 0.0
        total_variance = 0.0
        for record in self._dao.get_records():
            total_expectation += self._dao.get_expectation(record["id"])
            total_variance += self._dao.get_std_dev(record["id"]) ** 2
        return total_expectation, total_variance**0.5

    def _station_risk(self, station_id: int) -> float:
        """Return the 95th-percentile risk wait for the station with id <station_id>."""
        return self._dao.get_expectation(station_id) + Z_95 * self._dao.get_std_dev(
            station_id
        )

    def _station_risks(self) -> list[tuple[str, float]]:
        """Return the name and 95th-percentile risk wait of every station."""
        return [
            (record["name"], self._station_risk(record["id"]))
            for record in self._dao.get_records()
        ]

    def _map_risk(self) -> float:
        """Return the map's 95th-percentile risk wait time for the total."""
        total_expectation, total_std_dev = self._map_expectation()
        return total_expectation + Z_95 * total_std_dev

    def execute_continue_game(self) -> None:
        """Continue a pre-existing game, or report there is nothing to continue."""
        if not self._dao.exists_player_data():
            self._presenter.clear_messages()
            self._presenter.say_no_save()
            return

        data = self._dao.get_player_data()
        map_id = data.get("map_id", self._dao.current_map_id())
        rand_arrival = data.get("rand_arrival", False)
        self._last_game = (data["name"], map_id, rand_arrival)
        self._load_map(map_id)
        player_station = self._instantiate_station(
            self._dao.get_record(data["station"])
        )
        player = Player.build_player_from_data(data, player_station)
        self._game_turn(player, rand_arrival)

    def execute_restart(self) -> None:
        """Replay the current game's map, name and random-arrival setting."""
        if self._last_game is None:
            return
        name, map_id, rand_arrival = self._last_game
        self.execute_new_game(name, map_id, rand_arrival)

    def execute_quit_game(self) -> None:
        """Quit the game"""
        self._dao.erase_player_data()
        self._presenter.say_quitting_game()

    def get_world_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self._world.get_stations()

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self._dao.map_ids()

    def _load_map(self, map_id: int) -> None:
        """Switch to map <map_id>, rebuild the world and show it."""
        self._dao.load_map(map_id)
        self._world = self._new_world()
        self._presenter.show_stations(self._world.get_stations())

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
        """Return the step distance from <start_id> to every reachable station."""
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
        """Return the ids of the stations adjacent to <station_id> on the grid."""
        station = self._world.station_at(
            tuple(self._dao.get_record(station_id)["coordinates"])
        )
        return [neighbor.id for neighbor in self._world.adjacent_stations(station)]

    def _new_world(self) -> World:
        """Return a world built from the current map's station records."""
        world = World()
        world.add_stations(
            [self._instantiate_station(record) for record in self._dao.get_records()]
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
        """Sample each adjacent station's ride time, paired with that station."""
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
