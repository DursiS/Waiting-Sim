from datetime import timedelta
from typing import Callable

from scipy import stats


STATIONS = {
    "Coinflip Cove": stats.geom(p=0.30),
    "Patience Point": stats.nbinom(n=4, p=0.40),
    "Poisson Plaza": stats.poisson(mu=3.0),
    "Binomial Bazaar": stats.binom(n=10, p=0.35),
    "Dice Depot": stats.randint(low=1, high=7),
}


class WaitRules:
    """Rules to determine how waiting time is configured.

    Representation Invariants:
        - name must be a valid distribution scipy stats methods

    Public Attributes:
        - _rule_map is a dictionary mapping station names to their
        default distributions.
    """

    _rule_map: dict[str, Callable]
    dt: timedelta

    def __init__(self, rule_map: dict, dt: timedelta = timedelta(seconds=1)) -> None:
        self._rule_map = rule_map
        self.dt = dt

    def wait_time(self, name: str) -> timedelta:
        """Return the amount of dt the user must wait."""
        return self._rule_map[name].rvs() * self.dt

    def get_dt(self) -> timedelta:
        """Return dt."""
        return self.dt

    def set_dt(self, dt: timedelta) -> None:
        """Set dt."""
        self.dt = dt
