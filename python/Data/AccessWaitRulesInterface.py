import json
from abc import ABC, abstractmethod
from datetime import timedelta

from scipy.stats._distn_infrastructure import rv_frozen

from Entities import Station


class AccessWaitRulesInterface(ABC):
    """Applies parameter changes to a WaitRules instance."""

    @abstractmethod
    def set_dt(self, dt: timedelta) -> None:
        """Set dt in which wait time is counted in"""

    @abstractmethod
    def get_dt(self) -> None:
        """Get dt in which wait time is counted in"""

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
    def station_ids(self) -> list[int]:
        """Return the ids of every station."""

    @abstractmethod
    def get_record(self, station_id: int) -> dict:
        """Return the record for the station with id <station_id>."""

    @abstractmethod
    def get_records(self) -> list[dict]:
        """Return every station's record."""

    @abstractmethod
    def save_player(self, player_data: dict) -> None:
        """Write player_info into player_data.json."""

    @abstractmethod
    def get_player_data(self) -> dict:
        """Return the player data as a dict from its .json file."""

    @abstractmethod
    def exists_player_data(self) -> bool:
        """Return whether there is pre-existing player data."""

    @abstractmethod
    def erase_player_data(self) -> None:
        """Erase current player data leaving a empty .json"""
