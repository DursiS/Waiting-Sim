from datetime import timedelta

from scipy.stats._distn_infrastructure import rv_frozen


class Station:
    """A station in World.

    Public Attributes:
        - name: The name of the station
        - rule_name: The name of the wait-time distribution for this station
        - rule: The frozen wait-time distribution for this station
        - times_visited: The number of times this station has been visited
        - waited_at: The total time spent waiting at this station
        - N, S, E, W: The adjacent station's id in that direction, or None

    Stations may have the same name but NOT the same id.
    """

    name: str
    id: int
    rule_name: str
    rule: rv_frozen
    times_visited: int
    waited_at: timedelta
    N: int | None
    S: int | None
    E: int | None
    W: int | None
    coordinates: tuple[int, int]

    def __init__(
        self,
        name: str,
        rule_name: str,
        rule: rv_frozen,
        times_visited: int = 0,
        waited_at: timedelta = timedelta(),
        N: int | None = None,
        S: int | None = None,
        E: int | None = None,
        W: int | None = None,
        coordinates: tuple[int, int] = None,
    ) -> None:
        """Create a Station."""
        self.name = name
        self.rule_name = rule_name
        self.rule = rule
        self.times_visited = times_visited
        self.waited_at = waited_at
        self.N = N
        self.S = S
        self.E = E
        self.W = W
        self.coordinates = coordinates

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

    def get_adjacent_station_ids(self) -> list[int]:
        """Return the ids of all stations adjacent to this station."""
        return [d for d in (self.N, self.S, self.E, self.W) if d is not None]
