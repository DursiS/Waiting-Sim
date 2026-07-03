from datetime import timedelta

from scipy import stats

from Framework import WaitRules


class RulesController:
    """Applies parameter changes to a WaitRules instance."""

    _wait_rules: WaitRules

    def __init__(self, wait_rules: WaitRules) -> None:
        self._wait_rules = wait_rules

    def set_dt(self, dt: timedelta) -> None:
        """Set dt."""
        self._wait_rules.dt = dt

    def set_coinflip_cove(self, p: float) -> None:
        """Set Coinflip Cove's p."""
        self._wait_rules.set_rule("Coinflip Cove", stats.geom(p=p))

    def set_patience_point(self, n: int, p: float) -> None:
        """Set Patience Point's n and p."""
        self._wait_rules.set_rule("Patience Point", stats.nbinom(n=n, p=p))

    def set_poisson_plaza(self, mu: float) -> None:
        """Set Poisson Plaza's mu."""
        self._wait_rules.set_rule("Poisson Plaza", stats.poisson(mu=mu))

    def set_binomial_bazaar(self, n: int, p: float) -> None:
        """Set Binomial Bazaar's n and p."""
        self._wait_rules.set_rule("Binomial Bazaar", stats.binom(n=n, p=p))

    def set_dice_depot(self, low: int, high: int) -> None:
        """Set Dice Depot's low and high."""
        self._wait_rules.set_rule("Dice Depot", stats.randint(low=low, high=high))
