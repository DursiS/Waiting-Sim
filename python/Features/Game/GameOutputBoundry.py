from abc import ABC, abstractmethod
from datetime import timedelta

from Entities import Station


class GameOutputBoundry(ABC):
    """An interface to decouple Adapter and Business logic."""

    @abstractmethod
    def clear_messages(self) -> None:
        """Clear the running turn messages before a new turn."""

    @abstractmethod
    def clear_wait_stats(self) -> None:
        """Clear the wait-statistics header before a new game."""

    @abstractmethod
    def show_station_expectations(
        self, station_stats: list[tuple[str, float, float]]
    ) -> None:
        """Add each station's expected wait time with error bars."""

    @abstractmethod
    def show_player_station(self, station: Station) -> None:
        """Highlight <station> as the player's current location."""

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
