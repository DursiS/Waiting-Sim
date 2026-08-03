import random

import numpy as np


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

    def id(self) -> int:
        return self._id
