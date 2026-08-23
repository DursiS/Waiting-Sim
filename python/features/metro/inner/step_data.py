from dataclasses import dataclass

from .station import Station


@dataclass
class StepData:
    """Data collected from moving one station over."""

    from_station: Station
    to_station: Station
    wait_time: float
    step_i: int
    trial_i: int
