from Entities import GameState
from Features.Gamble import GambleOutputBoundary, GambleViewModel


class GamblePresenter(GambleOutputBoundary):
    """Turns interactor questions and results into updates on the gamble view
    model, so the View can render them."""

    view_model: GambleViewModel

    def __init__(self, view_model: GambleViewModel) -> None:
        """Create a presenter feeding <view_model>."""
        self.view_model = view_model

    def ask_name(self) -> None:
        """Ask the player for their name."""
        self.view_model.set_prompt("Enter your name:")

    def ask_map(self, map_ids: list[int]) -> None:
        """Ask the player which of <map_ids> to play."""
        ids = "/".join(str(m) for m in map_ids)
        self.view_model.set_prompt(f"Choose a map ({ids}):")

    def ask_bet_amount(self, balance: float) -> None:
        """Ask for a stake to lay, given the player's <balance>."""
        self.view_model.set_prompt(
            f"Bet amount (balance {balance:.2f}), or blank to finish betting:"
        )

    def ask_bet_target(self) -> None:
        """Ask whether the bet is on a wait-time interval or steps to finish."""
        self.view_model.set_prompt(
            "Bet on wait-time (i)nterval or (s)teps to finish?"
        )

    def ask_bet_interval(self) -> None:
        """Ask for the wait-time interval to bet on."""
        self.view_model.set_prompt("Wait-time interval as 'low high':")

    def ask_bet_steps(self) -> None:
        """Ask for the exact number of steps to finish to bet on."""
        self.view_model.set_prompt("Exact number of steps to finish:")

    def ask_another_bet(self) -> None:
        """Ask whether the player wants to lay another bet."""
        self.view_model.set_prompt("Place another bet? (y/n)")

    def say_invalid(self, what: str) -> None:
        """Tell the player their <what> entry was invalid."""
        self.view_model.add_message(f"Invalid {what}; please try again.")

    def say_bet_placed(self, amount: float, description: str) -> None:
        """Confirm a bet of <amount> described by <description> was placed."""
        self.view_model.add_message(f"Placed {amount:.2f} on {description}.")

    def say_bets_locked(self) -> None:
        """Announce the betting phase is closed and the game is starting."""
        self.view_model.add_message("Bets are locked. Running the game...")

    def say_game_result(self, game: GameState) -> None:
        """Report the finished game's outcome."""
        self.view_model.add_message(
            f"Game finished in {game.end_steps} steps, "
            f"waiting {game.wait_time:.1f}s."
        )

    def say_payout(self, payout: float, balance: float) -> None:
        """Report the total <payout> and the player's resulting <balance>."""
        self.view_model.add_message(
            f"Payout {payout:.2f}. Balance is now {balance:.2f}."
        )

    def end_round(self) -> None:
        """Close the round: clear the question and invite play-again or quit."""
        self.view_model.set_prompt("")
        self.view_model.add_message("Round over. Press Enter to play again, Esc to quit.")
