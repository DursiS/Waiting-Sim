import random
import time
from datetime import timedelta
from Entities import Station


class Player:
    """The player travelling the world station-to-station."""

    name: str
    id: int
    station: Station
    time_waited: timedelta
    stations_visited: dict[int, bool]

    def __init__(
        self,
        starting_station: Station,
        name: str = "Player1",
    ) -> None:
        self.name = name
        self.station = starting_station
        self.time_waited = timedelta(seconds=0)
        self.stations_visited = {}
        self.id = random.randint(1, 10**5)

    def move(self, new_station: Station) -> bool:
        """Change the current station of this player, return True
        if the direction and station was valid."""
        if new_station.id not in self.station.get_adjacent_station_ids():
            return False

        self.station = new_station
        self.stations_visited[new_station.id] = True
        return True

    def wait(self, times: list[float | None]) -> tuple[timedelta, str]:
        """Make the user wait for all the transportation to arrive.

        <times> holds None for any direction with no adjacent station."""
        directions = ("N", "S", "W", "E")

        deltas = [None if t is None else timedelta(seconds=t) for t in times]
        candidates = [delta if delta is not None else timedelta.max for delta in deltas]
        fastest_index = candidates.index(min(candidates))
        fastest = deltas[fastest_index]
        destination = directions[fastest_index]

        time.sleep(fastest.total_seconds())
        self.time_waited += fastest
        return fastest, destination

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
        player.stations_visited = data["stations_visited"]
        return player
