from abc import ABC, abstractmethod


class SimulationInputBoundry(ABC):
    """An input boundry between Game Interactor and Controller."""

    @abstractmethod
    def execute_simulation(self, trials: int, steps: int, map_id: int) -> None:
        """Execute a new simulation on the map with id <map_id>."""

    @abstractmethod
    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
