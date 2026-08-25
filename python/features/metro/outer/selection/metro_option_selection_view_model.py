import pygame

WIDTH = 860
HEIGHT = 700

BG_COLOR = (24, 24, 28)
TITLE_COLOR = (240, 210, 110)
PANEL_COLOR = (32, 34, 42)
PANEL_BORDER_COLOR = (70, 76, 92)
LABEL_COLOR = (205, 210, 220)
FIELD_BG_COLOR = (44, 47, 57)
FIELD_BORDER_COLOR = (90, 100, 120)
FIELD_FOCUS_COLOR = (240, 210, 110)
FIELD_TEXT_COLOR = (232, 236, 244)
TOGGLE_ON_COLOR = (70, 130, 90)
TOGGLE_OFF_COLOR = (120, 60, 60)
MODE_ON_COLOR = (52, 58, 72)
MODE_OFF_COLOR = (34, 36, 44)
MODE_LABEL_ON = (232, 236, 244)
MODE_LABEL_OFF = (150, 156, 170)
MODE_BORDER_ON = (240, 210, 110)
MODE_BORDER_OFF = (80, 86, 100)
MAP_ON_COLOR = (52, 58, 72)
MAP_OFF_COLOR = (40, 43, 52)
START_COLOR = (70, 130, 90)
START_HOVER_COLOR = (86, 156, 110)
START_LABEL_COLOR = (245, 248, 252)
HINT_COLOR = (150, 160, 175)
ERROR_COLOR = (230, 120, 110)

MODES = ["simulate", "play", "gamble"]
MODE_LABELS = {"simulate": "Simulate", "play": "Play", "gamble": "Gamble"}

FIELDS = {
    "play": [
        ("name", "text", "Name"),
        ("map", "map", "Map"),
        ("rand_arrival", "toggle", "Random arrival"),
        ("animate", "toggle", "Animate"),
    ],
    "gamble": [
        ("name", "text", "Name"),
        ("map", "map", "Map"),
        ("bet_range", "range", "Bet interval (steps)"),
        ("bet_stake", "text", "Stake"),
        ("rand_arrival", "toggle", "Random arrival"),
        ("animate", "toggle", "Animate"),
    ],
    "simulate": [
        ("name", "text", "Name"),
        ("map", "map", "Map"),
        ("trials", "text", "Trials"),
        ("rand_arrival", "toggle", "Random arrival"),
    ],
}


