from features.flying.inner import FlyingInputData
from features.flying.inner import FlyingInteractor
from features.flying.inner import FlyingOutputBoundary


SECONDS_PER_MINUTE = 60.0


class FlyingController:
    """Convert the player's flight request into an interactor run."""

    _presenter: FlyingOutputBoundary

    def __init__(self, presenter: FlyingOutputBoundary) -> None:
        self._presenter = presenter

    def handle_fly(self, minutes: float) -> None:
        """Translate the duration from minutes into seconds for the goose's dt,
        then run the flight."""
        input_data = FlyingInputData(minutes * SECONDS_PER_MINUTE)
        FlyingInteractor(input_data, self._presenter).execute_flight()
