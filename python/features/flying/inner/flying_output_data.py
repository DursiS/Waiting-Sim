from dataclasses import dataclass


@dataclass
class FlyingOutputData:
    """Raw flying data from the bird's flight."""
    flight_hist: list[tuple[float, float]]
