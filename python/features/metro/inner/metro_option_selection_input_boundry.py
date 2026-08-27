from abc import ABC, abstractmethod


class MetroOptionSelectionInputBoundry(ABC):
    """An interface for the option-selection screen's pre-game queries, keeping
    the menu decoupled from the game interactor."""

    @abstractmethod
    def optimal_bet_amount(
        self, low: int, high: int, map_id: int, balance: float
    ) -> float:
        """Return the Kelly-optimal stake for the [low, high] step interval on
        map <map_id> with <balance>."""

    @abstractmethod
    def bet_payout(self, low: int, high: int, map_id: int, stake: float) -> float:
        """Return the payout on a winning [low, high] bet of <stake> on map
        <map_id>."""

    @abstractmethod
    def optimal_betting_range(self, map_id: int) -> tuple[int, int, float]:
        """Return the globally optimal betting interval and its win probability
        for map <map_id> -- the highest-probability (safest) range."""
