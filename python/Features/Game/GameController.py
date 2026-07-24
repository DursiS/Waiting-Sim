from Entities import Station
from Features.Game import GameInputBoundry


class GameController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    input_boundry: GameInputBoundry

    def __init__(self, input_boundry: GameInputBoundry) -> None:
        self.input_boundry = input_boundry

    def handle_new_game(
        self,
        name: str,
        map_id: int,
        rand_arrival: bool,
    ) -> None:
        """Start a new game on the map with id <map_id>."""
        self.input_boundry.execute_new_game(
            name,
            map_id,
            rand_arrival,
        )

    def handle_continue_game(self) -> None:
        """Continue an existing game."""
        self.input_boundry.execute_continue_game()

    def get_stations(self) -> list[Station]:
        """Return every station in the world."""
        return self.input_boundry.get_world_stations()

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self.input_boundry.get_map_ids()
