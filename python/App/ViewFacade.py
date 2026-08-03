import os
from typing import Callable

import pygame

import Audio
from App.VolumeSlider import VolumeSlider
from Features.Game import GameView
from Features.Simulation import SimulationView


ICON_PATH = os.path.join(os.path.dirname(__file__), "test.jpg")
ICON_SIZE = 32
LOGO_MAX_WIDTH = 560
LOGO_MAX_HEIGHT = 300
MENU_WIDTH = 760
MENU_HEIGHT = 520
BG_COLOR = (24, 24, 28)
TITLE_COLOR = (240, 210, 110)
TITLE_SHADOW_COLOR = (0, 0, 0)
PROMPT_COLOR = (205, 205, 215)
TRACK_COLOR = (80, 80, 92)
PIXEL_SIZE = 15

# Pixel-art steam train; each glyph is one pixel block, '.' is transparent.
TRAIN_ART = [
    "......WWW...................",
    ".....WWWWW..................",
    ".....WWwww..................",
    ".....DdD.....DDD............",
    ".....DdD....DdddD...........",
    "...DDDDDDDDDDDDDDDDDDDDDDD..",
    "..DHHHHHHHHHHHHHHHHHHHHHHHD.",
    "..DRRRRRRRRRRRRRRRGGGRRRRRD.",
    "..DRRRRRRRRRRRRRRRGGGRRRRRD.",
    "..DRRRRRRRRRRRRRRRGGGRRRRRD.",
    "..DrrrrrrrrrrrrrrrrrrrrrrrD.",
    "..YYYYYYYYYYYYYYYYYYYYYYYYY.",
    "...DDDDDDDDDDDDDDDDDDDDDDD..",
    "....OOO......OOO......OOO...",
    "...OoSoO....OoSoO....OoSoO..",
    "....OOO......OOO......OOO...",
]
TRAIN_COLORS = {
    "W": (238, 238, 242),
    "w": (192, 194, 202),
    "D": (52, 52, 64),
    "d": (92, 92, 108),
    "H": (240, 122, 106),
    "R": (206, 74, 60),
    "r": (150, 46, 42),
    "Y": (242, 200, 92),
    "G": (150, 215, 235),
    "O": (64, 64, 80),
    "o": (122, 122, 140),
    "S": (170, 172, 184),
}

ABOUT_TITLE_COLOR = (150, 215, 235)
ABOUT_TEXT_COLOR = (220, 220, 225)
ABOUT_TITLE = "About Waiting-Sim"
ABOUT_LINES = [
    "A game about waiting for transit. Each turn you wait at your",
    "station for the next ride; the first to arrive carries you to",
    "that neighbouring station. Expected and sampled wait times let",
    "you read the network's rhythm -- reach the end with as little",
    "total waiting as possible.",
    "",
    "Simulation mode runs many trials to",
    "observe the waiting-time phenomena across a whole network.",
    "",
    "GitHub: github.com/DursiS/Waiting-Sim",
    "",
    "Press O to return to the menu.",
]


