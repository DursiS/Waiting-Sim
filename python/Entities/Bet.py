class Bet:
    """A single cash -> cash * payoff bet on noe outcome of the game.

    Representation Invariants:
        - 0 < payoff_factor < 1
        - 0 < amount <= balance
        - Both range and end_steps can't be None, and if one is None,
          the other cannot be.
        - end_steps > 0
    """

    payoff_factor: float
    amount: float
    range: tuple[float, float] | None
    end_steps: int | None
