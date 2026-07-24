from typing import Callable

import pygame

from App import ViewModelFacade
from Features.Game import GameView


MENU_WIDTH = 760
MENU_HEIGHT = 520
BG_COLOR = (24, 24, 28)
TITLE_COLOR = (240, 210, 110)
TITLE_SHADOW_COLOR = (0, 0, 0)
PROMPT_COLOR = (205, 205, 215)
TRACK_COLOR = (80, 80, 92)
PIXEL_SIZE = 24

# Pixel-art steam train; each glyph is one pixel block, '.' is transparent.
TRAIN_ART = [
    "....SS..........",
    "...SSSS.........",
    "...SS...........",
    "..CC............",
    "..CC...DDDDDDD..",
    ".BBBBBBBBBBBBB..",
    ".BWWBBBBBBBBBB..",
    ".BWWBBBBBBBBBB..",
    ".BBBBBBBBBBBBB..",
    ".FFFFFFFFFFFFF..",
    "..OO...OO...OO..",
]
TRAIN_COLORS = {
    "S": (225, 225, 230),
    "C": (60, 60, 70),
    "D": (150, 45, 45),
    "B": (205, 70, 60),
    "W": (150, 215, 235),
    "F": (35, 35, 42),
    "O": (70, 70, 82),
}


class ViewFacade:
    """Manage the main menu model and transition between feature
    view models."""

    view_model_facade: ViewModelFacade
    _game_view_factory: Callable[[], GameView]
    _busy: bool
    _running: bool
    _key_observers: dict

    def __init__(
        self,
        view_model_facade: ViewModelFacade,
        game_view_factory: Callable[[], GameView],
    ) -> None:
        self.view_model_facade = view_model_facade
        self._game_view_factory = game_view_factory
        self._busy = False
        self._running = True
        self._key_observers = {
            pygame.K_q: self.on_quit,
            pygame.K_g: self.on_game,
            pygame.K_s: self.on_simulation,
        }

        pygame.init()
        self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        pygame.display.set_caption("Waiting-Sim")
        self.keydown_loop()
        pygame.quit()

    def keydown_loop(self) -> None:
        """Listen for keypresses, notify the bound observer, and redraw."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    observer = self._key_observers.get(event.key)
                    if observer is not None:
                        observer()

            self._draw()
            pygame.display.flip()

    def _resize_if_needed(self, width: int, height: int) -> None:
        """Resize the screen to (<width>, <height>) only if it isn't already
        that size, avoiding a display recreation every frame."""
        if self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))

    def _draw(self) -> None:
        """Draw the active simulation view model, or the default menu."""
        simulation_view_model = self.view_model_facade.simulation_view_model

        if simulation_view_model._running:
            self._resize_if_needed(
                simulation_view_model.width, simulation_view_model.height
            )
            simulation_view_model.draw(self._screen)
        else:
            self._resize_if_needed(MENU_WIDTH, MENU_HEIGHT)
            self._draw_menu()

    def _draw_train(self, top_left_x: int, top_left_y: int, pixel: int) -> None:
        """Draw the pixel-art train with its top-left block at the given point."""
        for row_index, row in enumerate(TRAIN_ART):
            for col_index, glyph in enumerate(row):
                color = TRAIN_COLORS.get(glyph)
                if color is None:
                    continue
                block = pygame.Rect(
                    top_left_x + col_index * pixel,
                    top_left_y + row_index * pixel,
                    pixel,
                    pixel,
                )
                pygame.draw.rect(self._screen, color, block)

    def _draw_menu(self) -> None:
        """Draw the titled Game/Simulation/Quit menu with the train logo."""
        self._screen.fill(BG_COLOR)
        width, height = self._screen.get_size()

        title_font = pygame.font.SysFont("consolas", 60, bold=True)
        title = title_font.render("Waiting-Sim", True, TITLE_COLOR)
        shadow = title_font.render("Waiting-Sim", True, TITLE_SHADOW_COLOR)
        self._screen.blit(shadow, shadow.get_rect(center=(width // 2 + 3, 73)))
        self._screen.blit(title, title.get_rect(center=(width // 2, 70)))

        train_width = len(TRAIN_ART[0]) * PIXEL_SIZE
        train_height = len(TRAIN_ART) * PIXEL_SIZE
        train_x = (width - train_width) // 2
        train_y = 140
        self._draw_train(train_x, train_y, PIXEL_SIZE)
        pygame.draw.line(
            self._screen,
            TRACK_COLOR,
            (train_x - 20, train_y + train_height + 2),
            (train_x + train_width + 20, train_y + train_height + 2),
            3,
        )

        prompt_font = pygame.font.SysFont(None, 30)
        prompt = prompt_font.render(
            "Press G for Game     S for Simulation     Q to Quit",
            True,
            PROMPT_COLOR,
        )
        self._screen.blit(prompt, prompt.get_rect(center=(width // 2, height - 55)))

    def on_quit(self) -> None:
        """Action Listener to quit"""
        if self._busy:
            return
        self._busy = True
        try:
            self._running = False
        finally:
            self._busy = False

    def on_game(self) -> None:
        """Action Listener to launch the game feature. Blocks until the
        player quits back out of it, then reclaims the display for the menu."""
        if self._busy:
            return
        self._busy = True
        try:
            self._game_view_factory()
            self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
            pygame.display.set_caption("Waiting-Sim")
        finally:
            self._busy = False

    def on_simulation(self) -> None:
        """Action Listener to start simulation mode"""
        if self._busy:
            return
        self._busy = True
        try:
            self.view_model_facade.start_simulation()
        finally:
            self._busy = False
