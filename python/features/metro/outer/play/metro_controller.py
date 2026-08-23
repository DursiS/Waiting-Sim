from features.metro.inner import MetroInputData, MetroOutputData, Player
from features.metro.inner import MetroInputBoundry


class MetroController:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    input_boundry: MetroInputBoundry

    def __init__(self, input_boundry: MetroInputBoundry) -> None:
        self.input_boundry = input_boundry

    def handle_play(
        self,
        player: Player | None,
        name: str,
        map_id: int,
        rand_arrival: bool,
        gamble: bool,
        raw_bets: list | None,
        animate: bool,
    ) -> None:
        """Package the chosen settings into a request and run the game, settling
        <raw_bets> against the outcome when gambling."""
        input_data = MetroInputData(
            name=name,
            map_id=map_id,
            rand_arrival=rand_arrival,
            gamble=gamble,
            raw_bets=raw_bets,
            animate=animate,
        )
        self.input_boundry.execute(player, input_data)

    def handle_restart(self) -> MetroOutputData | None:
        """Replay the last game with the same settings."""
        return self.input_boundry.execute_restart()

    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""
        return self.input_boundry.get_map_ids()

    def get_balance(self) -> float:
        """Return the balance available to bet with."""
        return self.input_boundry.get_balance()
