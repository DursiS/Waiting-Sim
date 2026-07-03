from abc import ABC, abstractmethod
from datetime import timedelta

from scipy import stats
from scipy.stats import rv_frozen

from Entities import Station
from Framework import WaitRules


class WaitRulesGateway(ABC):
    """Applies parameter changes to a WaitRules instance."""

    _wait_rules: WaitRules

    def __init__(self, wait_rules: WaitRules) -> None:
        self._wait_rules = wait_rules

    @abstractmethod
    def set_dt(self, dt: timedelta) -> None:
        """Set dt in which wait time is counted in"""

    @abstractmethod
    def set_distribution(self, station: Station, dist: rv_frozen) -> None:
        """Polymorphic function to set distributions at any station."""
