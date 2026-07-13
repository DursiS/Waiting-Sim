from typing import Any

import numpy as np

from Entities import Station


class World:
    """A World of Stations (Vertices).

    Private Attributes:
        - _stations: A list of all the stations in the world.
        - _grid: A matrix of all places a station can be in this world.
    """

    _stations: list[Station]
    _grid: np.ndarray

    def __init__(self, x_m: int, y_m: int) -> None:
        """Create a World."""
        self._stations = []
        self._grid = np.zeros((x_m, y_m))

    def add_station(self, station: Station) -> bool:
        """Add station <station> to <_stations>, return whether
        it was successfully added."""
        x, y = station.coordinates
        if self._grid[x, y] != 0:
            return False
        else:
            self._stations.append(station)
            self._grid[x, y] = station.id
            return True

    def add_stations(self, stations: list[Station]) -> bool:
        """Add as many stations in stations as possible, return whether
        all were successfully added."""
        result = 0
        for station in stations:
            if not self.add_station(station):
                result += 1
        return result == 0

    def get_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self._stations

    def adjacent(self, u: Any, v: Any) -> bool:
        """Return True iff <u> and <v> are directly connected by an edge."""

    def get_neighbors(self, v: Any) -> list[Any]:
        """Return a list of all vertices adjacent to <v>; raise an error
        if <v> is missing."""

    def degree(self, v: Any) -> int:
        """Return the number of edges incident to <v>; raise an error
        if <v> is missing."""

    def num_vertices(self) -> int:
        """Return the total number of vertices in the graph."""

    def num_edges(self) -> int:
        """Return the total number of edges in the graph."""

    def has_path(self, start: Any, end: Any) -> bool:
        """Return True iff there exists a path from <start> to <end>."""
