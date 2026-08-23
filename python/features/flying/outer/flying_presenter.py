from features.flying.inner import FlyingOutputData
from features.flying.inner import Goose
from features.flying.inner import FlyingOutputBoundary
from .flying_view_model import FlyingViewModel


class FlyingPresenter(FlyingOutputBoundary):
    """Adapt a finished flight into the view model the flight screen rolls out."""

    view_model: FlyingViewModel

    def __init__(self, view_model: FlyingViewModel) -> None:
        self.view_model = view_model

    def present_flight(self, outputData: FlyingOutputData) -> None:
        """Hand the full flight history, with the goose's mean and unit, to the
        view model to be rolled out point by point."""
        self.view_model.set_flight(
            outputData.flight_hist, Goose.mean_alt, Goose.unit
        )