class MetroOptionSelectionViewModel:
    """Holds the option-selection form state (chosen mode plus per-mode field
    values) and renders it, exposing hit-test helpers over the laid-out rects."""

    width: int
    height: int
    map_ids: list[int]
    mode: str
    name: str
    map_id: int
    rand_arrival: bool
    animate: bool
    bet_low: str
    bet_high: str
    bet_stake: str
    trials: str
    focused: str | None
    error: str
    balance: float
    optimal: float | None
    optimal_range: tuple[int, int] | None

    def __init__(self, map_ids: list[int], balance: float) -> None:
        self.width = WIDTH
        self.height = HEIGHT
        self.map_ids = map_ids
        self.balance = balance
        self.mode = "play"
        self.name = ""
        self.map_id = map_ids[-1] if map_ids else 0
        self.rand_arrival = False
        self.animate = True
        self.bet_low = ""
        self.bet_high = ""
        self.bet_stake = ""
        self.trials = "1000"
        self.focused = None
        self.error = ""
        self.optimal = None
        self.optimal_range = None

        self._mode_rects: dict[str, pygame.Rect] = {}
        self._map_rects: dict[int, pygame.Rect] = {}
        self._field_rects: dict[str, pygame.Rect] = {}
        self._panel = pygame.Rect(0, 0, 0, 0)
        self._start_rect = pygame.Rect(0, 0, 0, 0)

        self._font_title = pygame.font.SysFont("consolas", 44, bold=True)
        self._font_mode = pygame.font.SysFont(None, 30)
        self._font_label = pygame.font.SysFont(None, 28)
        self._font_val = pygame.font.SysFont(None, 28)
        self._font_start = pygame.font.SysFont(None, 32, bold=True)
        self._font_hint = pygame.font.SysFont(None, 26)
        self._font_err = pygame.font.SysFont(None, 26)
        self._layout()

    def set_mode(self, mode: str) -> None:
        """Switch the selected mode, clearing focus and error, and re-lay out."""
        self.mode = mode
        self.focused = None
        self.error = ""
        self._layout()

    def text_value(self, key: str) -> str:
        """Return the current text held by field <key>."""
        return getattr(self, key)

    def set_text(self, key: str, value: str) -> None:
        """Set field <key>'s text to <value>."""
        setattr(self, key, value)

    def toggle_value(self, key: str) -> bool:
        """Return the current on/off state of toggle field <key>."""
        return getattr(self, key)

    def flip_toggle(self, key: str) -> None:
        """Flip the on/off state of toggle field <key>."""
        setattr(self, key, not getattr(self, key))

    def field_kind(self, key: str) -> str | None:
        """Return the kind ('text'/'toggle'/'map') of field <key> for this mode."""
        for field_key, kind, _ in FIELDS[self.mode]:
            if field_key == key:
                return kind
        return None

    def mode_at(self, pos: tuple[int, int]) -> str | None:
        """Return the mode button under <pos>, or None."""
        for mode, rect in self._mode_rects.items():
            if rect.collidepoint(pos):
                return mode
        return None

    def map_at(self, pos: tuple[int, int]) -> int | None:
        """Return the map id whose button is under <pos>, or None."""
        for map_id, rect in self._map_rects.items():
            if rect.collidepoint(pos):
                return map_id
        return None

    def field_at(self, pos: tuple[int, int]) -> str | None:
        """Return the text/toggle field key under <pos>, or None."""
        for key, rect in self._field_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def start_at(self, pos: tuple[int, int]) -> bool:
        """Return whether <pos> is on the Start button."""
        return self._start_rect.collidepoint(pos)

    def _layout(self) -> None:
        """Recompute every clickable rect for the current mode's fields."""
        mode_w, mode_h, gap = 200, 48, 16
        total = len(MODES) * mode_w + (len(MODES) - 1) * gap
        x0 = (WIDTH - total) // 2
        self._mode_rects = {
            mode: pygame.Rect(x0 + i * (mode_w + gap), 92, mode_w, mode_h)
            for i, mode in enumerate(MODES)
        }

        self._panel = pygame.Rect(90, 164, WIDTH - 180, HEIGHT - 164 - 120)
        self._field_rects = {}
        self._map_rects = {}
        ctrl_x = self._panel.left + 240
        row_y = self._panel.top + 26
        for key, kind, _ in FIELDS[self.mode]:
            if kind == "text":
                self._field_rects[key] = pygame.Rect(ctrl_x, row_y, 260, 36)
            elif kind == "toggle":
                self._field_rects[key] = pygame.Rect(ctrl_x, row_y, 92, 36)
            elif kind == "map":
                for j, map_id in enumerate(self.map_ids):
                    self._map_rects[map_id] = pygame.Rect(
                        ctrl_x + j * 56, row_y, 46, 36
                    )
            elif kind == "range":
                self._field_rects["bet_low"] = pygame.Rect(ctrl_x, row_y, 104, 36)
                self._field_rects["bet_high"] = pygame.Rect(
                    ctrl_x + 138, row_y, 104, 36
                )
            row_y += 52

        self._start_rect = pygame.Rect((WIDTH - 220) // 2, HEIGHT - 90, 220, 50)

    def draw(self, screen: pygame.Surface) -> None:
        """Render the whole option-selection screen for the current state."""
        self._layout()
        screen.fill(BG_COLOR)

        title = self._font_title.render("Metro", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 46)))

        for mode in MODES:
            rect = self._mode_rects[mode]
            selected = mode == self.mode
            pygame.draw.rect(
                screen, MODE_ON_COLOR if selected else MODE_OFF_COLOR, rect,
                border_radius=8,
            )
            pygame.draw.rect(
                screen, MODE_BORDER_ON if selected else MODE_BORDER_OFF, rect,
                width=3 if selected else 2, border_radius=8,
            )
            label = self._font_mode.render(
                MODE_LABELS[mode], True,
                MODE_LABEL_ON if selected else MODE_LABEL_OFF,
            )
            screen.blit(label, label.get_rect(center=rect.center))

        pygame.draw.rect(screen, PANEL_COLOR, self._panel, border_radius=10)
        pygame.draw.rect(
            screen, PANEL_BORDER_COLOR, self._panel, width=2, border_radius=10
        )

        for key, kind, label in FIELDS[self.mode]:
            self._draw_field(screen, key, kind, label)

        if self.mode == "gamble":
            money = self._font_label.render(
                f"Balance: ${self.balance:.2f}", True, TITLE_COLOR
            )
            screen.blit(money, money.get_rect(topright=(WIDTH - 24, 22)))
            if "bet_stake" in self._field_rects:
                rect = self._field_rects["bet_stake"]
                text = (
                    "Optimal: --"
                    if self.optimal is None
                    else f"Optimal: ${self.optimal:.2f}"
                )
                optimal = self._font_label.render(text, True, TITLE_COLOR)
                screen.blit(
                    optimal, optimal.get_rect(midleft=(rect.right + 16, rect.centery))
                )
            if self.optimal_range is not None and "bet_high" in self._field_rects:
                rect = self._field_rects["bet_high"]
                low, high = self.optimal_range
                best = self._font_label.render(
                    f"Best: {low}-{high}", True, TITLE_COLOR
                )
                screen.blit(best, best.get_rect(midleft=(rect.right + 24, rect.centery)))

        if self.error:
            error = self._font_err.render(self.error, True, ERROR_COLOR)
            screen.blit(
                error, error.get_rect(center=(WIDTH // 2, self._start_rect.top - 22))
            )

        hovered = self._start_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(
            screen, START_HOVER_COLOR if hovered else START_COLOR, self._start_rect,
            border_radius=8,
        )
        start = self._font_start.render("Start", True, START_LABEL_COLOR)
        screen.blit(start, start.get_rect(center=self._start_rect.center))

        hint = self._font_hint.render("Q  Quit", True, HINT_COLOR)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 26)))

    def _draw_field(
        self, screen: pygame.Surface, key: str, kind: str, label: str
    ) -> None:
        """Render one labelled field row for <key> of the given <kind>."""
        if kind == "map":
            row_rect = next(iter(self._map_rects.values()))
        elif kind == "range":
            row_rect = self._field_rects["bet_low"]
        else:
            row_rect = self._field_rects[key]
        text = self._font_label.render(label, True, LABEL_COLOR)
        screen.blit(text, text.get_rect(midleft=(self._panel.left + 26, row_rect.centery)))

        if kind == "text":
            self._draw_text_box(screen, key)
        elif kind == "range":
            self._draw_text_box(screen, "bet_low")
            self._draw_text_box(screen, "bet_high")
            dash = self._font_val.render("-", True, LABEL_COLOR)
            mid_x = (
                self._field_rects["bet_low"].right + self._field_rects["bet_high"].left
            ) // 2
            screen.blit(dash, dash.get_rect(center=(mid_x, row_rect.centery)))
        elif kind == "toggle":
            rect = self._field_rects[key]
            on = self.toggle_value(key)
            pygame.draw.rect(
                screen, TOGGLE_ON_COLOR if on else TOGGLE_OFF_COLOR, rect,
                border_radius=6,
            )
            value = self._font_val.render("ON" if on else "OFF", True, FIELD_TEXT_COLOR)
            screen.blit(value, value.get_rect(center=rect.center))
        elif kind == "map":
            for map_id, rect in self._map_rects.items():
                selected = map_id == self.map_id
                pygame.draw.rect(
                    screen, MAP_ON_COLOR if selected else MAP_OFF_COLOR, rect,
                    border_radius=6,
                )
                pygame.draw.rect(
                    screen, FIELD_FOCUS_COLOR if selected else FIELD_BORDER_COLOR, rect,
                    width=2, border_radius=6,
                )
                value = self._font_val.render(str(map_id), True, FIELD_TEXT_COLOR)
                screen.blit(value, value.get_rect(center=rect.center))

    def _draw_text_box(self, screen: pygame.Surface, key: str) -> None:
        """Render the text field <key> with its value and focus outline."""
        rect = self._field_rects[key]
        focused = self.focused == key
        pygame.draw.rect(screen, FIELD_BG_COLOR, rect, border_radius=6)
        pygame.draw.rect(
            screen, FIELD_FOCUS_COLOR if focused else FIELD_BORDER_COLOR, rect,
            width=2, border_radius=6,
        )
        shown = self.text_value(key) + ("_" if focused else "")
        value = self._font_val.render(shown, True, FIELD_TEXT_COLOR)
        screen.blit(value, value.get_rect(midleft=(rect.left + 10, rect.centery)))
