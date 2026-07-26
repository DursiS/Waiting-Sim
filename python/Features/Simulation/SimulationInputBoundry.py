from abc import ABC, abstractmethod


class SimulationInputBoundry(ABC):
    """An input boundry between Simulation Interactor and Controller."""

    @abstractmethod
    def execute_simulation(self, trials: int, steps: int, rand_arrival: bool) -> None:
        """Execute a new simulation."""

    @abstractmethod
    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
