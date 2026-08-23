from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from scipy.stats._distn_infrastructure import rv_frozen

from .station import Station


class WorldDataAccessInterface(ABC):
    """Access to the station catalogue and per-world layouts."""

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
    def get_expectation(self, station_id: int) -> float:
        """Return the expectation of the distribution of that name and inputs."""

    @abstractmethod
    def get_std_dev(self, station_id: int) -> float:
        """Return the standard deviation of the distribution of that name and inputs."""

    @abstractmethod
    def sample_rule(self, station_id: int) -> Any:
        """Return a sample from the distribution of that name and inputs."""

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
    def load_map(self, map_id: int) -> None:
        """Switch the active configuration to the map with id <map_id>."""

    @abstractmethod
    def map_ids(self) -> list[int]:
        """Return the ids of every available default map."""

    @abstractmethod
    def current_map_id(self) -> int | None:
        """Return the id of the currently loaded map."""

    @abstractmethod
    def save_highscore(
        self, map_id: int, rand_arrival: bool, name: str, time_waited: float
    ) -> None:
        """Append a completion of map <map_id> to the persistent highscores,
        kept separate per random-arrival setting."""

    @abstractmethod
    def get_highscores(self, map_id: int, rand_arrival: bool) -> list[dict]:
        """Return every recorded completion of map <map_id> for the given
        random-arrival setting."""

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
