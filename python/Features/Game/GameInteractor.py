import random
from typing import Any

from Entities import Station, World, Player
from Features.Game import GameInputBoundry, GameOutputBoundry
from Data import AccessWaitRulesInterface


class GameInteractor(GameInputBoundry):
    """Orchestrates business logic"""

    _world: World
    _dao: AccessWaitRulesInterface
    _presenter: GameOutputBoundry
    _directions: tuple[str, str, str, str]

    def __init__(
        self, dao: AccessWaitRulesInterface, presenter: GameOutputBoundry
    ) -> None:

        self._dao = dao
        self._presenter = presenter
        self._world = self._new_world()
        self._directions = ("N", "S", "W", "E")

    def _instantiate_station(self, record: dict) -> Station:
        """Build a Station from the wait rules entry <record>."""
        station = Station(
            name=record["name"],
            rule_name=record["rule_name"],
            rule=record["rule"],
            times_visited=record["times_visited"],
            waited_at=record["waited_at"],
            N=record["N"],
            S=record["S"],
            E=record["E"],
            W=record["W"],
            coordinates=record["coordinates"],
            end=record["end"],
        )
        station.set_id(record["id"])
        return station

    def _game_turn(self, player: Player, rand_arrival: bool) -> None:
        """Run one turn of the game, feeding the presenter as it goes."""
        self._presenter.clear_messages()
        E_t = self._get_expected_wait_times(player, rand_arrival)
        self._presenter.say_expected_times(dict(zip(self._directions, E_t)))

        t = self._get_wait_times(player, rand_arrival)
        self._presenter.say_sequenced_wait_times(dict(zip(self._directions, t)))
        self._presenter.say_waiting()
        t_waited, destination = player.wait(t)
        self._presenter.say_time_waited(t_waited, destination)

        starting_station = player.station
        idx = starting_station.id
        self._dao[idx]["times_visited"] += 1
        self._dao[idx]["waited_at"] += t_waited

        first_to_arrive = getattr(starting_station, destination)
        player.move(self._instantiate_station(self._dao.get_record(first_to_arrive)))
        self._presenter.show_player_station(player.station)
        self._presenter.show_total_wait(player.time_waited.total_seconds())

        if player.station.end:
            self._win(player)
        else:
            self._save_player(player)
            self._presenter.prompt_to_continue()

    def _win(self, player: Player) -> None:
        """End the game: record the highscore and clear the save."""
        total_wait = player.time_waited.total_seconds()
        self._dao.save_highscore(self._dao.current_map_id(), player.name, total_wait)
        self._dao.erase_player_data()
        self._presenter.say_reached_end(total_wait)

    def _save_player(self, player: Player) -> None:
        """Persist <player> along with the map they are playing."""
        data = player.convert_to_data()
        data["map_id"] = self._dao.current_map_id()
        self._dao.save_player(data)

    def execute_new_game(
        self,
        name: str,
        map_id: int,
        rand_arrival: bool,
    ) -> None:
        """Orchestrate a single game on the map with id <map_id>."""
        self._load_map(map_id)
        spawn = self._instantiate_station(self._dao.get_record(self._spawn_station_id()))
        player = Player(name=name, starting_station=spawn)

        self._game_turn(player, rand_arrival)

    def execute_continue_game(self) -> None:
        """Continue a pre-existing game, or report there is nothing to continue."""
        if not self._dao.exists_player_data():
            self._presenter.clear_messages()
            self._presenter.say_no_save()
            return

        data = self._dao.get_player_data()
        self._load_map(data.get("map_id", self._dao.current_map_id()))
        player_station = self._instantiate_station(
            self._dao.get_record(data["station"])
        )
        player = Player.build_player_from_data(data, player_station)
        self._game_turn(player, rand_arrival=False)

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
        """Return the ids of the stations adjacent to <station_id>."""
        record = self._dao.get_record(station_id)
        return [record[d] for d in self._directions if record[d] is not None]

    def _new_world(self) -> World:
        """Return the default world configuration."""
        stations, coordinates = [], []
        for record in self._dao.get_records():
            new_station = self._instantiate_station(record)
            stations.append(new_station)
            coordinates.append(new_station.coordinates)

        x_m, y_m = 0, 0
        for coordinate in coordinates:
            if coordinate[0] > x_m:
                x_m = coordinate[0]
            if coordinate[1] > y_m:
                y_m = coordinate[1]

        world = World(x_m + 1, y_m + 1)
        world.add_stations(stations)
        return world

    def _get_expected_wait_times(self, player: Player, rand_arrival: bool) -> list[Any]:
        """Return the expected time to wait for the transportation in each
        direction, None if there is no station adjacent in that direction."""
        idx = player.station.id
        result = []
        for direction in self._directions:
            neighbor_id = self._dao[idx][direction]
            E_x = None

            if neighbor_id is not None:
                E_x = self._dao.get_expectation(neighbor_id)
                if rand_arrival:
                    E_arrival = random.uniform(0, E_x) / 2
                    E_x -= E_arrival

            result.append(E_x)
        return result

    def _get_wait_times(self, player: Player, rand_arrival: bool) -> list[Any]:
        """Sample the distributions for each direction's transportation,
        None if there is no station adjacent in that direction."""
        idx = player.station.id
        result = []
        for direction in self._directions:
            neighbor_id = self._dao[idx][direction]
            x = None

            if neighbor_id is not None:
                x = self._dao.sample_rule(neighbor_id)
                if rand_arrival:
                    arrival = random.uniform(0, x) / 2
                    while x < arrival:
                        x = self._dao.sample_rule(neighbor_id)
                    x -= arrival
            result.append(x)
        return result
