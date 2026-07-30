from abc import ABC, abstractmethod


class SimulationOutputBoundry(ABC):
    """An output boundary the interactor uses to report simulation progress
    and results, decoupling business logic from the view."""

    @abstractmethod
    def clear_messages(self) -> None:
        """Clear the running messages before a new simulation."""

    @abstractmethod
    def say_executing_simulation(self, trials: int, steps: int) -> None:
        """Announce a simulation of <trials> trials of <steps> steps is running."""

    @abstractmethod
    def say_done_trials(self) -> None:
        """Announce every trial has finished and results are being digested."""

    @abstractmethod
    def show_loading(self, loading: bool) -> None:
        """Show or hide the animated dots while trials are running."""

    @abstractmethod
    def show_results(self, grid: dict[tuple[int, int], object]) -> None:
        """Display the digested metric grid, keyed by (row, column)."""
