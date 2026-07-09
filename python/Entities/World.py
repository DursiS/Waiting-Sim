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

    def __init__(self) -> None:
        """Create a World."""
        self._stations = []
        self._grid = np.matrix(np.ones(n))

    def add_station(self, station: Station) -> None:
        """Add station <station> to <_stations>"""
        self._stations.append(station)

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
