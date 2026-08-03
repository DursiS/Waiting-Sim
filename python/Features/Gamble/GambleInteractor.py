from Entities import Bet, BetLog, Player

HOUSE_FACTOR = 0.05


class GambleInteractor:
    """
    Orchestrates computing the payoffs of bets laid.
    """

    _bet_records: BetLog

    def execute_gambling(self) -> None:
        """Orchestrates prompts the user for their name, and desire map,
        enters betting phase and automatically into game phase.
        But afterwards prompts if they would like to restart back to the
        betting phase, quit or quit.
        """
        raise NotImplementedError

    def execute_betting_phase(self) -> None:
        """Prompt the user to customize their bet in a nice display of
        options and probabilities of each."""
        raise NotImplementedError

    def execute_game_phase(self) -> None:
        """Execute an automatically advancing Game that doesn't prompt for
        anything and doesn't allow the user any option to quit, restart or
        play again that may cheat the betting system."""
        raise NotImplementedError

    def create_bet(
        self,
        player: Player,
        amount: float,
        interval: tuple[float, float | None],
        end_steps: int | None,
    ) -> Bet | None:
        """Create a new bet, or return none if invalid information was given."""
        if interval and end_steps:
            return None
        elif amount <= 0 or amount > player.balance:
            return None
        elif end_steps <= 0:
            return None

        new_bet = Bet(self._house_payoff_factor(interval, end_steps),
                      amount,
                      interval,
                      end_steps)
        self._bet_records.add_bet(new_bet)
        return new_bet

    def _house_payoff_factor(self, interval: tuple[float, float | None],
                             end_steps: int | None) -> float:
        """Return the public payoff for taking this bet, adjusted
        according to probabilities to get a house edge."""
        raise NotImplementedError
