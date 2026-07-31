import math

import pygame

from Entities import Station


ROAD_LENGTH = 220
MARGIN_X = 130
HUD_TOP_HEIGHT = 92
NODE_TOP_PAD = 80
NODE_BOTTOM_PAD = 100
BOTTOM_BAR_HEIGHT = 56
MIN_WIDTH = 900
MIN_HEIGHT = 460
NODE_RADIUS = 14
TRACK_GAP = 9
TRACK_WIDTH = 3
ARROW_LEN = 9
ARROW_WID = 6
TRAIN_W = 40
TRAIN_H = 9

BG_COLOR = (16, 18, 24)
HUD_COLOR = (10, 12, 16)
HUD_LINE_COLOR = (44, 48, 58)
TRACK_COLOR = (66, 74, 90)
ARROW_COLOR = (120, 132, 152)
NODE_COLOR = (66, 120, 170)
NODE_BORDER_COLOR = (150, 172, 196)
CURRENT_COLOR = (250, 180, 60)
CURRENT_RING_COLOR = (255, 226, 150)
END_COLOR = (86, 190, 112)
LABEL_COLOR = (208, 220, 232)
CURRENT_LABEL_COLOR = (255, 224, 150)
END_LABEL_COLOR = (150, 235, 175)
SUB_LABEL_COLOR = (150, 162, 178)
TRAIN_COLOR = (240, 205, 90)
TRAIN_BORDER_COLOR = (60, 50, 24)
TRAIN_LABEL_COLOR = (240, 224, 170)
TOTAL_WAIT_COLOR = (255, 235, 150)
BEST_SCORE_COLOR = (150, 235, 170)
STATUS_COLOR = (200, 212, 228)
PROMPT_COLOR = (200, 200, 90)


