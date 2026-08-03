from abc import ABC, abstractmethod


class GambleInputBoundary(ABC):
    """An interface to decouple the gamble adapter from its business logic.

    The flow is a single-field question/answer loop: the interactor asks the
    next question through the output boundary, and the View submits the typed
    answer back through here."""

    @abstractmethod
    def start(self) -> None:
        """Begin a new gamble round by asking the first question."""

    @abstractmethod
    def submit(self, answer: str) -> None:
        """Handle <answer> to the question currently being asked."""
