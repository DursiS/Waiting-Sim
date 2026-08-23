import random

from .metro_output_data import MetroOutputData


class Bet:
    """A single cash -> cash * payoff bet on noe outcome of the game.

    Representation Invariants:
        - 0 < payoff_factor < 1
        - 0 < amount <= balance
        - Both range and end_steps can't be None, and if one is None,
          the other cannot be.
        - end_steps > 0
        - interval acts like (x, y]
    """

    _payoff_factor: float
    _amount: float
    _end_steps: int | None
    _id: int
    _win: bool | None
    _finished: bool

    def __init__(
        self,
        payoff_factor: float,
        amount: float,
        end_steps: int | None,
    ) -> None:
        self._payoff_factor = payoff_factor
        self._amount = amount
        self._end_steps = end_steps
        self._id = random.randint(0, 10**5)
        self._win = None
        self._finished = False

    def id(self) -> int:
        """Return the id of this bet."""
        return self._id

    def get_end_steps(self) -> int:
        """Return the amount of end_steps we bet on."""
        return self._end_steps

    def payout(self, game: MetroOutputData) -> float:
        """Settle this bet against <game>: record whether it won and return the
        winnings (stake times payoff factor) on a win, or 0.0 on a loss."""
        won = len(game.get_results()) == self._end_steps
        self._win = won
        self._finished = True
        return self._amount * self._payoff_factor if won else 0.0

    def result(self) -> dict:
        """Return this settled bet's outcome: its target step count, stake,
        whether it won, and the winnings paid on a win."""
        return {
            "end_steps": self._end_steps,
            "amount": self._amount,
            "won": bool(self._win),
            "winnings": self._amount * self._payoff_factor if self._win else 0.0,
        }
