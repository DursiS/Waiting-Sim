from datetime import timedelta

from scipy.stats import rv_frozen

from Entities import Station
from UseCases.WaitRulesGateway import WaitRulesGateway


class WaitRules(WaitRulesGateway):
    """Rules to determine how waiting time is configured.

    Public Attributes:
        - _rule_map is a dictionary mapping station names to their
        default distributions.
    """

    _rule_map: dict[str, rv_frozen]
    dt: timedelta

    def __init__(
        self, default_rule_map: dict, dt: timedelta = timedelta(seconds=1)
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
        self._rule_map[station.id].rule = rule
