import os
from typing import Callable

import pygame

from app import audio
from app.volume_slider import VolumeSlider
from features.metro.outer.play import MetroView
from features.metro.outer.simulation import SimulationView


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

BUTTON_WIDTH = 320
BUTTON_HEIGHT = 56
BUTTON_GAP = 18
BUTTON_BG_COLOR = (36, 38, 46)
BUTTON_HOVER_COLOR = (52, 58, 72)
BUTTON_BORDER_COLOR = (90, 100, 120)
BUTTON_LABEL_COLOR = (222, 228, 238)
SELECT_TITLE_COLOR = (240, 210, 110)
BACK_HINT_COLOR = (150, 160, 175)

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
ABOUT_TITLE = "About Thingamabob Simulator"
ABOUT_LINES = [
    "Play, gamble or simulate weird games.",
    "Each touches on different Statistics, Probability or CS concepts.",
    "",
    "Thingamabob is about waiting for transit. Each turn you wait at your",
    "station for the next ride; the first to arrive carries you to",
    "that neighbouring station.",
    "",
    "Flying is about watching the trajectory of a goose flying in the sky.",
    "Its based off real ecological data bout long-headed Geese",
    "",
    "Simulation mode runs many trials to",
    "observe the waiting-time phenomena across a whole network.",
    "",
    "GitHub: github.com/DursiS/Waiting-Sim",
    "",
    "Press A to return to the menu.",
]


