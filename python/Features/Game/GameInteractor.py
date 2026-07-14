from typing import Any

from Entities import Station
from Entities.World import World
from Features.Game.GameInputBoundry import GameInputBoundry

from Features.Game.GameOutputBoundry import GameOutputBoundry
from Data.AccessWaitRulesInterface import AccessWaitRulesInterface
from Entities.Player import Player
from Features.Game.GameState import GameState


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
        self._world = self.execute_new_world()
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

    def _game_turn(self, player: Player) -> GameState:
        """Run one turn of the game, returning the world's stations, the
        player's resulting station, and the turn's messages."""
        messages = []

        E_t = self.get_expected_wait_times(player)
        messages.append(
            self._presenter.say_expected_times(dict(zip(self._directions, E_t)))
        )

        t = self.get_wait_times(player)
        messages.append(
            self._presenter.say_sequenced_wait_times(dict(zip(self._directions, t)))
        )
        messages.append(self._presenter.say_waiting())
        t_waited, destination = player.wait(t)
        messages.append(self._presenter.say_time_waited(t_waited, destination))

        starting_station = player.station
        idx = starting_station.id
        self._dao[idx]["times_visited"] += 1
        self._dao[idx]["waited_at"] += t_waited

        first_to_arrive = getattr(starting_station, destination)
        player.move(self._instantiate_station(self._dao.get_record(first_to_arrive)))

        self._dao.save_player(player.convert_to_data())
        messages.append(self._presenter.prompt_to_continue())

        return GameState(self._world.get_stations(), player.station, messages)

    def execute_new_game(
        self, name: str, starting_station_id: int
    ) -> tuple[list[Station], Station, list[str]]:
        """Orchestrate a single game."""
        starting_station = self._instantiate_station(self._dao[starting_station_id])
        player = Player(
            name=name,
            starting_station=starting_station,
        )

        return self._game_turn(player)

    def execute_continue_game(self) -> tuple[list[Station], Station | None, list[str]]:
        """Continue a pre-existing game or start a new one otherwise."""
        if self._dao.exists_player_data():
            data = self._dao.get_player_data()
            player_station = self._instantiate_station(
                self._dao.get_record(data["station"])
            )
            player = Player.build_player_from_data(data, player_station)

            return self._game_turn(player)

        return self._world.get_stations(), None, [self._presenter.say_cant_continue()]

    def get_world_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self._world.get_stations()

    def execute_quit_game(self) -> None:
        """Quit the game"""
        self._dao.erase_player_data()
        self._presenter._say_quitting_game()

    def execute_new_world(self) -> World:
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

    def get_expected_wait_times(self, player: Player) -> list[Any]:
        """Return the expected time to wait for the transportation in each
        direction, None if there is no station adjacent in that direction."""
        idx = player.station.id
        result = []
        for direction in self._directions:
            neighbor_id = self._dao[idx][direction]
            if neighbor_id is not None:
                result.append(self._dao.get_expectation(neighbor_id))
            else:
                result.append(None)
        return result

    def get_wait_times(self, player: Player) -> list[Any]:
        """Sample the distributions for each direction's transportation,
        None if there is no station adjacent in that direction."""
        idx = player.station.id
        result = []
        for direction in self._directions:
            neighbor_id = self._dao[idx][direction]
            if neighbor_id is not None:
                result.append(self._dao[neighbor_id]["rule"].rvs())
            else:
                result.append(None)
        return result
