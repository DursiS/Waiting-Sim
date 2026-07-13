from datetime import timedelta

from UseCases.Game.GameOutputBoundry import GameOutputBoundry


class GamePresenter(GameOutputBoundry):
    def say_expected_times(self, expected_times: dict[str, float | None]) -> str:
        """Return a message describing the expected wait time for each direction."""
        parts = [
            f"{direction}: {'N/A' if time is None else f'{time:.1f}s'}"
            for direction, time in expected_times.items()
        ]
        return f"Expected wait times -- {', '.join(parts)}"

    def say_time_waited(self, t_waited: timedelta, destination: str) -> str:
        """Return a message describing how long the player waited."""
        return f"You waited {t_waited.total_seconds():.1f}s for your ride to arrive to {destination}"

    def say_sequenced_wait_times(self, wait_times: dict[str, float | None]) -> str:
        """Return a message describing the sampled wait time for each direction."""
        parts = [
            f"{direction}: {'N/A' if time is None else f'{time:.1f}s'}"
            for direction, time in wait_times.items()
        ]
        return f"Wait times -- {', '.join(parts)}"

    def say_waiting(self) -> str:
        """Return a message telling the user their ride is on its way."""
        return "Waiting for your ride to arrive..."

    def prompt_to_continue(self) -> str:
        """Return a message prompting the user to continue."""
        return "Press 'c' to continue..."

    def prompt_where_to_move(self) -> None:
        """Prompt the user for where to move next."""
        print("Where would you like to move?")

    def say_cant_continue(self) -> str:
        """Return a message telling the user there is no save to continue from."""
        return "No current save exists."

    def _say_quitting_game(self) -> str:
        """Return a message telling the user the game is quitting."""
        return "Quitting. See you next time!"
