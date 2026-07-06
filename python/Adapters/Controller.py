from UseCases.Interactor import Interactor


class Controller:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    interactor: Interactor

    def __init__(self, interactor: Interactor) -> None:
        self.interactor = interactor

    def handle_new_game(self, name: str, starting_station_id: int) -> None:
        """Start a new game."""
        self.interactor.execute_new_game(name, starting_station_id)
