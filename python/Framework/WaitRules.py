from datetime import timedelta
from typing import Any, Callable, overload

from scipy.stats import rv_frozen

from Entities import Station
from Framework.Database import CLOSED_FORM_EXPECTATIONS, DEFAULT_STATIONS
from UseCases.WaitRulesGateway import WaitRulesGateway


class WaitRules(WaitRulesGateway):
    """Rules to determine how waiting time is configured for a whole world
    of stations.

    Public Attributes:
        - _rule_map is a dictionary mapping station ids to their
        configuration.
    """

    _rule_map: dict[int, dict[str, Any]]
    dt: timedelta

    def __init__(
        self,
        default_rule_map: dict = DEFAULT_STATIONS,
        dt: timedelta = timedelta(seconds=1),
    ) -> None:
        self._rule_map = default_rule_map
        self.dt = dt

    def get_dt(self) -> timedelta:
        """Return dt."""
        return self.dt

    def set_dt(self, dt: timedelta) -> None:
        """Set dt."""
        self.dt = dt

    def set_distribution(self, station: Station, rule: rv_frozen) -> None:
        """Polymorphic function to set distributions at any station."""
        self._rule_map[station.id]["rule"] = rule

    def get_expectation(self, station_id: str) -> float:
        """Return a sample for the distribution of that name and inputs."""
        return self._rule_map[station_id]["rule"].mean()

    def __getitem__(self, station_id: int) -> dict:
        """Return the rule entry for the station with id <station_id>."""
        return self._rule_map[station_id]
