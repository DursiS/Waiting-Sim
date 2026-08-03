from Entities import Bet, BetRecords, Player


class GambleInteractor:
    """
    Orchestrates computing the payoffs of bets laid.
    """

    _bet_records: BetRecords

    def create_bet(
        self,
        player: Player,
        amount: float,
        range: tuple[float, float | None],
        end_steps: int | None,
    ) -> Bet | None:
        """Create a new bet, or return none if invalid information was given."""
        if range and end_steps:
            return
        elif amount <= 0 or amount > player.balance:
            return
        elif end_steps <= 0:
            return

        factor = 1  # Some function of probability of the valid outcome.
        new_bet = Bet(factor, amount, range, end_steps)
        self._bet_records.add_bet(new_bet)
        return new_bet
