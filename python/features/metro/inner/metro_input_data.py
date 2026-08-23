from dataclasses import dataclass


@dataclass
class MetroInputData:
    """Configurations for how the game should run."""

    name: str
    map_id: int
    rand_arrival: bool
    gamble: bool
    raw_bets: list | None
    animate: bool = True
