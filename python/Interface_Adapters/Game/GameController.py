from Entities import Station
from UseCases.Game.GameInteractor import GameInteractor


class GameController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    interactor: GameInteractor

    def __init__(self, interactor: GameInteractor) -> None:
        self.interactor = interactor

    def handle_new_game(
        self, name: str, starting_station_id: int
    ) -> tuple[list[Station], Station, list[str]]:
        """Start a new game."""
        return self.interactor.execute_new_game(name, starting_station_id)

    def handle_continue_game(self) -> tuple[list[Station], Station | None, list[str]]:
        """Continue an existing game."""
        return self.interactor.execute_continue_game()

    def get_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self.interactor.get_world_stations()
