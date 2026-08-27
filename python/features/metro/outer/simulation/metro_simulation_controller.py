from features.metro.inner import MetroSimulationInteractor


class MetroSimulationController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    input_boundry: MetroSimulationInteractor

    def __init__(self, input_boundry: MetroSimulationInteractor) -> None:
        self.input_boundry = input_boundry

    def handle_simulation(self, name: str, map_id: int, trials: int) -> None:
        """Run <trials> walks to the end on the map with id <map_id>."""
        self.input_boundry.execute_simulation(trials, map_id)

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self.input_boundry.get_map_ids()
