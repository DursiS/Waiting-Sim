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

    def show_stations(self, stations: list[Station]) -> None:
        """Show <stations> as the map the player is on."""
        self.view_model.set_stations(stations)

    def show_player_station(self, station: Station) -> None:
        """Highlight <station> as the player's current location."""
        self.view_model.set_current_station(station)

    def show_total_wait(self, total_wait: float) -> None:
        """Show the player's cumulative wait time so far."""
        self.view_model.set_total_wait(total_wait)

    def show_best_highscore(self, best: dict | None) -> None:
        """Show the current map's best highscore, or N/A if there is none."""
        if best is None:
            self.view_model.set_best_highscore("N/A")
        else:
            self.view_model.set_best_highscore(f"{best['name']} {best['time']:.1f}s")

    def show_loading(self, loading: bool) -> None:
        """Show or hide the animated waiting dots while waiting for trains."""
        self.view_model.set_loading(loading)

    def say_reached_end(self, total_wait: float) -> None:
        """Announce the player reached the end after <total_wait> seconds."""
        self.view_model.add_message(
            f"You reached the end after waiting {total_wait:.1f}s total!"
        )
        self.view_model.add_message("Press P for a new game or Q to quit.")

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
        """Add a message telling the user their ride is on its way.

        The trailing dots are animated by the view model while loading."""
        self.view_model.add_message("Waiting for your ride to arrive")

    def prompt_to_continue(self) -> None:
        """Add a message prompting the user to continue."""
        self.view_model.add_message("Press 'c' to continue...")

    def say_explanation(self) -> None:
        """Add the new-game explanation of how to play and the goal."""
        self.view_model.add_message("Welcome to Waiting-Sim!")
        self.view_model.add_message(
            "Each turn you wait at your station for the next ride; the first to "
            "arrive takes you to that neighbouring station."
        )
        self.view_model.add_message(
            "Expected and sampled wait times are shown so you can read the "
            "network's rhythm."
        )
        self.view_model.add_message(
            "Goal: travel the map with as little total waiting as possible."
        )

    def say_no_save(self) -> None:
        """Add a message telling the user there is no save to continue from."""
        self.view_model.add_message("No current save exists...")

    def say_quitting_game(self) -> None:
        """Add a message telling the user the game is quitting."""
        self.view_model.add_message("Quitting. See you next time!")
