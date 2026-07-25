import pygame

from Entities import Station


CELL_SIZE = 130
PADDING = 40
PROMPT_HEIGHT = 80
TEXT_PANEL_WIDTH = 280
BG_COLOR = (24, 24, 28)
CELL_COLOR = (70, 130, 180)
CURRENT_CELL_COLOR = (250, 180, 60)
BORDER_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)
RULE_TEXT_COLOR = (215, 230, 240)
ID_TEXT_COLOR = (255, 210, 120)
PROMPT_COLOR = (200, 200, 60)
PANEL_DIVIDER_COLOR = (70, 70, 80)
MESSAGE_COLOR = (220, 220, 220)
TOTAL_WAIT_COLOR = (255, 235, 150)


class GameViewModel:
    """A pygame rendering of the world grid, prompts, and a live side text
    block of presenter messages, for an active game turn."""

    stations: list[Station]
    curr_station: Station | None
    messages: list[str]
    total_wait: float
    grid_width: int
    width: int
    height: int
    _running: bool

    def __init__(
        self,
        stations: list[Station] = None,
        curr_station: Station | None = None,
        messages: list[str] = None,
    ) -> None:
        """Create a ViewModel for <stations>, highlighting <curr_station>."""
        self.stations = stations or []
        self.curr_station = curr_station
        self.messages = messages or []
        self.total_wait = 0.0
        self._running = False
        self._recompute_dimensions()

    def _recompute_dimensions(self) -> None:
        """Size the window to fit the station grid plus the side text panel."""
        x_m = max((s.coordinates[0] for s in self.stations), default=0)
        y_m = max((s.coordinates[1] for s in self.stations), default=0)
        self.grid_width = (x_m + 1) * CELL_SIZE + PADDING * 2
        self.height = (y_m + 1) * CELL_SIZE + PADDING * 2 + PROMPT_HEIGHT
        self.width = self.grid_width + TEXT_PANEL_WIDTH

    def set_stations(self, stations: list[Station]) -> None:
        """Replace the shown stations and resize to fit them."""
        self.stations = stations
        self._recompute_dimensions()

    def set_current_station(self, station: Station | None) -> None:
        """Set which station is highlighted as the player's location."""
        self.curr_station = station

    def clear_messages(self) -> None:
        """Empty the side text block."""
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add <message> to the side text block; the draw loop shows it next frame."""
        self.messages.append(message)

    def set_total_wait(self, total_wait: float) -> None:
        """Set the player's cumulative wait time shown in the corner."""
        self.total_wait = total_wait

    def _wrap_text(
        self, text: str, font: pygame.font.Font, max_width: int
    ) -> list[str]:
        """Split <text> into lines that each fit within <max_width>."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def _draw_centered_lines(
        self,
        screen: pygame.Surface,
        lines: list[str],
        font: pygame.font.Font,
        color: tuple[int, int, int],
        center_x: int,
        top_y: int,
    ) -> int:
        """Draw <lines> centered on <center_x> starting at <top_y>, return the bottom y."""
        y = top_y
        for line in lines:
            rendered = font.render(line, True, color)
            screen.blit(rendered, rendered.get_rect(midtop=(center_x, y)))
            y += rendered.get_height()
        return y

    def draw_grid(
        self,
        screen: pygame.Surface,
        name_font: pygame.font.Font,
        rule_font: pygame.font.Font,
        id_font: pygame.font.Font,
    ) -> None:
        """Draw every station at its grid coordinates."""
        for station in self.stations:
            x, y = station.coordinates
            rect = pygame.Rect(
                PADDING + x * CELL_SIZE,
                PADDING + y * CELL_SIZE,
                CELL_SIZE - 10,
                CELL_SIZE - 10,
            )
            is_current = (
                self.curr_station is not None and station.id == self.curr_station.id
            )
            pygame.draw.rect(
                screen, CURRENT_CELL_COLOR if is_current else CELL_COLOR, rect
            )
            if is_current:
                pygame.draw.rect(screen, BORDER_COLOR, rect, width=4)

            max_text_width = rect.width - 10
            name_lines = self._wrap_text(station.name, name_font, max_text_width)
            rule_lines = self._wrap_text(station.rule_name, rule_font, max_text_width)
            id_lines = [f"id: {station.id}"]
            total_height = (
                len(name_lines) * name_font.get_height()
                + len(rule_lines) * rule_font.get_height()
                + len(id_lines) * id_font.get_height()
            )
            top_y = rect.centery - total_height // 2

            bottom = self._draw_centered_lines(
                screen, name_lines, name_font, TEXT_COLOR, rect.centerx, top_y
            )
            bottom = self._draw_centered_lines(
                screen, rule_lines, rule_font, RULE_TEXT_COLOR, rect.centerx, bottom
            )
            self._draw_centered_lines(
                screen, id_lines, id_font, ID_TEXT_COLOR, rect.centerx, bottom
            )

    def draw_prompts(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the text prompts."""
        prompt = font.render(
            "Press P to Play  |  Press C to Continue  |  Press Q to Quit",
            True,
            PROMPT_COLOR,
        )
        screen.blit(prompt, (PADDING, self.height - PROMPT_HEIGHT // 2))

    def draw_messages(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the presenter's messages in a side text block."""
        panel_x = self.grid_width
        pygame.draw.line(
            screen, PANEL_DIVIDER_COLOR, (panel_x, 0), (panel_x, self.height), width=2
        )

        text_x = panel_x + PADDING // 2
        max_width = TEXT_PANEL_WIDTH - PADDING
        y = PADDING
        for message in self.messages:
            for line in self._wrap_text(message, font, max_width):
                rendered = font.render(line, True, MESSAGE_COLOR)
                screen.blit(rendered, (text_x, y))
                y += rendered.get_height() + 2
            y += 10

    def draw_total_wait(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the cumulative wait time in the top-left corner."""
        text = font.render(f"Total wait: {self.total_wait:.1f}s", True, TOTAL_WAIT_COLOR)
        screen.blit(text, (12, 10))

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the grid, prompts, and messages onto <screen>."""
        name_font = pygame.font.SysFont(None, 22)
        rule_font = pygame.font.SysFont(None, 16)
        id_font = pygame.font.SysFont(None, 16)
        prompt_font = pygame.font.SysFont(None, 24)
        message_font = pygame.font.SysFont(None, 18)
        total_wait_font = pygame.font.SysFont(None, 24)

        screen.fill(BG_COLOR)
        self.draw_grid(screen, name_font, rule_font, id_font)
        self.draw_prompts(screen, prompt_font)
        self.draw_messages(screen, message_font)
        self.draw_total_wait(screen, total_wait_font)


class DefaultViewModel(GameViewModel):
    """Default homescreen to select functionality from."""

    def __init__(self, stations: list[Station]) -> None:
        """Create a DefaultViewModel presenting <stations> and the available controls."""
        super().__init__(
            stations=stations,
            curr_station=None,
            messages=[
                "P - Play: start a new game",
                "C - Continue: resume a saved game",
                "S - Simulate: run simulations",
                "Q - Quit: exit the game",
            ],
        )

    def draw_prompts(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the homescreen's text prompts."""
        prompt = font.render(
            "Press P to Play  |  Press C to Continue  |  "
            "Press S to Simulate  |  Press Q to Quit",
            True,
            PROMPT_COLOR,
        )
        screen.blit(prompt, (PADDING, self.height - PROMPT_HEIGHT // 2))
