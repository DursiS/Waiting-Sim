from Features.Game.GameViewModel import GameViewModel
from Features.Simulation.SimulationViewModel import SimulationViewModel


class ViewModelFacade:
    """A facade over the app's view models, controlling which is active."""

    game_view_model: GameViewModel
    simulation_view_model: SimulationViewModel

    def __init__(
        self, game_view_model: GameViewModel, simulation_view_model: SimulationViewModel
    ) -> None:
        """Create a ViewModelFacade holding every feature's view model."""
        self.game_view_model = game_view_model
        self.simulation_view_model = simulation_view_model

    def start_game(self) -> None:
        """Activate the game view model."""
        self.game_view_model._running = True

    def start_simulation(self) -> None:
        """Activate the simulation view model."""
        self.simulation_view_model._running = True
