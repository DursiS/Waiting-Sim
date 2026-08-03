import random

import numpy as np

from Entities import GameState


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
    _interval: tuple[float, float] | None
    _end_steps: int | None
    _id: int
    _win: bool | None
    _finished: bool

    def __init__(
        self,
        payoff_factor: float,
        amount: float,
        interval: tuple[float, float] | None,
        end_steps: int | None,
    ) -> None:
        self._payoff_factor = payoff_factor
        self._amount = amount
        self._interval = interval
        self._end_steps = end_steps
        self._id = random.randint(0, 10**5)
        self._win = None
        self._finished = False

    def id(self) -> int:
        """Return the id of this bet."""
        return self._id

    def payout(self, game: GameState) -> float:
        """Settle this bet against <game>: record whether it won and return the
        winnings (stake times payoff factor) on a win, or 0.0 on a loss."""
        if self._interval is not None:
            x, y = self._interval
            won = x < game.wait_time <= y
        else:
            won = game.end_steps == self._end_steps
        self._win = won
        self._finished = True
        return self._amount * self._payoff_factor if won else 0.0
