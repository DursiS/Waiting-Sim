from abc import ABC, abstractmethod

from Entities import GameInputData, GameOutputData, Player


class GameInputBoundry(ABC):
    """An interface to decouple Adapter and Business logic."""

    @abstractmethod
    def execute(self, player: Player | None, inputData: GameInputData) -> None:
        """Set up and run the full game described by <inputData>, presenting each
        turn and the finished result. When gambling, its raw bet data is placed
        before the game and settled against the outcome."""

    @abstractmethod
    def execute_restart(self) -> GameOutputData | None:
        """Replay the last game with the same settings, or None if there was
        none."""

    @abstractmethod
    def get_map_ids(self) -> list[int]:
        """Return the ids of every selectable map."""

    @abstractmethod
    def get_balance(self) -> float:
        """Return the balance the next game's player bets with."""
