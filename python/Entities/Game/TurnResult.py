from dataclasses import dataclass

from Entities import Station


@dataclass
class TurnResult:
    """The result of a single step taken in Game."""

    _to: Station
    _from: Station
    t_travel: float
    t_waited: float
    probabilities: dict[int, float]
