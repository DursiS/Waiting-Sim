from abc import ABC, abstractmethod


class FlyingInputBoundary(ABC):
    """Boundary decoupling Flying's controller from its interactor."""

    @abstractmethod
    def execute_flight(self) -> None:
        """Run the flight simulation and hand its history to the presenter."""
