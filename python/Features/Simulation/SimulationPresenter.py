import numpy as np

import Audio
from Entities import Station
from Features.Simulation import SimulationOutputBoundry, SimulationViewModel


class SimulationPresenter(SimulationOutputBoundry):
    """Turns interactor output into updates on the simulation view model."""

    view_model: SimulationViewModel

    def __init__(self, view_model: SimulationViewModel) -> None:
        """Create a presenter feeding <view_model>."""
        self.view_model = view_model

    def clear_messages(self) -> None:
        """Clear the running messages before a new simulation."""
        self.view_model.clear_messages()

    def say_executing_simulation(self, trials: int, steps: int) -> None:
        """Announce a simulation of <trials> trials of <steps> steps is running."""
        self.view_model.add_message(f"Running {trials} trials of {steps} steps...")

    def say_done_trials(self) -> None:
        """Announce every trial has finished and results are being digested."""
        self.view_model.add_message("Done. Digesting results.")

    def show_loading(self, loading: bool) -> None:
        """Show or hide the animated dots while trials are running."""
        self.view_model.set_loading(loading)

    def show_results(self, grid: dict[tuple[int, int], object]) -> None:
        """Display the digested metric grid, keyed by (row, column)."""
        for (row, col), value in grid.items():
            self.view_model.set_value(row, col, self._format(value))
        Audio.play("ding")

    def _format(self, value: object) -> str:
        """Render a metric value for its cell: a name for a station, a text
        block for a matrix, error bars for a (mean, std) pair, else a number."""
        if isinstance(value, Station):
            return value.name
        if isinstance(value, np.ndarray):
            return self._format_matrix(value)
        if isinstance(value, tuple):
            if value and isinstance(value[0], np.ndarray):
                return self._format_matrix(value[0])
            if len(value) == 2 and all(self._is_number(v) for v in value):
                mean, std = value
                return f"{mean:.2f} +/- {std:.2f}"
        if self._is_number(value):
            return f"{value:.2f}"
        return str(value)

    def _format_matrix(self, matrix: np.ndarray) -> str:
        """Render a matrix as a newline-separated block of aligned rows."""
        rows = np.atleast_2d(np.round(matrix, 2))
        return "\n".join(" ".join(f"{x:.2f}" for x in row) for row in rows)

    def _is_number(self, value: object) -> bool:
        """Return whether <value> is a real scalar number."""
        return isinstance(value, (int, float, np.integer, np.floating))
