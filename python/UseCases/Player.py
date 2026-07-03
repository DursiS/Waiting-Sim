import random
from datetime import timedelta
from Entities import Station


class Player:
    """The player travelling the world station-to-station."""

    name: str
    id: int
    station_name: str
    station_id: int
    time_waited: timedelta
    stations_visited: dict[str, bool]Pla

    def __init__(
        self, name: str, starting_station: Station = Station("Coinflip Cove")
    ) -> None:
        self.name = name
        self.station_name = starting_station.get_name()
        self.station_id = starting_station.get_id()
        self.time_waited = timedelta(seconds=0)
        self.stations_visited = {}
        self.id = random.randint(1, 10**5)
