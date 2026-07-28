import pygame


CELL_SIZE = 130
PADDING = 40
PROMPT_HEIGHT = 80
TEXT_PANEL_WIDTH = 280
MIN_GRID_WIDTH = 720
PANEL_LINE_HEIGHT = 20
BG_COLOR = (24, 24, 28)
CELL_COLOR = (70, 130, 180)
BORDER_COLOR = (255, 255, 255)
LABEL_COLOR = (215, 230, 240)
VALUE_COLOR = (255, 255, 255)
PROMPT_COLOR = (200, 200, 60)
PANEL_DIVIDER_COLOR = (70, 70, 80)
MESSAGE_COLOR = (220, 220, 220)

# The metrics the interactor reports, keyed by their (row, column) in the grid.
DEFAULT_CELLS = {
    (0, 0): ("Avg wait time", "-"),
    (0, 1): ("Most visited station", "-"),
    (0, 2): ("Last-station spread", "-"),
    (1, 0): ("Avg error from mean", "-"),
    (1, 1): ("Avg random wait", "-"),
}


class SimulationViewModel:
    """A spreadsheet-style grid of simulation metrics with a live side text
    block of presenter messages, styled to match the game view."""

    cells: dict[tuple[int, int], tuple[str, str]]
    messages: list[str]
    grid_width: int
    width: int
    height: int
    _running: bool

    def __init__(
        self,
        cells: dict[tuple[int, int], tuple[str, str]] = None,
        messages: list[str] = None,
    ) -> None:
        """Create a ViewModel showing <cells> as a grid of labelled metrics."""
        self.cells = cells or dict(DEFAULT_CELLS)
        self.messages = messages or []
        self._running = False
        self._recompute_dimensions()

    def _recompute_dimensions(self) -> None:
        """Size the window to fit the metric grid and the side text panel,
        matching the game view's proportions."""
        max_col = max((col for _, col in self.cells), default=0)
        max_row = max((row for row, _ in self.cells), default=0)
        self.grid_width = max((max_col + 1) * CELL_SIZE + PADDING * 2, MIN_GRID_WIDTH)
        grid_height = (max_row + 1) * CELL_SIZE + PADDING * 2 + PROMPT_HEIGHT
        panel_height = PADDING * 2 + (len(self.messages) + 8) * PANEL_LINE_HEIGHT
        self.height = max(grid_height, panel_height)
        self.width = self.grid_width + TEXT_PANEL_WIDTH

    def set_cell(self, row: int, col: int, label: str, value: str) -> None:
        """Set the <label> and <value> of the metric cell at (<row>, <col>)."""
        self.cells[(row, col)] = (label, value)
        self._recompute_dimensions()

    def set_value(self, row: int, col: int, value: str) -> None:
        """Update just the value of the metric cell at (<row>, <col>)."""
        label = self.cells.get((row, col), ("", ""))[0]
        self.cells[(row, col)] = (label, value)

    def clear_messages(self) -> None:
        """Empty the side text block."""
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add <message> to the side text block; shown next frame."""
        self.messages.append(message)

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

    def draw_grid(
        self,
        screen: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        """Draw each metric as a labelled spreadsheet cell."""
        for (row, col), (label, value) in self.cells.items():
            rect = pygame.Rect(
                PADDING + col * CELL_SIZE,
                PADDING + row * CELL_SIZE,
                CELL_SIZE - 10,
                CELL_SIZE - 10,
            )
            pygame.draw.rect(screen, CELL_COLOR, rect)
            pygame.draw.rect(screen, BORDER_COLOR, rect, width=2)

            max_text_width = rect.width - 12
            y = rect.top + 10
            for line in self._wrap_text(label, label_font, max_text_width):
                rendered = label_font.render(line, True, LABEL_COLOR)
                screen.blit(rendered, rendered.get_rect(midtop=(rect.centerx, y)))
                y += rendered.get_height()

            value_lines = self._wrap_text(value, value_font, max_text_width)
            value_height = value_font.get_height() * len(value_lines)
            value_y = y + (rect.bottom - 10 - y - value_height) // 2
            for line in value_lines:
                rendered = value_font.render(line, True, VALUE_COLOR)
                screen.blit(rendered, rendered.get_rect(midtop=(rect.centerx, value_y)))
                value_y += rendered.get_height()

    def draw_prompts(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the text prompts."""
        prompt = font.render(
            "Press P to Simulate  |  Press Q to Quit",
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

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the metric grid, prompts and messages onto <screen>."""
        label_font = pygame.font.SysFont(None, 20)
        value_font = pygame.font.SysFont(None, 30)
        prompt_font = pygame.font.SysFont(None, 24)
        message_font = pygame.font.SysFont(None, 18)

        screen.fill(BG_COLOR)
        self.draw_grid(screen, label_font, value_font)
        self.draw_prompts(screen, prompt_font)
        self.draw_messages(screen, message_font)
