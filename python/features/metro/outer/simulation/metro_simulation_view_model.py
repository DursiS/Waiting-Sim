import pygame


CELL_SIZE = 130
PADDING = 40
PROMPT_HEIGHT = 80
TEXT_PANEL_WIDTH = 280
MIN_GRID_WIDTH = 720
PANEL_LINE_HEIGHT = 20
SCALAR_ROWS = 2
MATRIX_GAP = 22
MATRIX_FONT_SIZE = 16
MATRIX_LINE_H = 20
MATRIX_LABEL_H = 30
MATRIX_PAD = 14
BG_COLOR = (24, 24, 28)
CELL_COLOR = (70, 130, 180)
BORDER_COLOR = (255, 255, 255)
LABEL_COLOR = (215, 230, 240)
VALUE_COLOR = (255, 255, 255)
PROMPT_COLOR = (200, 200, 60)
PANEL_DIVIDER_COLOR = (70, 70, 80)
MESSAGE_COLOR = (220, 220, 220)
MATRIX_BG_COLOR = (38, 44, 56)
MATRIX_BORDER_COLOR = (84, 94, 114)
MATRIX_LABEL_COLOR = (250, 205, 100)
MATRIX_VALUE_COLOR = (210, 226, 240)

# The metrics the interactor reports, keyed by their (row, column) in the grid.
# Rows 0-1 are single-value moth; rows >= SCALAR_ROWS are full-width matrices.
DEFAULT_CELLS = {
    (0, 0): ("Avg wait time", "-"),
    (0, 1): ("Avg wait (random arrival)", "-"),
    (0, 2): ("Runtime (s)", "-"),
    (1, 0): ("Most visited station", "-"),
    (1, 1): ("Squared-error spread", "-"),
    (2, 0): ("n-step transition matrix", "-"),
    (2, 1): ("Fundamental matrix", "-"),
}


class MetroSimulationViewModel:
    """A grid of scalar simulation metrics above full-width matrix panels,
    with a live side text block of presenter messages."""

    cells: dict[tuple[int, int], tuple[str, str]]
    messages: list[str]
    grid_width: int
    width: int
    height: int
    loading: bool
    _running: bool

    def __init__(
        self,
        cells: dict[tuple[int, int], tuple[str, str]] = None,
        messages: list[str] = None,
    ) -> None:
        """Create a ViewModel showing <moth> as labelled metrics."""
        self.cells = cells or dict(DEFAULT_CELLS)
        self.messages = messages or []
        self.loading = False
        self._running = False
        self._recompute_dimensions()

    def set_loading(self, loading: bool) -> None:
        """Show or hide the animated dots on the last message."""
        self.loading = loading

    def _scalar_cells(self) -> list[tuple[int, int]]:
        """Return the positions of the small single-value metric moth."""
        return [pos for pos in self.cells if pos[0] < SCALAR_ROWS]

    def _matrix_cells(self) -> list[tuple[int, int]]:
        """Return the positions of the full-width matrix panels, top to bottom."""
        return sorted(pos for pos in self.cells if pos[0] >= SCALAR_ROWS)

    def _panel_height(self, value: str) -> int:
        """Return the pixel height a matrix panel needs for <value>."""
        rows = value.count("\n") + 1
        return MATRIX_LABEL_H + rows * MATRIX_LINE_H + MATRIX_PAD

    def _matrices_top(self) -> int:
        """Return the y at which the matrix panels begin, below the scalar grid."""
        return PADDING + SCALAR_ROWS * CELL_SIZE + MATRIX_GAP

    def _recompute_dimensions(self) -> None:
        """Size the window to fit the scalar grid, the matrix panels and the
        side text panel."""
        max_col = max((col for _, col in self._scalar_cells()), default=0)
        self.grid_width = max((max_col + 1) * CELL_SIZE + PADDING * 2, MIN_GRID_WIDTH)

        y = self._matrices_top()
        for pos in self._matrix_cells():
            y += self._panel_height(self.cells[pos][1]) + MATRIX_GAP
        grid_height = y + PROMPT_HEIGHT

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
        self._recompute_dimensions()

    def clear_messages(self) -> None:
        """Empty the side text block."""
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add <message> to the side text block; shown next frame."""
        self.messages.append(message)

    def _wrap_text(
        self, text: str, font: pygame.font.Font, max_width: int
    ) -> list[str]:
        """Split <text> into lines that each fit <max_width>, honouring any
        explicit newlines."""
        lines = []
        for paragraph in text.split("\n"):
            words = paragraph.split(" ")
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
        matrix_font: pygame.font.Font,
    ) -> None:
        """Draw the scalar metric moth, then the full-width matrix panels."""
        for row, col in self._scalar_cells():
            self._draw_scalar_cell(screen, row, col, label_font, value_font)

        y = self._matrices_top()
        for pos in self._matrix_cells():
            label, value = self.cells[pos]
            y = self._draw_matrix_panel(
                screen, label, value, y, label_font, matrix_font
            )
            y += MATRIX_GAP

    def _draw_scalar_cell(
        self,
        screen: pygame.Surface,
        row: int,
        col: int,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        """Draw one small labelled metric cell at (<row>, <col>)."""
        label, value = self.cells[(row, col)]
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

    def _draw_matrix_panel(
        self,
        screen: pygame.Surface,
        label: str,
        value: str,
        top: int,
        label_font: pygame.font.Font,
        matrix_font: pygame.font.Font,
    ) -> int:
        """Draw a full-width matrix panel and return its bottom y."""
        left = PADDING
        width = self.grid_width - PADDING * 2
        height = self._panel_height(value)
        rect = pygame.Rect(left, top, width, height)
        pygame.draw.rect(screen, MATRIX_BG_COLOR, rect, border_radius=6)
        pygame.draw.rect(screen, MATRIX_BORDER_COLOR, rect, width=1, border_radius=6)

        heading = label_font.render(label, True, MATRIX_LABEL_COLOR)
        screen.blit(heading, (left + MATRIX_PAD, top + 6))

        y = top + MATRIX_LABEL_H
        for line in value.split("\n"):
            rendered = matrix_font.render(line, True, MATRIX_VALUE_COLOR)
            screen.blit(rendered, (left + MATRIX_PAD, y))
            y += MATRIX_LINE_H
        return top + height

    def draw_prompts(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the text prompts."""
        prompt = font.render(
            "Press Q to Quit",
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
        last_index = len(self.messages) - 1
        for index, message in enumerate(self.messages):
            if self.loading and index == last_index:
                message += "." * (pygame.time.get_ticks() // 300 % 5 + 1)
            for line in self._wrap_text(message, font, max_width):
                rendered = font.render(line, True, MESSAGE_COLOR)
                screen.blit(rendered, (text_x, y))
                y += rendered.get_height() + 2
            y += 10

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the metric grid, matrix panels, prompts and messages."""
        label_font = pygame.font.SysFont(None, 20)
        value_font = pygame.font.SysFont(None, 30)
        matrix_font = pygame.font.SysFont("consolas", MATRIX_FONT_SIZE)
        prompt_font = pygame.font.SysFont(None, 24)
        message_font = pygame.font.SysFont(None, 18)

        screen.fill(BG_COLOR)
        self.draw_grid(screen, label_font, value_font, matrix_font)
        self.draw_prompts(screen, prompt_font)
        self.draw_messages(screen, message_font)
