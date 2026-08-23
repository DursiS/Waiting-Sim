import numpy as np
import scipy
from numpy import ndarray

from .flying_input_data import FlyingInputData
from .flying_output_data import FlyingOutputData
from .goose import Goose
from .flying_input_boundary import FlyingInputBoundary
from .flying_output_boundary import FlyingOutputBoundary


class FlyingInteractor(FlyingInputBoundary):
    """Orchestrating enterprise logic for the flight simulation."""

    _goose: Goose
    _duration: float
    _presenter: FlyingOutputBoundary

    def __init__(
        self, inputData: FlyingInputData, presenter: FlyingOutputBoundary
    ) -> None:
        self._duration = inputData.duration
        self._goose = Goose()
        self._presenter = presenter

    def execute_flight(self) -> None:
        """Run the flight simulation and send the raw data to be displayed.

        Each flap steps the height by <_dy> off the current position, growing
        the goose's history so the next step's mean-reversion reads the walk so
        far."""
        for _ in range(self._goose.num_flaps(self._duration)):
            y_t = self._goose.flight_hist[-1][-1]
            self._goose.flap(y_t + self._dy(self._goose))
        outputData = FlyingOutputData(self._goose.get_flight_history())
        self._presenter.present_flight(outputData)

    def _dy(self, goose: Goose) -> float:
        """Compute which height the goose should be next based on
        a random, mean reverting process with noise."""
        y_t = goose.flight_hist[-1][-1]
        theta = self._ar_score(goose.flight_hist)
        pull = theta * (goose.mean() - y_t) * goose.dt

        sigma = 450
        noise = sigma * np.random.normal(0, goose.dt)

        return pull + noise

    # def _calibrate_noise_parameters(
    #     self, y_path: list[float]
    # ) -> tuple[float, float, float]:
    #     return 0.5, 0.5, 0.5
    #
    # def _get_estimated_path(self, y_path: ndarray) -> list[float]:
    #     """Return a list of estimate true path of flight."""
    #     process_noise, observation_noise, p0 = self._calibrate_noise_parameters(y_path)
    #
    #     first_estimates = y_path - observation_noise
    #     estimates = []
    #     confidences = []
    #
    #     p = p0
    #     x = first_estimates[0]
    #
    #     for point in first_estimates[1:]:
    #         p = p + process_noise
    #
    #         kalman = p / (p + observation_noise)
    #         x = x + kalman * (point - x)
    #         p = (1 - kalman) * p
    #
    #         estimates.append(x)
    #         confidences.append(p)
    #     return estimates

    def _ar_score(self, flight_hist: list[tuple[float, float]]) -> float:
        """Return the AR(1) coefficient estimated from the flight history."""

        sum_of_multiples = sum(pos[0] * pos[1] for pos in flight_hist)
        sum_of_squares = sum(pos[1] ** 2 for pos in flight_hist)
        if len(flight_hist) == 0 or sum_of_squares == 0:
            return float("inf")

        return sum_of_multiples / sum_of_squares
