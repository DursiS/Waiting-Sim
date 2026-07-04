from abc import ABC, abstractmethod


class AdapterGateway(ABC):
    """An interface to decouple Adapter and Business logic."""

    @abstractmethod
    def handle_new_game(self, name: str, starting_station_id: int) -> None:
        """Start a new game."""
