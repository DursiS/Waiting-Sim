import math

import pygame

from Entities import Station


ROAD_LENGTH = 220
MARGIN_X = 130
HUD_TOP_HEIGHT = 106
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
CONTROL_GAP = 54

CONTROLS = (("P", "Play"), ("C", "Continue"), ("R", "Restart"), ("Q", "Quit"))

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
BET_RESULT_COLOR = (250, 220, 130)
BEST_SCORE_COLOR = (150, 235, 170)
STATUS_COLOR = (200, 212, 228)
KEY_COLOR = (250, 210, 90)
CONTROL_LABEL_COLOR = (200, 210, 224)


class GameViewModel:
    """A Rail-Route style map of the world: stations are nodes joined by dual
    one-way tracks, and the winning train departs from the player's station
    toward the neighbour whose train arrived first. A compact HUD carries the
    wait totals, the latest status lines and the controls."""

    stations: list[Station]
    curr_station: Station | None
    messages: list[str]
    wait_stats: list[str]
    total_wait: float
    best_highscore: str
    loading: bool
    game_over: bool
    incoming_train: tuple[Station | None, Station, int, float] | None
    last_train: tuple[str, str] | None
    roads: list[tuple[tuple[int, int], tuple[int, int]]]
    controls: tuple[tuple[str, str], ...]
    bet_result: str | None
    show_best: bool
    show_controls: bool
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
        self.game_over = False
        self.incoming_train = None
        self.last_train = None
        self.roads = []
        self.controls = CONTROLS
        self.bet_result = None
        self.show_best = True
        self.show_controls = True
        self.road_length = ROAD_LENGTH
        self._running = False
        self._recompute_dimensions()

    def set_controls(self, controls: tuple[tuple[str, str], ...]) -> None:
        """Replace the bottom control hints (e.g. only Restart/Quit)."""
        self.controls = controls

    def set_bet_result(self, bet_result: str | None) -> None:
        """Set the gamble result line shown in the HUD, or clear it."""
        self.bet_result = bet_result

    def set_show_best(self, show_best: bool) -> None:
        """Show or hide the best-completion line in the HUD."""
        self.show_best = show_best

    def set_show_controls(self, show_controls: bool) -> None:
        """Show or hide the bottom control bar."""
        self.show_controls = show_controls

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
        self.last_train = None
        self._recompute_dimensions()

    def set_roads(
        self, roads: list[tuple[tuple[int, int], tuple[int, int]]]
    ) -> None:
        """Set the roads to draw, each an ordered (from, to) coordinate pair.

        One lane is drawn per road, so a connection roaded both ways shows dual
        tracks and a one-way road shows a single lane."""
        self.roads = roads

    def set_current_station(self, station: Station | None) -> None:
        """Set the player's station; the departing train has now completed."""
        self.curr_station = station
        self.incoming_train = None

    def set_incoming_train(self, destination: Station, travel_seconds: float) -> None:
        """Depart the winning train -- the neighbour whose train arrived first --
        from the player's station toward <destination>, animating it over
        <travel_seconds>, the real time the ride spends travelling the line."""
        origin = self.curr_station
        self.incoming_train = (
            origin, destination, pygame.time.get_ticks(), travel_seconds,
        )
        self.last_train = (
            origin.name if origin is not None else "?", destination.name
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

    def set_game_over(self, game_over: bool) -> None:
        """Mark the game finished, clearing the turn HUD so only the closing
        message and its prompt are shown."""
        self.game_over = game_over
        if game_over:
            self.loading = False
            self.incoming_train = None
            self.last_train = None

    def _node_pos(self, station: Station) -> tuple[int, int]:
        """Return the screen centre of <station> from its grid coordinates."""
        return self._node_pos_at(station.coordinates)

    def _node_pos_at(self, coordinates: tuple[int, int]) -> tuple[int, int]:
        """Return the screen centre of the node at grid <coordinates>."""
        x, y = coordinates
        return (
            int(MARGIN_X + x * self.road_length),
            int(HUD_TOP_HEIGHT + NODE_TOP_PAD + y * self.road_length),
        )

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
        """Draw each road in the world as its own one-way lane with an arrow at
        its midpoint, so a connection roaded both ways shows dual tracks while a
        one-way road shows a single lane."""
        for from_coord, to_coord in self.roads:
            ax, ay = self._node_pos_at(from_coord)
            bx, by = self._node_pos_at(to_coord)
            gap = math.hypot(bx - ax, by - ay) or 1
            ux, uy = (bx - ax) / gap, (by - ay) / gap
            px, py = -uy, ux
            self._draw_road(screen, (ax, ay), (ux, uy), (px, py), gap)

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
            tags = [station.rule_name] + (["END"] if station.end else [])
            sub_y = cy + NODE_RADIUS + 7 + name.get_height()
            for tag in tags:
                sub = sub_font.render(tag, True, SUB_LABEL_COLOR)
                screen.blit(sub, sub.get_rect(midtop=(cx, sub_y)))
                sub_y += sub.get_height()

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
        """Draw the winning train part-way from the player's station toward its
        destination, rotated to face its direction of travel."""
        if self.incoming_train is None:
            return
        origin, destination, start_ticks, travel = self.incoming_train
        if origin is None:
            return
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000.0
        progress = 1.0 if travel <= 0 else min(elapsed / travel, 1.0)

        sx, sy = self._node_pos(origin)
        tx, ty = self._node_pos(destination)
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
        label = label_font.render(f"{travel:.1f}s", True, TRAIN_LABEL_COLOR)
        screen.blit(
            label, label.get_rect(midbottom=(int(x), int(y) - TRAIN_W // 2 - 2))
        )

    def _draw_hud(
        self,
        screen: pygame.Surface,
        hud_font: pygame.font.Font,
        status_font: pygame.font.Font,
    ) -> None:
        """Draw the top totals-and-status bar."""
        pygame.draw.rect(screen, HUD_COLOR, (0, 0, self.width, HUD_TOP_HEIGHT))
        pygame.draw.line(
            screen, HUD_LINE_COLOR, (0, HUD_TOP_HEIGHT), (self.width, HUD_TOP_HEIGHT), 2
        )
        total = hud_font.render(
            f"Total wait: {self.total_wait:.1f}s", True, TOTAL_WAIT_COLOR
        )
        screen.blit(total, (24, 20))
        best_width = 0
        if self.show_best:
            best = hud_font.render(f"Best: {self.best_highscore}", True, BEST_SCORE_COLOR)
            screen.blit(best, (24, 20 + total.get_height() + 8))
            best_width = best.get_width()

        if self.bet_result is not None:
            y = 14
            for line in self.bet_result.split("\n"):
                rendered = hud_font.render(line, True, BET_RESULT_COLOR)
                screen.blit(rendered, rendered.get_rect(midtop=(self.width // 2, y)))
                y += rendered.get_height() + 6

        status_x = 24 + max(total.get_width(), best_width) + 40
        status_width = self.width - status_x - 24
        y = 22
        for line in self._status_lines():
            rendered = status_font.render(
                self._truncate(line, status_font, status_width), True, STATUS_COLOR
            )
            screen.blit(rendered, (status_x, y))
            y += rendered.get_height() + 4

    def _draw_controls(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the bottom control hints: highlighted keys with spaced labels."""
        bar_top = self.height - BOTTOM_BAR_HEIGHT
        pygame.draw.rect(screen, HUD_COLOR, (0, bar_top, self.width, BOTTOM_BAR_HEIGHT))
        pygame.draw.line(screen, HUD_LINE_COLOR, (0, bar_top), (self.width, bar_top), 2)
        cy = bar_top + BOTTOM_BAR_HEIGHT // 2

        items = []
        for key, label in self.controls:
            key_surf = font.render(key, True, KEY_COLOR)
            label_surf = font.render(label, True, CONTROL_LABEL_COLOR)
            items.append(
                (key_surf, label_surf, key_surf.get_width() + 7 + label_surf.get_width())
            )
        total = sum(w for _, _, w in items) + CONTROL_GAP * (len(items) - 1)
        x = (self.width - total) // 2
        for key_surf, label_surf, width in items:
            screen.blit(key_surf, key_surf.get_rect(midleft=(x, cy)))
            screen.blit(
                label_surf,
                label_surf.get_rect(midleft=(x + key_surf.get_width() + 7, cy)),
            )
            x += width + CONTROL_GAP

    def _status_lines(self) -> list[str]:
        """Return the HUD status: expected times, the winning train (from ->
        to), the actual wait, and the ride's travel time while it is on its
        way, with dots animating on the last line while loading. Pre-turn and
        terminal states fall back to the latest messages."""
        if self.game_over:
            return self.messages[-3:]
        latest = self.messages[-1] if self.messages else ""
        terminal = any(
            key in latest for key in ("reached the end", "No current save", "Quitting")
        )
        if not self.messages or terminal:
            lines = self.messages[-2:]
        else:
            lines = []
            expected = self._latest_message("Expected wait times")
            if expected is not None:
                lines.append(expected)
            if self.last_train is not None:
                lines.append(
                    f"First train:  {self.last_train[0]}  ->  {self.last_train[1]}"
                )
            waits = self._latest_message("Wait times")
            if waits is not None:
                lines.append(waits)
            travelling = self._latest_message("Travelling to")
            if travelling is not None and self.incoming_train is not None:
                lines.append(travelling)
            if not lines:
                lines = self.messages[-2:]
        if self.loading and lines:
            dots = "." * (pygame.time.get_ticks() // 300 % 5 + 1)
            lines = lines[:-1] + [lines[-1] + dots]
        return lines

    def _latest_message(self, prefix: str) -> str | None:
        """Return the most recent message starting with <prefix>, or None."""
        for message in reversed(self.messages):
            if message.startswith(prefix):
                return message
        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the rail map and the HUD onto <screen>."""
        label_font = pygame.font.SysFont(None, 22)
        sub_font = pygame.font.SysFont(None, 16)
        hud_font = pygame.font.SysFont(None, 24)
        status_font = pygame.font.SysFont(None, 22)
        control_font = pygame.font.SysFont(None, 24)

        screen.fill(BG_COLOR)
        self._draw_tracks(screen)
        self._draw_stations(screen, label_font, sub_font)
        self._draw_train(screen, sub_font)
        self._draw_hud(screen, hud_font, status_font)
        if self.show_controls:
            self._draw_controls(screen, control_font)


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
