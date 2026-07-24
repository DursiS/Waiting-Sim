from abc import ABC, abstractmethod
from datetime import timedelta

from Entities import Station


class GameOutputBoundry(ABC):
    """An interface to decouple Adapter and Business logic."""

    @abstractmethod
    def clear_messages(self) -> None:
        """Clear the running turn messages before a new turn."""

    @abstractmethod
    def show_stations(self, stations: list[Station]) -> None:
        """Show <stations> as the map the player is on."""

    @abstractmethod
    def show_player_station(self, station: Station) -> None:
        """Highlight <station> as the player's current location."""

    @abstractmethod
    def say_reached_end(self, total_wait: float) -> None:
        """Announce the player reached the end after <total_wait> seconds."""

    @abstractmethod
    def say_expected_times(self, expected_times: dict[str, float | None]) -> None:
        """Add a message describing the expected wait time for each direction."""

    @abstractmethod
    def say_time_waited(self, t_waited: timedelta, destination: str) -> None:
        """Add a message describing how long the player waited."""

    @abstractmethod
    def say_sequenced_wait_times(self, wait_times: dict[str, float | None]) -> None:
        """Add a message describing the sampled wait time for each direction."""

    @abstractmethod
    def say_waiting(self) -> None:
        """Add a message telling the user their ride is on its way."""

    @abstractmethod
    def prompt_to_continue(self) -> None:
        """Add a message prompting the user to continue."""

    @abstractmethod
    def say_quitting_game(self) -> None:
        """Add a message telling the user the game is quitting."""

    @abstractmethod
    def say_no_save(self) -> None:
        """Add a message telling the user there is no save to continue from."""
