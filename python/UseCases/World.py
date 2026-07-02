from typing import Any
from Entities import Station, Road, Flight, Route, InvalidRouteError



class World:
    """A Entities of Stations (Vertices) and Routes between them (Edges).

    Terminology:
        - Vertices: The elements themselves
        - Edges: The bridge between any 2 vertices
        - Directed/Non-directed Edges: The direction of the edges.

    Private Attributes:
        - _locations: A list of all the stations of the vertices.
        - _roads: A list of all edges between any two vertices.
        - _flights: A list of all edges between any two vertices.
        Flights connect any two vertices and don't have multiple paths.
    """

    _locations: list[Station]
    _roads: list[Road]
    _flights: list[Flight]

    def __init__(self) -> None:
        """Create a Entities."""
        self._locations = []
        self._roads = []
        self._flights = []

    def add_location(self, l1: Station) -> None:
        """Add station <l> to <_locations>"""
        self._locations.append(l1)

    def add_road(self, road: Road) -> None:
        """Add a new road between two stations and distance between them.

        Raise InvalidRouteError if either <l1> or <l2> are not in Entities.
        """
        if road.start not in self._locations:
            raise InvalidRouteError
        elif road.stop not in self._locations:
            raise InvalidRouteError

        self._roads.append(road)

    def add_flight(self, flight: Flight) -> None:
        """Add a new flight between two stations and distance between them.

        Raise InvalidRouteError if either <l1> or <l2> are not in Entities.
        """
        if flight.start not in self._locations:
            raise InvalidRouteError
        elif flight.stop not in self._locations:
            raise InvalidRouteError

        self._flights.append(flight)

    def get_routes_from(self, l1: Station) -> list[tuple[Station, float]]:
        """Get all outgoing routes from <l> and to where."""

        outgoing = []
        for road in self._roads:
            if road.start == l1:
                mapping = l1, road.distance
                outgoing.append(mapping)

        for flight in self._flights:
            if flight.start == l1:
                mapping = l1, flight.time
                outgoing.append(mapping)
        return outgoing

    def get_fastest_route(self, l1: Station, l2: Station) -> list[Route] | False:
        """Find the combination of roads between <l1> and <l2>
        with the minimum distance.

        Return None if no route between <l1> and <l2> exist.
        """
        # # Find all possible combinations,
        # # Minimize over their combined distances
        # if not self.has_path(l1, l2):
        #     return False
        # # Know: There exists at least one combination from <l1> to <l2>
        #
        # combs = []
        # for location1 in self.get_routes_from(l1):
        #     if location1 == l2:
        #
        #     sub_routes = self.get_fastest_route(location1, l2)
        #     if sub_routes is not None:
        #         combs.extend(sub_routes)
        raise NotImplementedError

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
