from Entities import Station
from UseCases.Game.GameInputBoundry import GameInputBoundry


class GameController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    input_boundry: GameInputBoundry

    def __init__(self, input_boundry: GameInputBoundry) -> None:
        self.input_boundry = input_boundry

    def handle_new_game(
        self, name: str, starting_station_id: int
    ) -> tuple[list[Station], Station, list[str]]:
        """Start a new game."""
        return self.input_boundry.execute_new_game(name, starting_station_id)

    def handle_continue_game(self) -> tuple[list[Station], Station | None, list[str]]:
        """Continue an existing game."""
        return self.input_boundry.execute_continue_game()

    def get_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self.input_boundry.get_world_stations()
