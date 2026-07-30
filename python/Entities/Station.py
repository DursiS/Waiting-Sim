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
        - coordinates: The (x, y) grid position that fixes this station's neighbours
        - end: Whether this station is the map's finish line

    Stations may have the same name but NOT the same id.
    """

    name: str
    id: int
    rule_name: str
    rule: rv_frozen
    times_visited: int
    waited_at: timedelta
    coordinates: tuple[int, int]
    end: bool

    def __init__(
        self,
        name: str,
        rule_name: str,
        rule: rv_frozen,
        times_visited: int = 0,
        waited_at: timedelta = timedelta(),
        coordinates: tuple[int, int] = None,
        end: bool = False,
    ) -> None:
        """Create a Station."""
        self.name = name
        self.rule_name = rule_name
        self.rule = rule
        self.times_visited = times_visited
        self.waited_at = waited_at
        self.coordinates = coordinates
        self.end = end

    def __eq__(self, other: object) -> bool:
        """Return True if and only if <other> is a Station with the same id."""
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

    def E_t(self) -> float:
        """Return the expected wait time: the mean of this station's rule."""
        return float(self.rule.mean())
