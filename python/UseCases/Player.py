import random
import time
from datetime import timedelta
from Entities import Station


class Player:
    """The player travelling the world station-to-station."""

    name: str
    id: int
    station_name: str
    station_id: int
    time_waited: timedelta
    stations_visited: dict[int, bool]

    def __init__(
        self,
        name: str = "Player1",
        starting_station: Station = Station("Coinflip Cove"),
    ) -> None:
        self.name = name
        self.station_name = starting_station.get_name()
        self.station_id = starting_station.get_id()
        self.time_waited = timedelta(seconds=0)
        self.stations_visited = {}
        self.id = random.randint(1, 10**5)

    def move(self, new_station: Station, direction: str) -> bool:
        """Change the current station of this player, return True
        if the direction and station was valid."""
        if direction not in ["N", "S", "W", "E"]:
            return False
        elif new_station.id == self.station_id:
            return False
        else:
            self.station_name = new_station.name
            self.station_id = new_station.id
            self.stations_visited[new_station.id] = True
            return True

    def wait(
        self,
        t_N: timedelta = None,
        t_S: timedelta = None,
        t_E: timedelta = None,
        t_W: timedelta = None,
    ) -> None:
        """Make the user wait for all the transportation to arrive."""
        times = []
        if t_N is not None:
            times.append(t_N)
        if t_S is not None:
            times.append(t_S)
        if t_E is not None:
            times.append(t_E)
        if t_W is not None:
            times.append(t_W)
        time.sleep(max(times))
