import threading
from typing import Callable

import pygame

from Data import Audio
from Features.Game import (
    GameController,
    GamePresenter,
    GameViewModel,
    GameInteractor,
)


INPUT_BG_COLOR = (0, 0, 0)
INPUT_TEXT_COLOR = (255, 255, 255)
MAX_BETS = 3


class GameView:
    """The game screen. The player answers a short setup flow -- name, whether
    to gamble, which map, random arrival and whether to animate -- then the
    whole game plays out in a background thread so the 60fps draw loop keeps
    streaming the presenter's turn-by-turn updates in real time. A plain game
    types its answers over the rail map; choosing to gamble switches the screen
    to the betting view, where bets are placed before the game runs. Once a
    finished game is on screen R restarts it and Q quits back to the menu."""

    _controller: GameController
    _presenter: GamePresenter
    _interactor: GameInteractor
    _view_model: GameViewModel
    _running: bool
    _busy: bool
    _input_mode: str | None
    _input_buffer: str
    _buffer: str
    _pending_name: str
    _pending_gamble: bool
    _pending_map_id: int
    _pending_rand_arrival: bool
    _pending_animate: bool
    _bet_mode: str | None
    _raw_bets: list
    _bet_balance: float
    _pending_steps: int

    def __init__(
        self,
        controller: GameController,
        presenter: GamePresenter,
        interactor: GameInteractor,
        view_model: GameViewModel,
    ) -> None:
        self._controller = controller
        self._presenter = presenter
        self._interactor = interactor
        self._view_model = view_model
        self._running = True
        self._busy = False
        self._input_mode = "name"
        self._input_buffer = ""
        self._buffer = ""
        self._pending_name = ""
        self._pending_gamble = False
        self._pending_map_id = 0
        self._pending_rand_arrival = False
        self._pending_animate = True
        self._bet_mode = None
        self._raw_bets = []
        self._bet_balance = 0.0
        self._pending_steps = 0

        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Waiting-Sim")
        self.keydown_loop()

    def keydown_loop(self) -> None:
        """Listen for keypresses, drive the setup flow and controls, and redraw
        whichever phase's view the game is in each frame."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)

            self._draw()
            pygame.display.flip()
            self._clock.tick(60)

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Route a keypress: setup typing while a field is open, betting input
        during the betting phase, and restart/quit once a game has finished.

        While a game is playing out no control key does anything, so a gamble
        cannot be dodged by restarting or quitting mid-game."""
        if self._busy:
            return
        if self._input_mode is not None:
            self._handle_text_input(event)
        elif self._view_model.phase == "betting":
            self._handle_betting_input(event)
        elif self._view_model.game_over:
            if event.key == pygame.K_r:
                self.on_restart()
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.on_quit()

    def _draw(self) -> None:
        """Draw the betting screen or the rail map for the current phase, sizing
        the window to fit whichever is shown."""
        if self._view_model.phase == "betting":
            self._fit(self._view_model.betting_width, self._view_model.betting_height)
            self._view_model.draw_betting(self._screen, self._buffer)
        else:
            self._fit(self._view_model.width, self._view_model.height)
            self._view_model.draw(self._screen)
            if self._input_mode is not None:
                self._draw_input_prompt()

    def _fit(self, width: int, height: int) -> None:
        """Resize the window to (<width>, <height>) only if it isn't already."""
        if self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))

    def _run_in_background(self, action: Callable[[], None]) -> None:
        """Run <action> in a daemon thread so the draw loop keeps streaming the
        presenter's updates in real time instead of freezing on the game."""
        if self._busy:
            return
        self._busy = True

        def worker() -> None:
            try:
                action()
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _draw_input_prompt(self) -> None:
        """Draw the setup field currently being typed into over the rail map."""
        if self._input_mode == "map":
            ids = "/".join(str(m) for m in self._controller.get_map_ids())
            label = f"Map id ({ids})"
        else:
            label = {
                "name": "Name",
                "gamble": "Gamble? (y/n)",
                "arrival": "Random arrival? (y/n)",
                "animate": "Animate turns? (y/n)",
            }.get(self._input_mode, "")
        font = pygame.font.SysFont(None, 28)
        text = font.render(f"{label}: {self._input_buffer}_", True, INPUT_TEXT_COLOR)
        box = text.get_rect().inflate(20, 10)
        box.topright = (self._screen.get_width() - 20, 20)
        pygame.draw.rect(self._screen, INPUT_BG_COLOR, box)
        self._screen.blit(text, text.get_rect(center=box.center))

    def _handle_text_input(self, event: pygame.event.Event) -> None:
        """Handle a keypress while a setup field is being typed into."""
        if event.key == pygame.K_ESCAPE:
            self.on_quit()
        elif event.key == pygame.K_RETURN:
            self._submit_input()
        elif event.key == pygame.K_BACKSPACE:
            self._input_buffer = self._input_buffer[:-1]
        elif event.unicode.isprintable():
            self._input_buffer += event.unicode

    def _submit_input(self) -> None:
        """Advance the setup flow when the open field is submitted, launching
        the game or the betting phase once every answer is in."""
        if self._input_mode == "name":
            self._pending_name = self._input_buffer or "Player1"
            self._open_input("gamble")
        elif self._input_mode == "gamble":
            if not self._is_yes_no():
                return
            self._pending_gamble = self._input_buffer.lower() == "y"
            self._open_input("map")
        elif self._input_mode == "map":
            if not self._input_buffer.isdigit() or (
                int(self._input_buffer) not in self._controller.get_map_ids()
            ):
                Audio.play("error")
                return
            self._pending_map_id = int(self._input_buffer)
            self._open_input("arrival")
        elif self._input_mode == "arrival":
            if not self._is_yes_no():
                return
            self._pending_rand_arrival = self._input_buffer.lower() == "y"
            self._open_input("animate")
        elif self._input_mode == "animate":
            if not self._is_yes_no():
                return
            self._pending_animate = self._input_buffer.lower() == "y"
            self._input_mode = None
            self._input_buffer = ""
            self._finish_setup()

    def _open_input(self, mode: str) -> None:
        """Open setup field <mode> for typing, clearing the buffer."""
        self._input_mode = mode
        self._input_buffer = ""

    def _is_yes_no(self) -> bool:
        """Return whether the current buffer is 'y' or 'n', chiming on error."""
        if self._input_buffer.lower() in ("y", "n"):
            return True
        Audio.play("error")
        return False

    def _finish_setup(self) -> None:
        """Start the chosen game: run a plain game straight away, or enter the
        betting phase first when the player chose to gamble."""
        if self._pending_gamble:
            self._view_model.set_phase("betting")
            self._view_model.clear_messages()
            self._begin_betting()
        else:
            self._start_game(gamble=False, raw_bets=None)

    def _start_game(self, gamble: bool, raw_bets: list | None) -> None:
        """Play a fresh game with the pending setup answers in the background,
        settling <raw_bets> against the outcome when gambling."""
        name = self._pending_name
        map_id = self._pending_map_id
        rand_arrival = self._pending_rand_arrival
        animate = self._pending_animate
        self._run_in_background(
            lambda: self._controller.handle_play(
                None, name, map_id, rand_arrival, gamble, raw_bets, animate
            )
        )

    def _begin_betting(self) -> None:
        """Start collecting bets on the betting screen. Bets are gathered as raw
        {end_steps, amount} data, prompting for one after another until the
        player finishes or MAX_BETS is placed, then handed to the game as
        raw_bets."""
        self._raw_bets = []
        self._bet_balance = self._controller.get_balance()
        self._prompt_next_bet()

    def _prompt_next_bet(self) -> None:
        """Show the remaining balance and open the next bet's steps field."""
        self._view_model.set_balance(self._bet_balance - self._staked())
        self._bet_mode = "steps"
        self._buffer = ""
        self._view_model.set_prompt(
            f"Bet {len(self._raw_bets) + 1}/{MAX_BETS} -- reach the end in how "
            "many steps? (blank to finish)"
        )

    def _handle_betting_input(self, event: pygame.event.Event) -> None:
        """Collect the current bet field, looping until the player finishes or
        has placed MAX_BETS; Escape leaves back to the menu."""
        if event.key == pygame.K_ESCAPE:
            self.on_quit()
        elif event.key == pygame.K_RETURN:
            self._submit_bet()
        elif event.key == pygame.K_BACKSPACE:
            self._buffer = self._buffer[:-1]
        elif event.unicode.isprintable():
            self._buffer += event.unicode

    def _submit_bet(self) -> None:
        """Advance the bet-collection flow when the open field is submitted."""
        answer = self._buffer.strip()
        if self._bet_mode == "steps":
            self._submit_bet_steps(answer)
        elif self._bet_mode == "amount":
            self._submit_bet_amount(answer)

    def _submit_bet_steps(self, answer: str) -> None:
        """Take the target step count, or finish betting on a blank answer."""
        if answer == "":
            self._finish_betting()
            return
        if not answer.isdigit() or int(answer) <= 0:
            Audio.play("error")
            return
        self._pending_steps = int(answer)
        self._bet_mode = "amount"
        self._buffer = ""
        self._view_model.set_prompt(
            f"Stake on reaching the end in exactly {self._pending_steps} steps? "
            "(blank to cancel)"
        )

    def _submit_bet_amount(self, answer: str) -> None:
        """Take the stake and place the bet, or cancel it on a blank answer."""
        if answer == "":
            self._prompt_next_bet()
            return
        amount = self._parse_amount(answer)
        if amount is None:
            Audio.play("error")
            return
        self._raw_bets.append({"end_steps": self._pending_steps, "amount": amount})
        Audio.play("ding")
        self._view_model.add_message(
            f"Placed {amount:.2f} on reaching the end in {self._pending_steps} steps."
        )
        if len(self._raw_bets) >= MAX_BETS:
            self._finish_betting()
        else:
            self._prompt_next_bet()

    def _parse_amount(self, answer: str) -> float | None:
        """Return a positive stake within the remaining balance, or None."""
        try:
            amount = float(answer)
        except ValueError:
            return None
        if amount <= 0 or amount > self._bet_balance - self._staked():
            return None
        return amount

    def _staked(self) -> float:
        """Return the total already staked across the placed bets."""
        return sum(bet["amount"] for bet in self._raw_bets)

    def _finish_betting(self) -> None:
        """Close the betting screen and play out the gamble game."""
        self._view_model.set_prompt("")
        self._bet_mode = None
        self._start_game(gamble=True, raw_bets=self._raw_bets)

    def on_quit(self) -> None:
        """Leave the game screen back to the menu."""
        Audio.play("quit")
        self._running = False

    def on_restart(self) -> None:
        """Replay the finished game with the same settings."""
        self._run_in_background(self._controller.handle_restart)
