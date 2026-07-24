import random
from typing import Any

from Entities import Station, World, Player
from Features.Game import GameInputBoundry, GameOutputBoundry
from Data import AccessWaitRulesInterface

Z_95 = 1.645


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

        self._dao.save_player(player.convert_to_data())
        self._presenter.show_player_station(player.station)
        self._presenter.prompt_to_continue()

    def execute_new_game(
        self,
        name: str,
        starting_station_id: int,
        rand_arrival: bool,
    ) -> None:
        """Orchestrate a single game."""
        self._present_wait_stats()
        starting_station = self._instantiate_station(self._dao[starting_station_id])
        player = Player(
            name=name,
            starting_station=starting_station,
        )

        self._game_turn(player, rand_arrival)

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

    def _station_risks(self) -> list[tuple[str, float]]:
        """Return the name and 95th-percentile risk wait of every station."""
        return [
            (
                record["name"],
                self._dao.get_expectation(record["id"])
                + Z_95 * self._dao.get_std_dev(record["id"]),
            )
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
