import pygame


WIDTH = 940
HEIGHT = 560
PLOT_LEFT = 70
PLOT_RIGHT = 28
PLOT_TOP = 28
PLOT_BOTTOM = 42
MIN_SPAN = 100.0
ROLLING_WINDOW_SECONDS = 60.0
STATS_X = 14
STATS_Y = 14
STATS_W = 230
STATS_H = 78
CONTROLS_Y = STATS_Y + STATS_H + 12

SKY_TOP_COLOR = (86, 148, 220)
SKY_HORIZON_COLOR = (188, 222, 248)
CLOUD_COLOR = (248, 250, 255)
MEAN_LINE_COLOR = (255, 255, 255)
TRAJECTORY_COLOR = (34, 50, 78)
ROLLING_COLOR = (236, 138, 42)
QUIT_KEY_COLOR = (250, 210, 90)
QUIT_LABEL_COLOR = (240, 246, 255)
BIRD_COLOR = (32, 38, 54)
AXIS_COLOR = (70, 96, 130)
PANEL_BG_COLOR = (12, 22, 38, 190)
PANEL_LINE_COLOR = (120, 150, 185)
STAT_LABEL_COLOR = (176, 202, 232)
STAT_VALUE_COLOR = (245, 249, 255)
PROMPT_COLOR = (245, 249, 255)
CLOUDS = [(180, 110, 70), (520, 80, 95), (760, 160, 60), (360, 210, 55), (660, 300, 80)]


