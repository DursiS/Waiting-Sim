from datetime import timedelta

from Entities import Station
from Features.Game import GameOutputBoundry, GameViewModel


class GamePresenter(GameOutputBoundry):
    view_model: GameViewModel

    def __init__(self, view_model: GameViewModel) -> None:
        self.view_model = view_model

    def clear_messages(self) -> None:
        """Clear the running turn messages before a new turn."""
        self.view_model.clear_messages()

    def clear_wait_stats(self) -> None:
        """Clear the wait-statistics header before a new game."""
        self.view_model.clear_wait_stats()

    def show_station_expectations(
        self, station_stats: list[tuple[str, float, float]]
    ) -> None:
        """Add each station's expected wait time with error bars."""
        self.view_model.add_wait_stat("Expected wait per station:")
        for name, expectation, std_dev in station_stats:
            self.view_model.add_wait_stat(f"{name}: {expectation:.1f} +/- {std_dev:.1f}s")

    def show_map_expectation(self, expectation: float, std_dev: float) -> None:
        """Add the map's total expected wait time with error bars."""
        self.view_model.add_wait_stat(
            f"Map total: {expectation:.1f} +/- {std_dev:.1f}s"
        )

    def show_station_risks(self, station_risks: list[tuple[str, float]]) -> None:
        """Add each station's 95th-percentile risk wait time."""
        self.view_model.add_wait_stat("95th percentile risk:")
        for name, risk in station_risks:
            self.view_model.add_wait_stat(f"{name}: {risk:.1f}s")

    def show_map_risk(self, risk: float) -> None:
        """Add the map's 95th-percentile risk wait time."""
        self.view_model.add_wait_stat(f"Map (95%): {risk:.1f}s")

    def show_player_station(self, station: Station) -> None:
        """Highlight <station> as the player's current location."""
        self.view_model.set_current_station(station)

    def say_expected_times(self, expected_times: dict[str, float | None]) -> None:
        """Add a message describing the expected
        wait time for each direction."""
        parts = [
            f"{direction}: {'N/A' if time is None else f'{time:.1f}s'}"
            for direction, time in expected_times.items()
        ]
        self.view_model.add_message(f"Expected wait times -- {', '.join(parts)}")

    def say_time_waited(self, t_waited: timedelta, destination: str) -> None:
        """Add a message describing how long the player waited."""
        self.view_model.add_message(
            f"You waited {t_waited.total_seconds():.1f}s for your ride to arrive to {destination}"
        )

    def say_sequenced_wait_times(self, wait_times: dict[str, float | None]) -> None:
        """Add a message describing the sampled wait time for each direction."""
        parts = [
            f"{direction}: {'N/A' if time is None else f'{time:.1f}s'}"
            for direction, time in wait_times.items()
        ]
        self.view_model.add_message(f"Wait times -- {', '.join(parts)}")

    def say_waiting(self) -> None:
        """Add a message telling the user their ride is on its way."""
        self.view_model.add_message("Waiting for your ride to arrive...")

    def prompt_to_continue(self) -> None:
        """Add a message prompting the user to continue."""
        self.view_model.add_message("Press 'c' to continue...")

    def say_no_save(self) -> None:
        """Add a message telling the user there is no save to continue from."""
        self.view_model.add_message("No current save exists...")

    def say_quitting_game(self) -> None:
        """Add a message telling the user the game is quitting."""
        self.view_model.add_message("Quitting. See you next time!")
