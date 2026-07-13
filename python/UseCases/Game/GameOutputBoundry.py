from abc import ABC, abstractmethod
from datetime import timedelta


class GameOutputBoundry(ABC):
    """An interface to decouple Adapter and Business logic."""

    @abstractmethod
    def say_expected_times(self, expected_times: dict[str, float | None]) -> str:
        """Return a message describing the expected wait time for each direction."""

    @abstractmethod
    def say_time_waited(self, t_waited: timedelta, destination: str) -> str:
        """Return a message describing how long the player waited."""

    @abstractmethod
    def say_sequenced_wait_times(self, wait_times: dict[str, float | None]) -> str:
        """Return a message describing the sampled wait time for each direction."""

    @abstractmethod
    def say_waiting(self) -> str:
        """Return a message telling the user their ride is on its way."""

    @abstractmethod
    def prompt_to_continue(self) -> str:
        """Return a message prompting the user to continue."""

    @abstractmethod
    def prompt_where_to_move(self) -> None:
        """Prompt the user for where to move next."""

    @abstractmethod
    def say_cant_continue(self) -> str:
        """Return a message telling the user there is no save to continue from."""

    @abstractmethod
    def _say_quitting_game(self) -> str:
        """Return a message telling the user the game is quitting."""
