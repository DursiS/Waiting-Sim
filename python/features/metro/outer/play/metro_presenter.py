import time
from datetime import timedelta

from app import audio
from features.metro.inner import MetroOutputData, Station
from features.metro.inner import TurnResult
from features.metro.inner import MetroOutputBoundry
from .metro_view_model import MetroViewModel

REPLAY_PROMPT = "Press R to restart this map, P to play a different map, or Q to quit."


class MetroPresenter(MetroOutputBoundry):
    view_model: MetroViewModel
    _animate: bool

    def __init__(self, view_model: MetroViewModel) -> None:
        self.view_model = view_model
        self._animate = True

    def present_game_setup(
        self,
        stations: list[Station],
        roads: list[tuple[tuple[int, int], tuple[int, int]]],
        spawn: Station,
        gamble: bool,
        animate: bool,
    ) -> None:
        """Show the map and reset the HUD for a fresh game, remembering whether
        to animate turns."""
        self._animate = animate
        self.view_model.set_phase("game")
        self.show_stations(stations)
        self.show_roads(roads)
        self.view_model.set_show_controls(False)
        self.view_model.set_bet_result(None)
        self.view_model.set_game_over(False)
        self.clear_messages()
        self.show_total_wait(0.0)
        self.view_model.set_steps(0)
        self.show_player_station(spawn)

    def present_bets(self, bets: list[tuple[int, int, float]]) -> None:
        """Register the placed bets and their prior odds so the HUD can track
        each one's win probability and fair odds through the game."""
        self.view_model.set_bet_targets(bets)

    def present_game_turn(self, turn: TurnResult) -> None:
        """Animate one played turn: wait for the ride (dots, no train) for the
        real wait time, then depart and travel to the next station over the real
        travel time, updating the HUD and chiming on arrival. When not
        animating, the turn is presented instantly with no waiting."""
        self.show_player_station(turn._from)
        self.clear_messages()
        self.say_waiting()
        self.show_loading(True)
        if self._animate:
            time.sleep(turn.t_waited.total_seconds())

        self.show_loading(False)
        self.say_time_waited(turn.t_waited, turn._to.name)
        self.say_travelling(turn.t_travel, turn._to.name)
        self.show_incoming_train(
            turn._to, turn.t_travel.total_seconds(), turn.t_waited.total_seconds()
        )
        self.show_loading(True)
        if self._animate:
            time.sleep(turn.t_travel.total_seconds())

        self.show_loading(False)
        self.show_player_station(turn._to)
        self.show_total_wait(
            self.view_model.total_wait
            + turn.t_waited.total_seconds()
            + turn.t_travel.total_seconds()
        )
        self.chime_arrival()
        self.view_model.set_steps(self.view_model.steps + 1)
        self.view_model.set_bet_odds(turn.probabilities)

    def present_game_state(self, game: MetroOutputData) -> None:
        """Present the finished game: the total wait, then the closing message.

        The kind of close is inferred from the MetroOutputData: a plain play shows
        the reached-end message, a gamble shows its bet result read off the
        settled payout carried on the output object."""
        total_wait = sum(
            turn.t_waited.total_seconds() + turn.t_travel.total_seconds()
            for turn in game._turn_results
        )
        self.show_total_wait(total_wait)
        self.clear_messages()
        if game.gamble:
            self._present_bet_result(game)
        else:
            self.say_reached_end(total_wait)
        self.show_game_over(True)

    def _present_bet_result(self, game: MetroOutputData) -> None:
        """Show the gamble's outcome in the HUD: how many steps the game took,
        each bet's result and the net payout, then the replay prompt."""
        steps = len(game.get_results())
        lines = [f"Reached the end in {steps} steps"]
        if game.bet_results:
            lows = [bet["end_steps"] for bet in game.bet_results]
            low, high = min(lows), max(lows)
            span = f"{low} steps" if low == high else f"{low}-{high} steps"
            stake = game.bet_results[0]["amount"]
            if game.payout > 0:
                lines.append(f"Bet {stake:.2f} on {span}  ->  WON +{game.payout:.2f}")
            else:
                lines.append(f"Bet {stake:.2f} on {span}  ->  LOST")
        else:
            lines.append("No bets placed.")
        lines.append(f"Net payout: {game.payout:+.2f}")
        lines.append("Press R to restart or Q to quit")
        self.view_model.set_bet_result("\n".join(lines))
        audio.play("victory" if game.payout > 0 else "lose")

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
            self.view_model.add_wait_stat(
                f"{name}: {expectation:.1f} +/- {std_dev:.1f}s"
            )

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

    def show_stations(self, stations: list[Station]) -> None:
        """Show <stations> as the map the player is on."""
        self.view_model.set_stations(stations)

    def show_roads(self, roads: list[tuple[tuple[int, int], tuple[int, int]]]) -> None:
        """Draw the world's roads, each an ordered (from, to) coordinate pair."""
        self.view_model.set_roads(roads)

    def show_player_station(self, station: Station) -> None:
        """Highlight <station> as the player's current location."""
        self.view_model.set_current_station(station)

    def show_total_wait(self, total_wait: float) -> None:
        """Show the player's cumulative wait time so far."""
        self.view_model.set_total_wait(total_wait)

    def show_loading(self, loading: bool) -> None:
        """Show or hide the animated waiting dots while waiting for trains."""
        self.view_model.set_loading(loading)

    def show_incoming_train(
        self, destination: Station, seconds: float, wait_seconds: float
    ) -> None:
        """Depart the winning train toward <destination>, travelling <seconds>,
        after <wait_seconds> spent waiting for it."""
        self.view_model.set_incoming_train(destination, seconds, wait_seconds)

    def chime_arrival(self) -> None:
        """Sound a soft chime as the player arrives at a station mid-game."""
        audio.play("soft_ding")

    def show_game_over(self, game_over: bool) -> None:
        """Clear the turn HUD and show only the closing message, or resume."""
        self.view_model.set_game_over(game_over)

    def say_reached_end(self, total_wait: float) -> None:
        """Announce the player reached the end after <total_wait> seconds."""
        audio.play("ding")
        self.view_model.add_message(
            f"You reached the end after waiting {total_wait:.1f}s total!"
        )
        self.view_model.add_message(REPLAY_PROMPT)

    def say_already_finished(self) -> None:
        """Tell the player this game is over, so there is nothing to continue."""
        self.view_model.add_message(
            "You are already at the end -- this game is finished."
        )
        self.view_model.add_message(REPLAY_PROMPT)

    def say_expected_times(self, expected_times: list[tuple[str, float]]) -> None:
        """Add a message describing the expected wait time to each neighbour."""
        parts = [f"{name}: {seconds:.1f}s" for name, seconds in expected_times]
        self.view_model.add_message(f"Expected wait times -- {', '.join(parts)}")

    def say_time_waited(self, t_waited: timedelta, destination: str) -> None:
        """Add a message describing how long the player waited."""
        self.view_model.add_message(
            f"You waited {t_waited.total_seconds():.1f}s for your ride to arrive to {destination}"
        )

    def say_travelling(self, t_travel: timedelta, destination: str) -> None:
        """Add a message describing how long the ride to <destination> takes.

        The trailing dots are animated by the view model while travelling."""
        self.view_model.add_message(
            f"Travelling to {destination} -- {t_travel.total_seconds():.1f}s"
        )

    def say_percentile_wait(self) -> None:
        """Add a message flagging a wait that landed in the 95th percentile."""
        self.view_model.add_message("Unlucky! That was a 95th-percentile wait.")

    def say_sequenced_wait_times(self, wait_times: list[tuple[str, float]]) -> None:
        """Add a message describing the sampled wait time to each neighbour."""
        parts = [f"{name}: {seconds:.1f}s" for name, seconds in wait_times]
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
        self.view_model.add_message("Welcome to Thingamabob Simulator!")
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
