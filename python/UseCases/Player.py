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
        name: str = "Player1",
        starting_station: Station = Station("Coinflip Cove"),
    ) -> None:
        self.name = name
        self.station = starting_station
        self.time_waited = timedelta(seconds=0)
        self.stations_visited = {}
        self.id = random.randint(1, 10**5)

    def move(self, new_station: Station) -> bool:
        """Change the current station of this player, return True
        if the direction and station was valid."""
        if new_station not in self.station.get_adjacent_station_ids():
            return False

        self.station = new_station
        self.stations_visited[new_station.id] = True
        return True

    def wait(self, times: list[float]) -> timedelta:
        """Make the user wait for all the transportation to arrive."""
        deltas = [timedelta(seconds=t) for t in times]
        longest = max(deltas)
        time.sleep(longest.total_seconds())
        self.time_waited += longest
        return longest