class FlyingViewModel:
    """The flight scene: a cloudy sky behind a plot that is rolled out point by
    point, a bird flapping along the newest point of the 60-second rolling
    average, an optional (toggleable) raw-flight line, and the running
    mean-reversion, highest and lowest-altitude stats."""

    flight_hist: list[tuple[float, float]]
    rolling: list[tuple[float, float] | None]
    revealed: int
    mean: float
    unit: str
    duration: float
    y_min: float
    y_max: float
    reversions: int
    highest: float | None
    wing_up: bool
    show_raw: bool
    width: int
    height: int
    _prev_side: int | None
    _sky: pygame.Surface | None

    def __init__(self) -> None:
        self.flight_hist = []
        self.rolling = []
        self.revealed = 0
        self.mean = 0.0
        self.unit = "feet"
        self.duration = 0.0
        self.y_min = 0.0
        self.y_max = 0.0
        self.reversions = 0
        self.highest = None
        self.wing_up = False
        self.show_raw = True
        self.width = WIDTH
        self.height = HEIGHT
        self._prev_side = None
        self._sky = None

    def set_flight(
        self, flight_hist: list[tuple[float, float]], mean: float, unit: str
    ) -> None:
        """Store a finished flight to roll out, sizing the plot to its range and
        resetting the running stats."""
        self.flight_hist = flight_hist
        self.rolling = self._rolling_average(flight_hist)
        self.mean = mean
        self.unit = unit
        self.revealed = 0
        self.reversions = 0
        self.highest = None
        self._prev_side = None
        self.duration = flight_hist[-1][0] if flight_hist else 0.0
        heights = [h for _, h in flight_hist] or [mean]
        low, high = min(heights + [mean]), max(heights + [mean])
        if high - low < MIN_SPAN:
            mid = (high + low) / 2
            low, high = mid - MIN_SPAN / 2, mid + MIN_SPAN / 2
        pad = (high - low) * 0.08
        self.y_min, self.y_max = low - pad, high + pad

    def _rolling_average(
        self, flight_hist: list[tuple[float, float]]
    ) -> list[tuple[float, float] | None]:
        """Return the trailing 60-second average altitude aligned with each
        flight point, or None before 60 seconds of flight have elapsed."""
        rolling: list[tuple[float, float] | None] = [None] * len(flight_hist)
        if len(flight_hist) < 2:
            return rolling
        dt = flight_hist[1][0] - flight_hist[0][0] or 1.0
        window = max(1, round(ROLLING_WINDOW_SECONDS / dt))
        prefix = [0.0]
        for _, height in flight_hist:
            prefix.append(prefix[-1] + height)
        for i in range(window, len(flight_hist)):
            average = (prefix[i + 1] - prefix[i - window]) / (window + 1)
            rolling[i] = (flight_hist[i][0], average)
        return rolling

    def ready(self) -> bool:
        """Return whether a flight is loaded and waiting to be rolled out."""
        return len(self.flight_hist) > 0

    def done(self) -> bool:
        """Return whether the whole flight has been rolled out."""
        return self.ready() and self.revealed >= len(self.flight_hist)

    def reveal(self, count: int) -> None:
        """Reveal the next <count> plotted points, folding them into the running
        highest-altitude and mean-reversion (mean-crossing) stats."""
        end = min(self.revealed + count, len(self.flight_hist))
        for i in range(self.revealed, end):
            height = self.flight_hist[i][1]
            if self.highest is None:
                self.highest = height
            else:
                self.highest = max(self.highest, height)
            side = (height > self.mean) - (height < self.mean)
            if side != 0:
                if self._prev_side is not None and side != self._prev_side:
                    self.reversions += 1
                self._prev_side = side
        self.revealed = end

    def set_wing(self, up: bool) -> None:
        """Set the bird's wing position for the flap animation."""
        self.wing_up = up

    def toggle_raw(self) -> None:
        """Show or hide the raw flight line, leaving the average and bird."""
        self.show_raw = not self.show_raw

    def _sx(self, t: float) -> int:
        """Map flight time <t> to a screen x within the plot area."""
        span = self.duration or 1.0
        return int(PLOT_LEFT + (t / span) * (self.width - PLOT_LEFT - PLOT_RIGHT))

    def _sy(self, height: float) -> int:
        """Map an altitude to a screen y within the plot area (up is up)."""
        span = (self.y_max - self.y_min) or 1.0
        frac = (height - self.y_min) / span
        return int(self.height - PLOT_BOTTOM - frac * (self.height - PLOT_TOP - PLOT_BOTTOM))

    def _build_sky(self) -> pygame.Surface:
        """Build the vertical sky gradient with a few soft clouds baked in."""
        sky = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            f = y / self.height
            color = tuple(
                int(a + (b - a) * f)
                for a, b in zip(SKY_TOP_COLOR, SKY_HORIZON_COLOR)
            )
            pygame.draw.line(sky, color, (0, y), (self.width, y))
        for cx, cy, r in CLOUDS:
            puff = pygame.Surface((r * 4, r * 2), pygame.SRCALPHA)
            for dx, dy, rr in ((r, r, r), (r * 2, r, int(r * 0.8)), (int(r * 1.4), int(r * 0.7), int(r * 0.7))):
                pygame.draw.circle(puff, (*CLOUD_COLOR, 210), (dx, dy), rr)
            sky.blit(puff, (cx, cy))
        return sky

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the sky, and once a flight is loaded the rolled-out trajectory,
        the bird at its leading point and the running stats."""
        if self._sky is None or self._sky.get_size() != (self.width, self.height):
            self._sky = self._build_sky()
        screen.blit(self._sky, (0, 0))
        if not self.ready():
            return

        self._draw_axes(screen)
        self._draw_trajectory(screen)
        self._draw_rolling(screen)
        self._draw_legend(screen)
        self._draw_stats(screen)
        if self.done():
            self._draw_controls(screen)

    def _draw_axes(self, screen: pygame.Surface) -> None:
        """Draw the plot frame and the dashed mean-altitude line."""
        left, right = PLOT_LEFT, self.width - PLOT_RIGHT
        top, bottom = PLOT_TOP, self.height - PLOT_BOTTOM
        pygame.draw.line(screen, AXIS_COLOR, (left, top), (left, bottom), 2)
        pygame.draw.line(screen, AXIS_COLOR, (left, bottom), (right, bottom), 2)
        my = self._sy(self.mean)
        for x in range(left, right, 14):
            pygame.draw.line(screen, MEAN_LINE_COLOR, (x, my), (x + 7, my), 1)
        font = pygame.font.SysFont(None, 20)
        label = font.render(f"mean {self.mean:.0f} {self.unit}", True, MEAN_LINE_COLOR)
        screen.blit(label, (right - label.get_width(), my - 20))

    def _draw_trajectory(self, screen: pygame.Surface) -> None:
        """Draw the revealed raw-flight line when it is toggled on -- no bird,
        the bird now rides the rolling average instead."""
        if not self.show_raw:
            return
        points = [
            (self._sx(t), self._sy(h))
            for t, h in self.flight_hist[: self.revealed]
        ]
        if len(points) >= 2:
            pygame.draw.lines(screen, TRAJECTORY_COLOR, False, points, 2)

    def _draw_bird(self, screen: pygame.Surface, bx: int, by: int) -> None:
        """Draw the gull at (<bx>, <by>) with wings up or down for the flap."""
        tip_dy = -11 if self.wing_up else 7
        wing = [(bx - 16, by + tip_dy), (bx, by), (bx + 16, by + tip_dy)]
        pygame.draw.lines(screen, BIRD_COLOR, False, wing, 3)
        pygame.draw.circle(screen, BIRD_COLOR, (bx, by), 4)

    def _draw_rolling(self, screen: pygame.Surface) -> None:
        """Draw the revealed portion of the 60-second rolling-average line and
        the flapping bird at its newest point (the line begins at 60 seconds)."""
        points = []
        for i in range(self.revealed):
            entry = self.rolling[i]
            if entry is not None:
                t, average = entry
                points.append((self._sx(t), self._sy(average)))
        if len(points) >= 2:
            pygame.draw.lines(screen, ROLLING_COLOR, False, points, 2)
        if points:
            self._draw_bird(screen, *points[-1])

    def _draw_legend(self, screen: pygame.Surface) -> None:
        """Draw the top-right legend, dropping the flight row when it is hidden."""
        font = pygame.font.SysFont(None, 20)
        rows = [(ROLLING_COLOR, f"{int(ROLLING_WINDOW_SECONDS)}s average")]
        if self.show_raw:
            rows.insert(0, (TRAJECTORY_COLOR, "Flight"))
        box = pygame.Rect(self.width - 186, 14, 172, 12 + len(rows) * 24)
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill(PANEL_BG_COLOR)
        screen.blit(panel, box.topleft)
        pygame.draw.rect(screen, PANEL_LINE_COLOR, box, width=1, border_radius=8)
        y = box.top + 12
        for color, label in rows:
            pygame.draw.line(screen, color, (box.left + 12, y + 7), (box.left + 44, y + 7), 3)
            screen.blit(font.render(label, True, STAT_LABEL_COLOR), (box.left + 54, y))
            y += 24

    def _draw_controls(self, screen: pygame.Surface) -> None:
        """Draw the classic Q Quit control and, right below it, the R raw-flight
        toggle, at the top left below the stats."""
        key_font = pygame.font.SysFont(None, 26, bold=True)
        label_font = pygame.font.SysFont(None, 26)
        raw_label = "Hide raw flight" if self.show_raw else "Show raw flight"
        y = CONTROLS_Y
        for key_text, label_text in (("Q", "Quit"), ("R", raw_label)):
            key = key_font.render(key_text, True, QUIT_KEY_COLOR)
            screen.blit(key, (STATS_X + 8, y))
            label = label_font.render(label_text, True, QUIT_LABEL_COLOR)
            screen.blit(label, (STATS_X + 8 + key.get_width() + 9, y))
            y += 28

    def _draw_stats(self, screen: pygame.Surface) -> None:
        """Draw the top-left panel of running flight stats."""
        box = pygame.Rect(STATS_X, STATS_Y, STATS_W, STATS_H)
        panel = pygame.Surface(box.size, pygame.SRCALPHA)
        panel.fill(PANEL_BG_COLOR)
        screen.blit(panel, box.topleft)
        pygame.draw.rect(screen, PANEL_LINE_COLOR, box, width=1, border_radius=8)

        label_font = pygame.font.SysFont(None, 22)
        value_font = pygame.font.SysFont(None, 24, bold=True)
        rows = [
            ("Mean reversions", str(self.reversions)),
            ("Highest", f"{self.highest:.0f} {self.unit}" if self.highest is not None else "--"),
        ]
        y = box.top + 12
        for label, value in rows:
            screen.blit(label_font.render(label, True, STAT_LABEL_COLOR), (box.left + 14, y))
            value_surf = value_font.render(value, True, STAT_VALUE_COLOR)
            screen.blit(value_surf, value_surf.get_rect(topright=(box.right - 14, y - 1)))
            y += 32
