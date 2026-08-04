import time

from Data import WorldDataAccess
from Entities import Bet, BetLog, GameState, Player
from Features.Game import GameInteractor, GamePresenter, GameViewModel
from Features.Gamble import GambleInputBoundary, GambleOutputBoundary


HOUSE_DEFLATOR = 0.95
STARTING_BALANCE = 100.0
GAME_CONTROLS = (("R", "Restart"), ("Q", "Quit"))
GAMBLE_STEP_DELAY = 0.6


class GambleInteractor(GambleInputBoundary):
    """Orchestrates the bet -> automatic game -> payoff loop.

    Every question is asked through the presenter so it is shown in the view
    model, and the View feeds answers back one at a time through submit(); the
    current expected answer is tracked by <_mode>."""

    _log: BetLog
    _game: GameInteractor
    _game_view_model: GameViewModel
    _presenter: GambleOutputBoundary
    _player: Player | None
    _mode: str
    _name: str
    _map_id: int
    _phase: int
    _amount: float
    _staked: float
    _animate: bool
    _run_id: int

    def __init__(self, presenter: GambleOutputBoundary) -> None:
        """Create an interactor asking its questions through <presenter>."""
        self._log = BetLog()
        self._game_view_model = GameViewModel()
        self._game_view_model.set_controls(GAME_CONTROLS)
        self._game_view_model.set_show_best(False)
        self._game = GameInteractor(
            dao=WorldDataAccess(), presenter=GamePresenter(self._game_view_model)
        )
        self._presenter = presenter
        self._player = None
        self._mode = "done"
        self._name = ""
        self._map_id = 0
        self._phase = 0
        self._amount = 0.0
        self._staked = 0.0
        self._animate = True
        self._run_id = 0

    def game_view_model(self) -> GameViewModel:
        """Return the game view model the View draws during the game phase."""
        return self._game_view_model

    def start(self) -> None:
        """Begin a new gamble round, keeping the balance across restarts.

        Bumping the run id cancels any game animation still in flight from a
        previous round."""
        if self._player is None:
            self._player = Player(starting_station=None, name="Player1")
            self._player.balance = STARTING_BALANCE
        self._run_id += 1
        self._game_view_model.set_bet_result(None)
        self._mode = "name"
        self._presenter.ask_name()
        self._presenter.show_balance(self._player.balance)

    def submit(self, answer: str) -> None:
        """Handle <answer> to the question currently being asked."""
        handler = {
            "name": self._on_name,
            "map": self._on_map,
            "speed": self._on_speed,
            "amount": self._on_amount,
            "target": self._on_target,
            "interval": self._on_interval,
            "steps": self._on_steps,
            "another": self._on_another,
        }.get(self._mode)
        if handler is not None:
            handler(answer.strip())

    def _on_name(self, answer: str) -> None:
        """Store the player's name and ask for a map."""
        self._name = answer or "Player1"
        self._player.name = self._name
        self._mode = "map"
        self._presenter.ask_map(self._game.get_map_ids())

    def _on_map(self, answer: str) -> None:
        """Validate the chosen map, then open a betting phase."""
        if not (answer.isdigit() and int(answer) in self._game.get_map_ids()):
            self._presenter.say_invalid("map id")
            self._presenter.ask_map(self._game.get_map_ids())
            return
        self._map_id = int(answer)
        self._mode = "speed"
        self._presenter.ask_speed()

    def _on_speed(self, answer: str) -> None:
        """Choose animated auto-play (default) or an instant result, then open
        a betting phase."""
        choice = answer.lower()
        if choice in ("", "a"):
            self._animate = True
        elif choice == "i":
            self._animate = False
        else:
            self._presenter.say_invalid("choice")
            self._presenter.ask_speed()
            return
        self._phase = self._log.new_betting_phase()
        self._staked = 0.0
        self._ask_amount()

    def _on_amount(self, answer: str) -> None:
        """Take a stake, or finish betting when the answer is blank."""
        if not answer:
            self._settle()
            return
        amount = self._parse_amount(answer, self._player.balance)
        if amount is None:
            self._presenter.say_invalid("amount")
            self._ask_amount()
            return
        self._amount = amount
        self._mode = "target"
        self._presenter.ask_bet_target()

    def _on_target(self, answer: str) -> None:
        """Route to the interval or steps question."""
        if answer.lower() == "i":
            self._mode = "interval"
            self._presenter.ask_bet_interval()
        elif answer.lower() == "s":
            self._mode = "steps"
            self._presenter.ask_bet_steps()
        else:
            self._presenter.say_invalid("choice")
            self._presenter.ask_bet_target()

    def _on_interval(self, answer: str) -> None:
        """Place a wait-time interval bet."""
        interval = self._parse_interval(answer)
        if interval is None:
            self._presenter.say_invalid("interval")
            self._presenter.ask_bet_interval()
            return
        description = f"a wait in {interval[0]:.1f}-{interval[1]:.1f}s"
        self._presenter.show_probability(
            description, self._event_probability(interval, None)
        )
        self._place_bet(interval, None, description)

    def _on_steps(self, answer: str) -> None:
        """Place an exact-steps bet."""
        steps = self._parse_end_steps(answer)
        if steps is None:
            self._presenter.say_invalid("number of steps")
            self._presenter.ask_bet_steps()
            return
        description = f"finishing in exactly {steps} steps"
        self._presenter.show_probability(
            description, self._event_probability(None, steps)
        )
        self._place_bet(None, steps, description)

    def _place_bet(
        self,
        interval: tuple[float, float] | None,
        end_steps: int | None,
        description: str,
    ) -> None:
        """Create and log the pending bet, then ask whether to lay another."""
        bet = self.create_bet(self._player, self._amount, interval, end_steps)
        if bet is None:
            self._presenter.say_invalid("bet")
        else:
            self._log.add_bet(self._phase, bet)
            self._staked += self._amount
            self._presenter.say_bet_placed(self._amount, description)
        self._mode = "another"
        self._presenter.ask_another_bet()

    def _event_probability(
        self, interval: tuple[float, float] | None, end_steps: int | None
    ) -> float:
        """Return the probability the bet's event occurs. Placeholder p = 1/2
        until wired to the map's wait distributions."""
        return 0.5

    def _on_another(self, answer: str) -> None:
        """Lay another bet, or finish the betting phase."""
        if answer.lower() == "y":
            self._ask_amount()
        elif answer.lower() == "n":
            self._settle()
        else:
            self._presenter.say_invalid("choice")
            self._presenter.ask_another_bet()

    def _ask_amount(self) -> None:
        """Ask for the next stake."""
        self._mode = "amount"
        self._presenter.ask_bet_amount(self._player.balance)

    def _settle(self) -> None:
        """Lock the bets and switch to the game phase. The View then calls
        run_game() in the background to play it out."""
        self._mode = "done"
        self._presenter.show_game()

    def run_game(self) -> None:
        """Play the game -- animated turn by turn, or instantly -- then pay out
        and reveal the outcome. Meant to be run in a background thread so an
        animated game does not block the View's frame loop."""
        run_id = self._run_id
        if self._animate:
            game = self._play_animated(run_id)
            if game is None:
                return
        else:
            game = self.execute_game_phase(self._phase)
        if run_id != self._run_id:
            return
        game.phase_id = self._phase
        payout = self.execute_payoff_phase(game)
        self._player.add_to_balance(payout)
        self._reveal_outcome(game, payout)

    def _play_animated(self, run_id: int) -> GameState | None:
        """Play the game turn by turn with animation, or None if a restart
        cancelled it partway through."""
        self._game.setup_gamble_game(self._name, self._map_id)
        finished = False
        while not finished:
            if run_id != self._run_id:
                return None
            finished = self._game.gamble_turn()
            if not finished:
                time.sleep(GAMBLE_STEP_DELAY)
        return self._game.gamble_result()

    def _reveal_outcome(self, game: GameState, payout: float) -> None:
        """Reveal the bet result on the game HUD once the outcome is known.

        Stakes are not yet deducted when bets are placed, so the payout is the
        net gain and the player won when it is positive."""
        self._game_view_model.set_total_wait(game.wait_time)
        won = payout > 0
        outcome = "WON" if won else "LOST"
        self._game_view_model.set_bet_result(
            f"Staked {self._staked:.2f}  |  {game.end_steps} steps, "
            f"waited {game.wait_time:.1f}s  |  Payout {payout:.2f} -- {outcome}"
        )
        self._presenter.show_balance(self._player.balance)
        self._presenter.announce_outcome(won)

    def execute_game_phase(self, n: int) -> GameState:
        """Execute an automatically advancing Game that doesn't prompt for
        anything and doesn't allow the user any option to quit, restart or
        play again that may cheat the betting system, return the results
        of the game."""
        game_state = self._game.execute_new_gamble_game(self._name, self._map_id)
        game_state.phase_id = n
        return game_state

    def execute_payoff_phase(self, game: GameState) -> float:
        """Handle the accounting of who needs to be paid
        and how much given the outcome of the game."""
        n = game.phase_id
        self._log.complete_phase(n)
        payout = 0.0
        for bet in self._log.get_bets(n):
            payout += bet.payout(game)
        return payout

    def create_bet(
        self,
        player: Player,
        amount: float,
        interval: tuple[float, float] | None,
        end_steps: int | None,
    ) -> Bet | None:
        """Build a new bet, or return None if the information was invalid.

        Exactly one target -- a wait-time interval or an end-step count -- must
        be given, and the stake must fit within the player's balance."""
        if (interval is None) == (end_steps is None):
            return None
        if amount <= 0 or amount > player.balance:
            return None
        if interval is not None and interval[0] >= interval[1]:
            return None
        if end_steps is not None and end_steps <= 0:
            return None

        return Bet(
            self._house_payoff_factor(interval, end_steps), amount, interval, end_steps
        )

    def _house_payoff_factor(
        self, interval: tuple[float, float] | None, end_steps: int | None
    ) -> float:
        """Return the profit multiple paid on a winning bet -- the fair odds
        shaved by the house edge -- so a stake returns stake * factor as profit
        on a win."""
        if end_steps is None:
            p = 1 / 2  # P(X inside interval)
        else:
            p = 1 / 2  # P(X = end_steps)
        fair_value = 1 / p  # decimal odds for a binary outcome
        house_value = fair_value * HOUSE_DEFLATOR
        return house_value - 1

    def _parse_amount(self, raw: str, balance: float) -> float | None:
        """Return <raw> as a stake in (0, balance], or None if invalid."""
        try:
            amount = float(raw)
        except ValueError:
            return None
        return amount if 0 < amount <= balance else None

    def _parse_interval(self, raw: str) -> tuple[float, float] | None:
        """Return <raw> as a (low, high) interval with low < high, or None."""
        parts = raw.split()
        if len(parts) != 2:
            return None
        try:
            low, high = float(parts[0]), float(parts[1])
        except ValueError:
            return None
        return (low, high) if low < high else None

    def _parse_end_steps(self, raw: str) -> int | None:
        """Return <raw> as a positive whole number of steps, or None."""
        raw = raw.strip()
        if not raw.isdigit():
            return None
        steps = int(raw)
        return steps if steps > 0 else None
