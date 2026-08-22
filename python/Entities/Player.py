import random
import time
from datetime import timedelta
from Entities import Station

DEFAULT_BALANCE = 100.0


class Player:
    """The player travelling the world station-to-station."""

    name: str
    id: int
    station: Station
    time_waited: timedelta
    stations_visited: dict[int, bool]
    balance: float

    def __init__(
        self,
        starting_station: Station | None,
        name: str = "Admin",
        starting_balance: int = DEFAULT_BALANCE,
    ) -> None:
        self.name = name
        self.station = starting_station
        self.time_waited = timedelta(seconds=0)
        self.stations_visited = {}
        self.id = random.randint(1, 10**5)
        self.balance = starting_balance

    def move(self, new_station: Station) -> bool:
        """Move the player onto <new_station> and mark it visited."""
        self.station = new_station
        self.stations_visited[new_station.id] = True
        return True

    def wait(self, fastest_time: timedelta) -> None:
        """Make the user wait for all the transportation to arrive."""

        time.sleep(fastest_time.total_seconds())
        self.time_waited += fastest_time

    def convert_to_data(self) -> dict:
        """Return this player as a dict."""
        return {
            "name": self.name,
            "id": self.id,
            "station": self.station,
            "time_waited": self.time_waited,
            "stations_visited": self.stations_visited,
        }

    @classmethod
    def build_player_from_data(cls, data: dict, station: Station) -> "Player":
        """Return a Player built from <data>, resuming at <station>."""
        player = cls(starting_station=station, name=data["name"])
        player.id = data["id"]
        player.time_waited = timedelta(seconds=data["time_waited"])
        player.stations_visited = {
            int(station_id): visited
            for station_id, visited in data["stations_visited"].items()
        }
        return player

    def get_balance(self) -> float:
        return self.balance

    def add_to_balance(self, n: float) -> None:
        self.balance += n
