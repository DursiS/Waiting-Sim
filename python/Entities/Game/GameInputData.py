from dataclasses import dataclass


@dataclass
class GameInputData:
    """Configurations for how the game should run."""

    name: str
    map_id: int
    rand_arrival: bool
    gamble: bool
    raw_bets: list | None
    animate: bool = True
