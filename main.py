from datetime import timedelta
from typing import Any, Callable
from scipy import stats

STATIONS = {
    "Coinflip Cove":   stats.geom(p=0.30),
    "Patience Point":  stats.nbinom(n=4, p=0.40),
    "Poisson Plaza":   stats.poisson(mu=3.0),
    "Binomial Bazaar": stats.binom(n=10, p=0.35),
    "Dice Depot":      stats.randint(low=1, high=7),
}

class WaitRules:
    """Rules to determine how waiting time is configured.

    Representation Invariants:
        - name must be a valid distribution scipy stats methods

    Public Attributes:
        - _rule_map is a dictionary mapping station names to their
        default distributions.
    """

    _rule_map: dict[str, Callable]
    dt: timedelta

    def __init__(self, rule_map: dict, dt: timedelta=timedelta(seconds=1)) -> None:
        self._rule_map = rule_map
        self.dt = dt

    def wait_time(self, name: str) -> timedelta:
        """Return the amount of dt the user must wait."""
        return self._rule_map[name].rvs() * self.dt

    def get_dt(self) -> timedelta:
        """Return dt."""
        return self.dt

    def set_dt(self, dt: timedelta) -> None:
        """Set dt."""
        self.dt = dt


class Station:
    """A station in World.

    Public Attributes:
        - name: The name of the station

    Stations may have the same name but NOT the same id.
    """

    name: str
    id: int

    def __init__(self, name: str) -> None:
        """Create a Station."""
        self.name = name

    def __eq__(self, other: object) -> bool:
        """Return True if and only if <other> has the same name."""
        if not isinstance(other, Station):
            return False
        return self.id == other.id

    def get_name(self) -> str:
        """Return name."""
        return self.name

    def set_name(self, name: str) -> None:
        """Set name."""
        self.name = name

    def get_id(self) -> int:
        """Return id."""
        return self.id

    def set_id(self, id: int) -> None:
        """Set id."""
        self.id = id


class InvalidRouteError:
    """Raise an error when adding a Route that doesn't exist in Graph."""

    def __str__(self) -> str:
        return "InvalidRouteError: A station is not in the graph already."


class Route:
    """An abstract class representing a route between two stations.

    Private Attributes:
        - start: Station where the route starts
        - stop: Station where the route stops

    """

    start: Station
    stop: Station

    def __init__(self, start: Station, stop: Station) -> None:
        """Create a new Route."""
        self.start = start
        self.stop = stop

    def __str__(self) -> str:
        raise NotImplementedError

    def get_start(self) -> Station:
        """Return start."""
        return self.start

    def set_start(self, start: Station) -> None:
        """Set start."""
        self.start = start

    def get_stop(self) -> Station:
        """Return stop."""
        return self.stop

    def set_stop(self, stop: Station) -> None:
        """Set stop."""
        self.stop = stop


class Road(Route):
    """A road between two stations.

    Public Attribute:
        - distance: The distance between _start and _stop

    Representation Invariants:
        - _distance > 0
    """

    distance: float

    def __init__(self, l1: Station, l2: Station, distance: float) -> None:
        """Create a new Road."""
        super().__init__(l1, l2)
        self.distance = distance

    def __str__(self) -> str:
        return f"Road to {self.stop}: {self.distance} km"

    def get_distance(self) -> float:
        """Return distance."""
        return self.distance

    def set_distance(self, distance: float) -> None:
        """Set distance."""
        self.distance = distance

class Player:
    """The player travelling the world station-to-station."""
    name: str
    station_name: str
    station_id: int
    time_waited: timedelta
    stations_visited: dict[str, bool]

    def __init__(self, name: str, starting_station: Station) -> None:
        self.name = name
        self.station_name = starting_station.get_name()
        self.station_id = starting_station.get_id()
        self.time_waited = timedelta(seconds=0)
        self.stations_visited = {}

class Flight(Route):
    """A flight between two stations.

    Private Attribute:
        - _time: The time it takes to go between _start and _stop in minutes

    Representation Invariants:
        - _time > 0
    """

    time: float

    def __init__(self, l1: Station, l2: Station, time: float) -> None:
        """Create a new Flight."""
        super().__init__(l1, l2)
        self.time = time

    def __str__(self) -> str:
        return f"Flight to {self.stop}: {self.time} min"


class World:
    """A Graph of Stations (Vertices) and Routes between them (Edges).

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
        """Create a Graph."""
        self._locations = []
        self._roads = []
        self._flights = []

    def add_location(self, l1: Station) -> None:
        """Add station <l> to <_locations>"""
        self._locations.append(l1)

    def add_road(self, road: Road) -> None:
        """Add a new road between two stations and distance between them.

        Raise InvalidRouteError if either <l1> or <l2> are not in Graph.
        """
        if road.start not in self._locations:
            raise InvalidRouteError
        elif road.stop not in self._locations:
            raise InvalidRouteError

        self._roads.append(road)

    def add_flight(self, flight: Flight) -> None:
        """Add a new flight between two stations and distance between them.

        Raise InvalidRouteError if either <l1> or <l2> are not in Graph.
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
        # Find all possible combinations,
        # Minimize over their combined distances
        if not self.has_path(l1, l2):
            return False
        # Know: There exists at least one combination from <l1> to <l2>

        combs = []
        for location1 in self.get_routes_from(l1):
            if location1 == l2:

            sub_routes = self.get_fastest_route(location1, l2)
            if sub_routes is not None:
                combs.extend(sub_routes)

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