class ViewFacade:
    """Manage the main menu model and transition between feature
    view models."""

    _game_view_factory: Callable[[], GameView]
    _simulation_view_factory: Callable[[], SimulationView]
    _busy: bool
    _running: bool
    _showing_about: bool
    _key_observers: dict
    _logo: pygame.Surface | None
    _volume_slider: VolumeSlider

    def __init__(
        self,
        game_view_factory: Callable[[], GameView],
        simulation_view_factory: Callable[[], SimulationView],
    ) -> None:
        self._game_view_factory = game_view_factory
        self._simulation_view_factory = simulation_view_factory
        self._busy = False
        self._running = True
        self._showing_about = False
        self._key_observers = {
            pygame.K_q: self.on_quit,
            pygame.K_g: self.on_game,
            pygame.K_s: self.on_simulation,
            pygame.K_o: self.on_about,
        }

        pygame.init()
        Audio.init()
        self._set_window_icon()
        self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        pygame.display.set_caption("Waiting-Sim")
        self._logo = self._load_logo()
        self._volume_slider = VolumeSlider()
        self.keydown_loop()
        self._drain_audio()
        pygame.quit()

    def _drain_audio(self) -> None:
        """Let a final effect (such as the quit click) finish before the mixer
        is torn down, waiting briefly and stopping early once it is silent."""
        if not pygame.mixer.get_init():
            return
        for _ in range(20):
            if not pygame.mixer.get_busy():
                return
            pygame.time.wait(10)

    def _load_logo(self) -> pygame.Surface | None:
        """Return the app logo scaled to fit the menu, or None when missing."""
        if not os.path.exists(ICON_PATH):
            return None
        image = pygame.image.load(ICON_PATH).convert()
        width, height = image.get_size()
        scale = min(LOGO_MAX_WIDTH / width, LOGO_MAX_HEIGHT / height)
        return pygame.transform.smoothscale(
            image, (round(width * scale), round(height * scale))
        )

    def _load_icon(self) -> pygame.Surface | None:
        """Return the app logo as a square icon keeping its aspect ratio,
        or None when the image is missing."""
        if not os.path.exists(ICON_PATH):
            return None
        image = pygame.image.load(ICON_PATH)
        width, height = image.get_size()
        scale = ICON_SIZE / max(width, height)
        scaled = pygame.transform.smoothscale(
            image, (max(round(width * scale), 1), max(round(height * scale), 1))
        )
        icon = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)
        icon.blit(scaled, scaled.get_rect(center=(ICON_SIZE // 2, ICON_SIZE // 2)))
        return icon

    def _set_window_icon(self) -> None:
        """Set the app logo as the icon for every window the app opens."""
        icon = self._load_icon()
        if icon is not None:
            pygame.display.set_icon(icon)

    def keydown_loop(self) -> None:
        """Listen for keypresses, notify the bound observer, and redraw."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    observer = self._key_observers.get(event.key)
                    if observer is not None:
                        Audio.play("click")
                        observer()
                elif event.type in (
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEBUTTONUP,
                    pygame.MOUSEMOTION,
                ):
                    if not self._showing_about:
                        self._volume_slider.handle_event(
                            event, self._screen.get_width()
                        )

            self._draw()
            pygame.display.flip()

    def _resize_if_needed(self, width: int, height: int) -> None:
        """Resize the screen to (<width>, <height>) only if it isn't already
        that size, avoiding a display recreation every frame."""
        if self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))

    def _draw(self) -> None:
        """Draw the About screen or the default menu."""
        self._resize_if_needed(MENU_WIDTH, MENU_HEIGHT)
        if self._showing_about:
            self._draw_about()
        else:
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

    def _draw_logo(self, width: int, height: int) -> None:
        """Draw the logo image centred above the prompt, falling back to the
        pixel-art train and rendered title when the image is missing."""
        if self._logo is not None:
            self._screen.blit(
                self._logo, self._logo.get_rect(center=(width // 2, (height - 90) // 2))
            )
            return

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

    def _draw_menu(self) -> None:
        """Draw the Game/Simulation/Quit menu beneath the app logo."""
        self._screen.fill(BG_COLOR)
        width, height = self._screen.get_size()

        self._draw_logo(width, height)
        self._volume_slider.draw(self._screen)

        prompt_font = pygame.font.SysFont(None, 30)
        prompt = prompt_font.render(
            "G Game     S Simulation     O About     Q Quit",
            True,
            PROMPT_COLOR,
        )
        self._screen.blit(prompt, prompt.get_rect(center=(width // 2, height - 55)))

    def _draw_about(self) -> None:
        """Draw the About screen: what the game and simulation are, then credits."""
        self._screen.fill(BG_COLOR)
        width, _ = self._screen.get_size()

        title_font = pygame.font.SysFont("consolas", 40, bold=True)
        title = title_font.render(ABOUT_TITLE, True, ABOUT_TITLE_COLOR)
        self._screen.blit(title, title.get_rect(center=(width // 2, 48)))

        text_font = pygame.font.SysFont(None, 24)
        y = 95
        for line in ABOUT_LINES:
            rendered = text_font.render(line, True, ABOUT_TEXT_COLOR)
            self._screen.blit(rendered, rendered.get_rect(center=(width // 2, y)))
            y += 28

    def on_quit(self) -> None:
        """Action Listener to quit"""
        if self._busy:
            return
        self._busy = True
        try:
            self._running = False
        finally:
            self._busy = False

    def on_about(self) -> None:
        """Action Listener to toggle the About screen"""
        if self._busy:
            return
        self._busy = True
        try:
            self._showing_about = not self._showing_about
        finally:
            self._busy = False

    def on_game(self) -> None:
        """Action Listener to launch the game feature. Blocks until the
        player quits back out of it, then reclaims the display for the menu."""
        if self._busy:
            return
        self._busy = True
        try:
            self._showing_about = False
            self._game_view_factory()
            self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
            pygame.display.set_caption("Waiting-Sim")
        finally:
            self._busy = False

    def on_simulation(self) -> None:
        """Action Listener to launch simulation mode. Blocks until the user
        quits back out of it, then reclaims the display for the menu."""
        if self._busy:
            return
        self._busy = True
        try:
            self._showing_about = False
            self._simulation_view_factory()
            self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
            pygame.display.set_caption("Waiting-Sim")
        finally:
            self._busy = False
