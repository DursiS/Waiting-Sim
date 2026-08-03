from Features.Gamble import GambleInputBoundary


class GambleController:
    """Controller per CA to convert View input into interactor calls."""

    input_boundary: GambleInputBoundary

    def __init__(self, input_boundary: GambleInputBoundary) -> None:
        """Create a controller driving <input_boundary>."""
        self.input_boundary = input_boundary

    def handle_start(self) -> None:
        """Begin a new gamble round."""
        self.input_boundary.start()

    def handle_answer(self, answer: str) -> None:
        """Submit the player's typed <answer> to the current question."""
        self.input_boundary.submit(answer)