class ViewFacade:
    """Manage the main menu model and transition between feature
    view models."""

    _games: list[tuple[str, Callable[[], object]]]
    _simulations: list[tuple[str, Callable[[], object]]]
    _busy: bool
    _running: bool
    _page: str
    _key_observers: dict
    _logo: pygame.Surface | None
    _volume_slider: VolumeSlider

    def __init__(
        self,
        metro_view_factory: Callable[[], MetroView],
        simulation_view_factory: Callable[[], SimulationView],
        flying_view_factory: Callable[[], object],
    ) -> None:
        self._games = [
            ("Metro", metro_view_factory),
            ("Flying", flying_view_factory),
        ]
        self._simulations = [
            ("Metro", simulation_view_factory),
            ("Flying", flying_view_factory),
        ]
        self._busy = False
        self._running = True
        self._page = "menu"
        self._key_observers = {
            pygame.K_q: self.on_quit,
            pygame.K_g: self.on_game,
            pygame.K_s: self.on_simulation,
            pygame.K_a: self.on_about,
        }

        pygame.init()
        audio.init()
        self._set_window_icon()
        self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        pygame.display.set_caption("Thingamabob Simulator")
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
        """Listen for key and mouse input, act on it, and redraw each frame."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event)
                elif event.type in (
                    pygame.MOUSEBUTTONDOWN,
                    pygame.MOUSEBUTTONUP,
                    pygame.MOUSEMOTION,
                ):
                    if (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                        and self._page in ("games", "simulations")
                    ):
                        self._handle_selection_click(event.pos)
                    if self._page == "menu":
                        self._volume_slider.handle_event(
                            event, self._screen.get_width()
                        )

            self._draw()
            pygame.display.flip()

    def _handle_keydown(self, event: pygame.event.Event) -> None:
        """Run a menu shortcut on the menu; otherwise Escape (or About's own
        key) returns to the menu."""
        if self._page == "menu":
            observer = self._key_observers.get(event.key)
            if observer is not None:
                audio.play("click")
                observer()
        elif self._page in ("games", "simulations"):
            if event.key == pygame.K_q:
                audio.play("click")
                self.on_quit()
            elif event.key == pygame.K_ESCAPE:
                audio.play("click")
                self._page = "menu"
        elif event.key == pygame.K_ESCAPE or (
            self._page == "about" and event.key == pygame.K_a
        ):
            audio.play("click")
            self._page = "menu"

    def _resize_if_needed(self, width: int, height: int) -> None:
        """Resize the screen to (<width>, <height>) only if it isn't already
        that size, avoiding a display recreation every frame."""
        if self._screen.get_size() != (width, height):
            self._screen = pygame.display.set_mode((width, height))

    def _draw(self) -> None:
        """Draw whichever page the menu is currently showing."""
        self._resize_if_needed(MENU_WIDTH, MENU_HEIGHT)
        if self._page == "about":
            self._draw_about()
        elif self._page == "games":
            self._draw_selection("Thingamabob Selection", self._games)
        elif self._page == "simulations":
            self._draw_selection("Simulation Selection", self._simulations)
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
        title = title_font.render("Thingamabob Simulator", True, TITLE_COLOR)
        shadow = title_font.render("Thingamabob Simulator", True, TITLE_SHADOW_COLOR)
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
        """Draw the Game/Simulation/About/Quit menu beneath the app logo."""
        self._screen.fill(BG_COLOR)
        width, height = self._screen.get_size()

        self._draw_logo(width, height)
        self._volume_slider.draw(self._screen)

        prompt_font = pygame.font.SysFont(None, 30)
        prompt = prompt_font.render(
            "G Thingamabobs   S Simulation   A About   Q Quit",
            True,
            PROMPT_COLOR,
        )
        self._screen.blit(prompt, prompt.get_rect(center=(width // 2, height - 55)))

    def _button_rects(self, count: int) -> list[pygame.Rect]:
        """Return the vertical stack of <count> button rectangles, centred."""
        width, height = self._screen.get_size()
        total = count * BUTTON_HEIGHT + (count - 1) * BUTTON_GAP
        x = (width - BUTTON_WIDTH) // 2
        top = (height - total) // 2
        return [
            pygame.Rect(
                x, top + i * (BUTTON_HEIGHT + BUTTON_GAP), BUTTON_WIDTH, BUTTON_HEIGHT
            )
            for i in range(count)
        ]

    def _draw_selection(
        self, title: str, options: list[tuple[str, Callable[[], object]]]
    ) -> None:
        """Draw a titled vertical stack of buttons, one per option, highlighting
        whichever the mouse is hovering over."""
        self._screen.fill(BG_COLOR)
        width, height = self._screen.get_size()

        title_font = pygame.font.SysFont("consolas", 40, bold=True)
        heading = title_font.render(title, True, SELECT_TITLE_COLOR)
        self._screen.blit(heading, heading.get_rect(center=(width // 2, 80)))

        label_font = pygame.font.SysFont(None, 30)
        mouse = pygame.mouse.get_pos()
        for rect, (label, _) in zip(self._button_rects(len(options)), options):
            hovered = rect.collidepoint(mouse)
            color = BUTTON_HOVER_COLOR if hovered else BUTTON_BG_COLOR
            pygame.draw.rect(self._screen, color, rect, border_radius=8)
            pygame.draw.rect(
                self._screen, BUTTON_BORDER_COLOR, rect, width=2, border_radius=8
            )
            text = label_font.render(label, True, BUTTON_LABEL_COLOR)
            self._screen.blit(text, text.get_rect(center=rect.center))

        hint_font = pygame.font.SysFont(None, 26)
        hint = hint_font.render("Q  Quit", True, BACK_HINT_COLOR)
        self._screen.blit(hint, hint.get_rect(center=(width // 2, height - 40)))

    def _selection_options(self) -> list[tuple[str, Callable[[], object]]]:
        """Return the option list for the current selection page."""
        return self._games if self._page == "games" else self._simulations

    def _handle_selection_click(self, pos: tuple[int, int]) -> None:
        """Launch the feature whose button was clicked, if any."""
        options = self._selection_options()
        for rect, (_, factory) in zip(self._button_rects(len(options)), options):
            if rect.collidepoint(pos):
                self._launch(factory)
                return

    def _launch(self, factory: Callable[[], object]) -> None:
        """Run a feature view to completion, then reclaim the menu display."""
        if self._busy:
            return
        self._busy = True
        try:
            audio.play("click")
            factory()
            self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
            pygame.display.set_caption("Thingamabob Simulator")
        finally:
            self._busy = False

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
        """Action Listener to quit the app."""
        self._running = False

    def on_about(self) -> None:
        """Action Listener to open the About page."""
        self._page = "about"

    def on_game(self) -> None:
        """Action Listener to open the game selection page, a button per game."""
        self._page = "games"

    def on_simulation(self) -> None:
        """Action Listener to open the simulation selection page, a button per
        simulation."""
        self._page = "simulations"
