from Entities import Bet


class BetLog:
    """A history of all bets made."""

    _history: list[Bet]

    def __init__(self) -> None:
        self._history = []

    def add_bet(self, bet: Bet) -> None:
        self._history.append(bet)

    def remove_bet(self, _id: int) -> bool:
        for bet in self._history:
            if bet.id() == _id:
                self._history.remove(bet)
                return True
        return False
