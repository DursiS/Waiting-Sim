from dataclasses import dataclass


@dataclass
class GameState:
    """The result of one Game."""

    phase_id: int
    end_steps: int
    wait_time: float
