from Station import Station


class InvalidRouteError:
    """Raise an error when adding a Route that doesn't exist in Entities."""

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
