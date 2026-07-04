from abc import ABC, abstractmethod
from datetime import timedelta

from scipy.stats import rv_frozen

from Entities import Station


class WaitRulesGateway(ABC):
    """Applies parameter changes to a WaitRules instance."""

    @abstractmethod
    def set_dt(self, dt: timedelta) -> None:
        """Set dt in which wait time is counted in"""

    @abstractmethod
    def set_distribution(self, station: Station, dist: rv_frozen) -> None:
        """Polymorphic function to set distributions at any station."""
