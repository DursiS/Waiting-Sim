from Entities import Station


DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}


class World:
    """A World of Stations laid out on a coordinate grid.

    Adjacency is not stored: two stations are neighbours exactly when their
    coordinates differ by one step in a cardinal direction, so every adjacency
    query is a grid lookup by coordinate.

    Private Attributes:
        - _stations: Every station in the world.
        - _by_coordinate: Every station keyed by its (x, y) grid position.
    """

    _stations: list[Station]
    _by_coordinate: dict[tuple[int, int], Station]

    def __init__(self) -> None:
        """Create an empty World."""
        self._stations = []
        self._by_coordinate = {}

    def add_station(self, station: Station) -> bool:
        """Add <station>, return whether its grid position was free."""
        if station.coordinates in self._by_coordinate:
            return False
        self._stations.append(station)
        self._by_coordinate[station.coordinates] = station
        return True

    def add_stations(self, stations: list[Station]) -> bool:
        """Add as many stations as possible, return whether all were added."""
        result = 0
        for station in stations:
            if not self.add_station(station):
                result += 1
        return result == 0

    def get_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self._stations

    def get_station_by_id(self, station_id: int) -> Station | None:
        """Return the station with id <station_id>, or None if absent."""
        for station in self._stations:
            if station.id == station_id:
                return station
        return None

    def station_at(self, coordinate: tuple[int, int]) -> Station | None:
        """Return the station at <coordinate>, or None if that cell is empty."""
        return self._by_coordinate.get(coordinate)

    def neighbor(self, station: Station, direction: str) -> Station | None:
        """Return the station one step from <station> in <direction>."""
        dx, dy = DIRECTION_DELTAS[direction]
        x, y = station.coordinates
        return self._by_coordinate.get((x + dx, y + dy))

    def adjacent_stations(self, station: Station) -> list[Station]:
        """Return every station directly adjacent to <station> on the grid."""
        return [
            found
            for direction in DIRECTION_DELTAS
            if (found := self.neighbor(station, direction)) is not None
        ]
