from Features.Simulation import SimulationInteractor


class SimulationController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    input_boundry: SimulationInteractor

    def __init__(self, input_boundry: SimulationInteractor) -> None:
        self.input_boundry = input_boundry
