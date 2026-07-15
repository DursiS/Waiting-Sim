from abc import ABC, abstractmethod

from Entities import Station


class GameInputBoundry(ABC):
    """An interface to decouple Adapter and Business logic."""

    @abstractmethod
    def execute_new_game(
        self,
        name: str,
        starting_station_id: int,
        rand_arrival: bool,
    ) -> tuple[list[Station], Station, list[str]]:
        """Orchestrate a single game."""

    @abstractmethod
    def execute_continue_game(self) -> tuple[list[Station], Station | None, list[str]]:
        """Continue a pre-existing game or start a new one otherwise."""

    @abstractmethod
    def execute_quit_game(self) -> None:
        """Quit the game."""

    @abstractmethod
    def get_world_stations(self) -> list[Station]:
        """Return every station in the world."""