class GameViewModel:
    """A Rail-Route style map of the world: stations are nodes joined by dual
    one-way tracks, and the single fastest train is animated from its station
    to the player's in real time. A compact HUD carries the wait totals, the
    latest status lines and the controls."""

    stations: list[Station]
    curr_station: Station | None
    messages: list[str]
    wait_stats: list[str]
    total_wait: float
    best_highscore: str
    loading: bool
    incoming_train: tuple[Station, Station | None, int, float] | None
    width: int
    height: int
    road_length: float
    _running: bool

    def __init__(
        self,
        stations: list[Station] = None,
        curr_station: Station | None = None,
        messages: list[str] = None,
    ) -> None:
        """Create a rail-map ViewModel for <stations>, player at <curr_station>."""
        self.stations = stations or []
        self.curr_station = curr_station
        self.messages = messages or []
        self.wait_stats = []
        self.total_wait = 0.0
        self.best_highscore = "N/A"
        self.loading = False
        self.incoming_train = None
        self.road_length = ROAD_LENGTH
        self._running = False
        self._recompute_dimensions()

    def _recompute_dimensions(self) -> None:
        """Size the window to the station layout plus the HUD bars."""
        x_m = max((s.coordinates[0] for s in self.stations), default=0)
        y_m = max((s.coordinates[1] for s in self.stations), default=0)
        self.width = max(int(MARGIN_X * 2 + x_m * self.road_length), MIN_WIDTH)
        self.height = max(
            int(
                HUD_TOP_HEIGHT + NODE_TOP_PAD + y_m * self.road_length
                + NODE_BOTTOM_PAD + BOTTOM_BAR_HEIGHT
            ),
            MIN_HEIGHT,
        )

    def set_stations(self, stations: list[Station]) -> None:
        """Replace the shown stations and resize to fit them."""
        self.stations = stations
        self._recompute_dimensions()

    def set_current_station(self, station: Station | None) -> None:
        """Set the player's station; the arriving train has now completed."""
        self.curr_station = station
        self.incoming_train = None

    def set_incoming_train(self, source: Station, seconds: float) -> None:
        """Start the fastest train travelling from <source> to the player's
        current station over <seconds> real seconds."""
        self.incoming_train = (
            source, self.curr_station, pygame.time.get_ticks(), seconds
        )

    def clear_messages(self) -> None:
        """Empty the running status messages."""
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add <message>; the HUD shows the latest ones next frame."""
        self.messages.append(message)

    def clear_wait_stats(self) -> None:
        """Empty the wait-statistics header (unused by the rail HUD)."""
        self.wait_stats = []

    def add_wait_stat(self, stat: str) -> None:
        """Record a wait statistic (kept for the presenter contract)."""
        self.wait_stats.append(stat)

    def set_total_wait(self, total_wait: float) -> None:
        """Set the player's cumulative wait time shown in the HUD."""
        self.total_wait = total_wait

    def set_best_highscore(self, best_highscore: str) -> None:
        """Set the current map's best highscore shown in the HUD."""
        self.best_highscore = best_highscore

    def set_loading(self, loading: bool) -> None:
        """Show or hide the animated dots on the latest status line."""
        self.loading = loading

    def _node_pos(self, station: Station) -> tuple[int, int]:
        """Return the screen centre of <station> from its grid coordinates."""
        x, y = station.coordinates
        return (
            int(MARGIN_X + x * self.road_length),
            int(HUD_TOP_HEIGHT + NODE_TOP_PAD + y * self.road_length),
        )

    def _road_length(self, from_station: Station, to_station: Station) -> float:
        """Return the road length from <from_station> to <to_station>.

        Per-connection and per-direction lengths will be stored here; a single
        shared length is used for every road for now."""
        return self.road_length

    def _pairs(self) -> list[tuple[Station, Station]]:
        """Return each grid-adjacent station pair exactly once."""
        by_coord = {tuple(s.coordinates): s for s in self.stations}
        pairs = []
        for station in self.stations:
            x, y = station.coordinates
            for dx, dy in ((1, 0), (0, 1)):
                neighbour = by_coord.get((x + dx, y + dy))
                if neighbour is not None:
                    pairs.append((station, neighbour))
        return pairs

    def _truncate(
        self, text: str, font: pygame.font.Font, max_width: int
    ) -> str:
        """Return <text> shortened with an ellipsis to fit <max_width>."""
        if font.size(text)[0] <= max_width:
            return text
        while text and font.size(text + "...")[0] > max_width:
            text = text[:-1]
        return text + "..."

    def _draw_tracks(self, screen: pygame.Surface) -> None:
        """Draw every connection as two one-way roads, each drawn to its own
        (currently shared) length with the arrow at its midpoint."""
        for a, b in self._pairs():
            ax, ay = self._node_pos(a)
            bx, by = self._node_pos(b)
            gap = math.hypot(bx - ax, by - ay) or 1
            ux, uy = (bx - ax) / gap, (by - ay) / gap
            px, py = -uy, ux
            self._draw_road(screen, (ax, ay), (ux, uy), (px, py), self._road_length(a, b))
            self._draw_road(screen, (bx, by), (-ux, -uy), (-px, -py), self._road_length(b, a))

    def _draw_road(
        self,
        screen: pygame.Surface,
        origin: tuple[float, float],
        direction: tuple[float, float],
        perp: tuple[float, float],
        length: float,
    ) -> None:
        """Draw a one-way road of <length> from <origin> along <direction>,
        offset to its own lane, with the direction arrow at its midpoint."""
        ux, uy = direction
        ox = origin[0] + perp[0] * TRACK_GAP / 2
        oy = origin[1] + perp[1] * TRACK_GAP / 2
        start = (ox + ux * NODE_RADIUS, oy + uy * NODE_RADIUS)
        end = (ox + ux * (length - NODE_RADIUS), oy + uy * (length - NODE_RADIUS))
        pygame.draw.line(screen, TRACK_COLOR, start, end, TRACK_WIDTH)
        mid = (ox + ux * length / 2, oy + uy * length / 2)
        self._draw_arrow(screen, mid, direction)

    def _draw_arrow(
        self,
        screen: pygame.Surface,
        pos: tuple[float, float],
        direction: tuple[float, float],
    ) -> None:
        """Draw a small filled arrowhead at <pos> pointing along <direction>."""
        ux, uy = direction
        px, py = -uy, ux
        tip = (pos[0] + ux * ARROW_LEN, pos[1] + uy * ARROW_LEN)
        left = (pos[0] - ux * ARROW_LEN + px * ARROW_WID,
                pos[1] - uy * ARROW_LEN + py * ARROW_WID)
        right = (pos[0] - ux * ARROW_LEN - px * ARROW_WID,
                 pos[1] - uy * ARROW_LEN - py * ARROW_WID)
        pygame.draw.polygon(screen, ARROW_COLOR, [tip, left, right])

    def _draw_stations(
        self,
        screen: pygame.Surface,
        label_font: pygame.font.Font,
        sub_font: pygame.font.Font,
    ) -> None:
        """Draw every station node with its name and a tag beneath it."""
        for station in self.stations:
            cx, cy = self._node_pos(station)
            is_current = (
                self.curr_station is not None
                and station.id == self.curr_station.id
            )
            if is_current:
                color, label_color = CURRENT_COLOR, CURRENT_LABEL_COLOR
            elif station.end:
                color, label_color = END_COLOR, END_LABEL_COLOR
            else:
                color, label_color = NODE_COLOR, LABEL_COLOR

            pygame.draw.circle(screen, color, (cx, cy), NODE_RADIUS)
            pygame.draw.circle(screen, NODE_BORDER_COLOR, (cx, cy), NODE_RADIUS, 2)
            if is_current:
                pygame.draw.circle(
                    screen, CURRENT_RING_COLOR, (cx, cy), NODE_RADIUS + 6, 2
                )

            name = label_font.render(station.name, True, label_color)
            screen.blit(name, name.get_rect(midtop=(cx, cy + NODE_RADIUS + 7)))
            tag = "END" if station.end else station.rule_name
            sub = sub_font.render(tag, True, SUB_LABEL_COLOR)
            screen.blit(
                sub,
                sub.get_rect(midtop=(cx, cy + NODE_RADIUS + 7 + name.get_height())),
            )

    def _make_train_surface(self) -> pygame.Surface:
        """Build the plain train rectangle drawn nose-right, ready to rotate."""
        surf = pygame.Surface((TRAIN_W, TRAIN_H), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, TRAIN_W, TRAIN_H)
        pygame.draw.rect(surf, TRAIN_COLOR, rect, border_radius=3)
        pygame.draw.rect(surf, TRAIN_BORDER_COLOR, rect, width=1, border_radius=3)
        return surf

    def _draw_train(
        self, screen: pygame.Surface, label_font: pygame.font.Font
    ) -> None:
        """Draw the fastest train part-way along its lane toward the player,
        rotated to face its direction of travel."""
        if self.incoming_train is None:
            return
        source, target, start_ticks, duration = self.incoming_train
        if target is None:
            return
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0
        progress = 1.0 if duration <= 0 else min(elapsed / duration, 1.0)

        sx, sy = self._node_pos(source)
        tx, ty = self._node_pos(target)
        dx, dy = tx - sx, ty - sy
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        off = TRACK_GAP / 2
        x = sx + dx * progress + px * off
        y = sy + dy * progress + py * off

        sprite = pygame.transform.rotate(
            self._make_train_surface(), math.degrees(math.atan2(-uy, ux))
        )
        screen.blit(sprite, sprite.get_rect(center=(int(x), int(y))))
        label = label_font.render(f"{duration:.1f}s", True, TRAIN_LABEL_COLOR)
        screen.blit(
            label, label.get_rect(midbottom=(int(x), int(y) - TRAIN_W // 2 - 2))
        )

    def _draw_hud(
        self,
        screen: pygame.Surface,
        hud_font: pygame.font.Font,
        status_font: pygame.font.Font,
        prompt_font: pygame.font.Font,
    ) -> None:
        """Draw the top totals/status bar and the bottom controls bar."""
        pygame.draw.rect(screen, HUD_COLOR, (0, 0, self.width, HUD_TOP_HEIGHT))
        pygame.draw.line(
            screen, HUD_LINE_COLOR, (0, HUD_TOP_HEIGHT), (self.width, HUD_TOP_HEIGHT), 2
        )
        total = hud_font.render(
            f"Total wait: {self.total_wait:.1f}s", True, TOTAL_WAIT_COLOR
        )
        screen.blit(total, (24, 20))
        best = hud_font.render(f"Best: {self.best_highscore}", True, BEST_SCORE_COLOR)
        screen.blit(best, (24, 20 + total.get_height() + 8))

        status_x = 24 + max(total.get_width(), best.get_width()) + 40
        status_width = self.width - status_x - 24
        y = 22
        for line in self._status_lines():
            rendered = status_font.render(
                self._truncate(line, status_font, status_width), True, STATUS_COLOR
            )
            screen.blit(rendered, (status_x, y))
            y += rendered.get_height() + 4

        bar_top = self.height - BOTTOM_BAR_HEIGHT
        pygame.draw.rect(screen, HUD_COLOR, (0, bar_top, self.width, BOTTOM_BAR_HEIGHT))
        pygame.draw.line(screen, HUD_LINE_COLOR, (0, bar_top), (self.width, bar_top), 2)
        prompt = prompt_font.render(
            "P Play    C Continue    R Restart    Q Quit", True, PROMPT_COLOR
        )
        screen.blit(
            prompt, prompt.get_rect(center=(self.width // 2, bar_top + BOTTOM_BAR_HEIGHT // 2))
        )

    def _status_lines(self) -> list[str]:
        """Return the latest status lines, animating dots while loading."""
        if not self.messages:
            return []
        lines = self.messages[-2:]
        if self.loading:
            dots = "." * (pygame.time.get_ticks() // 300 % 5 + 1)
            lines = lines[:-1] + [lines[-1] + dots]
        return lines

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the rail map and the HUD onto <screen>."""
        label_font = pygame.font.SysFont(None, 22)
        sub_font = pygame.font.SysFont(None, 16)
        hud_font = pygame.font.SysFont(None, 24)
        status_font = pygame.font.SysFont(None, 22)
        prompt_font = pygame.font.SysFont(None, 24)

        screen.fill(BG_COLOR)
        self._draw_tracks(screen)
        self._draw_stations(screen, label_font, sub_font)
        self._draw_train(screen, sub_font)
        self._draw_hud(screen, hud_font, status_font, prompt_font)


class DefaultViewModel(GameViewModel):
    """Default homescreen presenting the stations and available controls."""

    def __init__(self, stations: list[Station]) -> None:
        """Create a DefaultViewModel presenting <stations> and the controls."""
        super().__init__(
            stations=stations,
            curr_station=None,
            messages=[
                "P - Play: start a new game",
                "C - Continue: resume a saved game",
                "Q - Quit: exit the game",
            ],
        )
