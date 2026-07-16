from Features.Simulation import SimulationViewModel


class ViewModelFacade:
    """A facade over the app's flag-driven view models, controlling which
    is active."""

    simulation_view_model: SimulationViewModel

    def __init__(self, simulation_view_model: SimulationViewModel) -> None:
        """Create a ViewModelFacade holding every flag-driven feature's
        view model."""
        self.simulation_view_model = simulation_view_model

    def start_simulation(self) -> None:
        """Activate the simulation view model."""
        self.simulation_view_model._running = True
