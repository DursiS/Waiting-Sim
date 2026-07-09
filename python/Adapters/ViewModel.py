import pygame

from Entities import Station


CELL_SIZE = 120
PADDING = 40
PROMPT_HEIGHT = 80
BG_COLOR = (24, 24, 28)
CELL_COLOR = (70, 130, 180)
TEXT_COLOR = (255, 255, 255)
PROMPT_COLOR = (200, 200, 60)


class ViewModel:
    """A pygame rendering of the world grid and startup prompts."""

    stations: list[Station]
    width: int
    height: int

    def __init__(self, stations: list[Station], curr_station: Station) -> None:
        """Create a ViewModel for <stations>."""
        self.stations = stations
        x_m = max((s.coordinates[0] for s in stations), default=0)
        y_m = max((s.coordinates[1] for s in stations), default=0)
        self.width = (x_m + 1) * CELL_SIZE + PADDING * 2
        self.height = (y_m + 1) * CELL_SIZE + PADDING * 2 + PROMPT_HEIGHT

    def draw_grid(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw every station at its grid coordinates."""
        for station in self.stations:
            x, y = station.coordinates
            rect = pygame.Rect(
                PADDING + x * CELL_SIZE,
                PADDING + y * CELL_SIZE,
                CELL_SIZE - 10,
                CELL_SIZE - 10,
            )
            pygame.draw.rect(screen, CELL_COLOR, rect)
            label = font.render(station.name, True, TEXT_COLOR)
            screen.blit(label, label.get_rect(center=rect.center))

    def draw_prompts(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the startup text prompts."""
        prompt = font.render("Press P to Play  |  Press Q to Quit", True, PROMPT_COLOR)
        screen.blit(prompt, (PADDING, self.height - PROMPT_HEIGHT // 2))

    def run(self) -> None:
        """Open a window and show the world grid until closed."""
        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Waiting Sim")
        font = pygame.font.SysFont(None, 24)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            screen.fill(BG_COLOR)
            self.draw_grid(screen, font)
            self.draw_prompts(screen, font)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    from Framework.Database import DEFAULT_STATIONS

    demo_stations = []
    for station_id, record in DEFAULT_STATIONS.items():
        station = Station(
            name=record["name"],
            rule_name=record["rule_name"],
            rule=record["rule"],
            times_visited=record["times_visited"],
            waited_at=record["waited_at"],
            N=record["N"],
            S=record["S"],
            E=record["E"],
            W=record["W"],
            coordinates=record["coordinates"],
        )
        station.set_id(station_id)
        demo_stations.append(station)

    ViewModel(demo_stations).run()
