from Features.Simulation import SimulationInteractor


class SimulationController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    input_boundry: SimulationInteractor

    def __init__(self, input_boundry: SimulationInteractor) -> None:
        self.input_boundry = input_boundry

    def handle_simulation(self, trials: int, steps: int, rand_arrival: bool) -> None:
        """Simulation <trials> many trials with <steps> steps."""
        self.input_boundry.execute_simulation(trials, steps, rand_arrival)
