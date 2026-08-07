from Entities import Bet, GameOutputData


class BetLog:
    """A history of all bets made."""

    _history: dict[int, tuple[list[Bet] | tuple[Bet, ...], GameOutputData | None]]

    def __init__(self) -> None:
        self._history = {}

    def new_betting_phase(self) -> int:
        """Return the id for a new log of bets for a new betting phase."""
        n = max(self._history, default=-1) + 1
        self._history[n] = ([], None)
        return n

    def add_bet(self, n: int, bet: Bet) -> None:
        """Add a bet to the log of a specific betting phase."""
        self._history[n][0].append(bet)

    def remove_bet(self, n: int, bet_id: int) -> bool:
        """Remove the bet with <bet_id> from phase <n>, returning whether it
        was found."""
        for bet in self._history[n][0]:
            if bet.id() == bet_id:
                self._history[n][0].remove(bet)
                return True
        return False

    def complete_phase(self, n: int) -> None:
        """End a betting phase by locking its bets so none can be added."""
        bets, game_state = self._history[n]
        self._history[n] = (tuple(bets), game_state)

    def get_bets(self, n: int) -> tuple[Bet, ...] | None:
        """Return all the bets of a specific phase, or None
        if the phase is not complete yet."""
        if not isinstance(self._history[n][0], tuple):
            return None
        return self._history[n][0]
