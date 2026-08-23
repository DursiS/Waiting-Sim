from abc import ABC, abstractmethod

from .flying_output_data import FlyingOutputData


class FlyingOutputBoundary(ABC):
    """Boundary between Flying's inner/outer layers of output."""

    @abstractmethod
    def present_flight(self, outputData: FlyingOutputData) -> None:
        """Hand the full flight history to the view, to be rolled out as an
        animated bird flying through a cloudy sky at 60 frames a second."""
