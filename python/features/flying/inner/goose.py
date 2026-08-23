import math


class Goose:
    """A long-head goose."""

    flight_hist: list[tuple[float, float]]
    pos: tuple[float, float]  # (x, y) with x,y > 0
    mean_alt: float = 5500.0
    unit: str = "feet"
    dt: float = 1

    def __init__(self) -> None:
        # self.pos = (0.0, self.mean_alt)
        self.pos = (0.0, 1.0)
        self.flight_hist = [self.pos]

    def flap(self, y: float) -> None:
        """Flap wings once, advancing time by dt to height and recording it."""
        if y < 0:
            self.pos = self.pos[0] + self.dt, 0
        else:
            self.pos = self.pos[0] + self.dt, y
        self.flight_hist.append(self.pos)

    def fly(self, y_path: list[float]) -> None:
        """Have the goose flap multiple times in a row."""
        for i in range(len(y_path)):
            self.flap(y_path[i])

    def num_flaps(self, duration: float) -> int:
        """Return how many times the goose will flap in an amount of time."""
        return math.floor(duration / self.dt)

    def get_flight_history(self) -> list[tuple[float, float]]:
        """Return a copy of the flight history of bird."""
        return self.flight_hist[:]

    def mean(self) -> float:
        """Return the mean altitude this bird flies at."""
        return self.mean_alt
