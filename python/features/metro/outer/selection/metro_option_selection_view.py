from typing import Callable

import pygame

from app import audio
from features.metro.inner import MetroInputData
from .metro_option_selection_controller import MetroOptionSelectionController
from .metro_option_selection_view_model import MetroOptionSelectionViewModel


class MetroOptionSelectionView:
    """The Metro entry screen: pick a mode (Play/Gamble) and fill in its inputs,
    then Start launches the game with that request. The screen keeps its state
    for the whole Metro session, so returning from a game lands back here with
    the same inputs; Q leaves Metro back to the main menu."""

    _controller: MetroOptionSelectionController
    _view_model: MetroOptionSelectionViewModel
    _play_view_factory: Callable[[MetroInputData], object]
    _running: bool

    def __init__(
        self,
        controller: MetroOptionSelectionController,
        view_model: MetroOptionSelectionViewModel,
        play_view_factory: Callable[[MetroInputData], object],
    ) -> None:
        self._controller = controller
        self._view_model = view_model
        self._play_view_factory = play_view_factory
        self._running = True

        self._clock = pygame.time.Clock()
        self._screen = pygame.display.set_mode((view_model.width, view_model.height))
        pygame.display.set_caption("Thingamabob Simulator")
        self.event_loop()

    def event_loop(self) -> None:
        """Handle input and redraw the selection screen each frame."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
            self._view_model.draw(self._screen)
            pygame.display.flip()
            self._clock.tick(60)

    def _handle_key(self, event: pygame.event.Event) -> None:
        """Type into the focused field, or run screen shortcuts when none is."""
        view_model = self._view_model
        if view_model.focused is None:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                self.on_quit()
            elif event.key == pygame.K_RETURN:
                self._start()
            return
        if event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
            view_model.focused = None
        elif event.key == pygame.K_BACKSPACE:
            key = view_model.focused
            view_model.set_text(key, view_model.text_value(key)[:-1])
            if key in ("bet_low", "bet_high", "bet_stake"):
                self._update_bet_hints()
        elif event.unicode and self._accepts(view_model.focused, event.unicode):
            key = view_model.focused
            view_model.set_text(key, view_model.text_value(key) + event.unicode)
            if key in ("bet_low", "bet_high", "bet_stake"):
                self._update_bet_hints()

    def _accepts(self, key: str, char: str) -> bool:
        """Return whether <char> is a valid keystroke for field <key>."""
        if key == "name":
            return char.isprintable()
        if key == "bet_stake":
            return char.isdigit() or (char == "." and "." not in self._view_model.bet_stake)
        return char.isdigit()

    def _update_bet_hints(self) -> None:
        """Recompute the suggested optimal stake and the potential payout for the
        current gamble interval and stake, clearing them when unavailable."""
        view_model = self._view_model
        if (
            view_model.mode == "gamble"
            and view_model.bet_low.isdigit()
            and view_model.bet_high.isdigit()
        ):
            low, high = int(view_model.bet_low), int(view_model.bet_high)
            if 0 < low <= high:
                view_model.optimal = self._controller.optimal_bet_amount(
                    low, high, view_model.map_id, view_model.balance
                )
                view_model.payout = self._payout(low, high)
                return
        view_model.optimal = None
        view_model.payout = None

    def _payout(self, low: int, high: int) -> float | None:
        """Return the payout on a winning [low, high] bet at the typed stake, or
        None when the stake is not a positive number."""
        try:
            stake = float(self._view_model.bet_stake)
        except ValueError:
            return None
        if stake <= 0:
            return None
        return self._controller.bet_payout(low, high, self._view_model.map_id, stake)

    def _update_optimal_range(self) -> None:
        """Recompute the map's globally optimal betting range (independent of the
        typed interval), clearing it when not gambling or it is unavailable."""
        view_model = self._view_model
        if view_model.mode != "gamble":
            view_model.optimal_range = None
            return
        try:
            view_model.optimal_range = self._controller.optimal_betting_range(
                view_model.map_id
            )
        except Exception:
            view_model.optimal_range = None

    def _handle_click(self, pos: tuple[int, int]) -> None:
        """Route a left click to a mode, map, field, toggle, or the Start button."""
        view_model = self._view_model
        mode = view_model.mode_at(pos)
        if mode is not None:
            if mode != view_model.mode:
                audio.play("click")
                view_model.set_mode(mode)
                self._update_bet_hints()
                self._update_optimal_range()
            return
        map_id = view_model.map_at(pos)
        if map_id is not None:
            audio.play("click")
            view_model.map_id = map_id
            self._update_bet_hints()
            self._update_optimal_range()
            return
        key = view_model.field_at(pos)
        if key is not None:
            if view_model.field_kind(key) == "toggle":
                audio.play("click")
                view_model.flip_toggle(key)
            else:
                view_model.focused = key
            return
        if view_model.start_at(pos):
            self._start()
            return
        view_model.focused = None

    def _start(self) -> None:
        """Launch the game for the current inputs, or show why it can't."""
        view_model = self._view_model
        request, error = self._controller.build_request(
            view_model.mode,
            view_model.name,
            view_model.map_id,
            view_model.rand_arrival,
            view_model.animate,
            view_model.bet_low,
            view_model.bet_high,
            view_model.bet_stake,
            view_model.balance,
        )
        if request is None:
            view_model.error = error
            audio.play("error")
            return
        view_model.error = ""
        view_model.focused = None
        audio.play("click")
        self._launch_play(request)

    def _launch_play(self, request: MetroInputData) -> None:
        """Run the game for <request> to completion, then reclaim this screen."""
        self._play_view_factory(request)
        self._screen = pygame.display.set_mode(
            (self._view_model.width, self._view_model.height)
        )
        pygame.display.set_caption("Thingamabob Simulator")

    def on_quit(self) -> None:
        """Leave the Metro option-selection screen back to the main menu."""
        audio.play("quit")
        self._running = False
