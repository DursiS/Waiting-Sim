from datetime import timedelta

from scipy.stats import rv_frozen


class Station:
    """A station in World.

    Public Attributes:
        - name: The name of the station

    Stations may have the same name but NOT the same id.
    """

    name: str
    id: int
    name: str
    rule_name: str
    rule: rv_frozen
    times_visited: int
    waited_at: timedelta
    N: int | None
    S: int | None
    E: int | None
    W: int | None

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

    def get_adjacent_station_ids(self, station_id: int) -> list[int]:
        """Return the ids of all stations adjacent to <station_id>."""
        station = self._rule_map[station_id]
        return [station[d] for d in ("N", "S", "E", "W") if station[d] is not None]
