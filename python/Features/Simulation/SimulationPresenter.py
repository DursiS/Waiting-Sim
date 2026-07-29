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

    def say_executing_simulation(
        self, trials: int, steps: int, rand_arrival: bool
    ) -> None:
        """Announce a simulation of <trials> trials of <steps> steps is running."""
        self.view_model.add_message(f"Running {trials} trials of {steps} steps...")

    def say_done_trials(self) -> None:
        """Announce every trial has finished and results are being digested."""
        self.view_model.add_message("Done. Digesting results.")

    def show_results(self, grid: dict[tuple[int, int], object]) -> None:
        """Display the digested metric grid, keyed by (row, column)."""
        for (row, col), value in grid.items():
            self.view_model.set_value(row, col, self._format(value))

    def _format(self, value: object) -> str:
        """Render a metric value as a compact cell string."""
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)
