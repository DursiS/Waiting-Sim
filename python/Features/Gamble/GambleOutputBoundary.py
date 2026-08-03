from abc import ABC, abstractmethod

from Entities import GameState


class GambleOutputBoundary(ABC):
    """An interface to decouple the gamble adapter from its business logic.

    The interactor asks its questions through here so they are shown in a view
    model rather than read from the console; the View renders the current
    question and feeds the answer back to the interactor."""

    @abstractmethod
    def ask_name(self) -> None:
        """Ask the player for their name."""

    @abstractmethod
    def ask_map(self, map_ids: list[int]) -> None:
        """Ask the player which of <map_ids> to play."""

    @abstractmethod
    def ask_bet_amount(self, balance: float) -> None:
        """Ask for a stake to lay, given the player's <balance>."""

    @abstractmethod
    def ask_bet_target(self) -> None:
        """Ask whether the bet is on a wait-time interval or steps to finish."""

    @abstractmethod
    def ask_bet_interval(self) -> None:
        """Ask for the wait-time interval to bet on."""

    @abstractmethod
    def ask_bet_steps(self) -> None:
        """Ask for the exact number of steps to finish to bet on."""

    @abstractmethod
    def ask_another_bet(self) -> None:
        """Ask whether the player wants to lay another bet."""

    @abstractmethod
    def say_invalid(self, what: str) -> None:
        """Tell the player their <what> entry was invalid."""

    @abstractmethod
    def say_bet_placed(self, amount: float, description: str) -> None:
        """Confirm a bet of <amount> described by <description> was placed."""

    @abstractmethod
    def say_bets_locked(self) -> None:
        """Announce the betting phase is closed and the game is starting."""

    @abstractmethod
    def say_game_result(self, game: GameState) -> None:
        """Report the finished game's outcome."""

    @abstractmethod
    def say_payout(self, payout: float, balance: float) -> None:
        """Report the total <payout> and the player's resulting <balance>."""

    @abstractmethod
    def end_round(self) -> None:
        """Close the round: clear the question and invite play-again or quit."""
