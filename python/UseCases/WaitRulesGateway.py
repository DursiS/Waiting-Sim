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

    @abstractmethod
    def get_expectation(self, station_id: str) -> float:
        """Return a sample for the distribution of that name and inputs."""

    @abstractmethod
    def __getitem__(self, station_id: int) -> dict:
        """Return the rule entry for the station with id <station_id>."""

    @abstractmethod
    def get_adjacent_station_ids(self, station_id: int) -> list[int]:
        """Return the ids of all stations adjacent to <station_id>."""
