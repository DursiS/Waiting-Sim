from Entities.Entities import TurnResult


class GameOutputData:
    """The result of one Game."""

    phase_id: int
    _turn_results: list[TurnResult]
    gamble: bool
    rand_arrival: bool
    payout: float = 0.0

    def __init__(self, phase_id, turn_results, gamble, rand_arrival, payout) -> None:
        self.phase_id = phase_id
        self._turn_results = turn_results
        self.gamble = gamble
        self.rand_arrival = rand_arrival
        self.payout = payout

    def get_results(self) -> list[TurnResult]:
        """Return the history of turns and what happened on them."""
        return self._turn_results
