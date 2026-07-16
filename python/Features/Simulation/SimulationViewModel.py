import pygame


BG_COLOR = (24, 24, 28)
TEXT_COLOR = (255, 255, 255)
MESSAGE_COLOR = (220, 220, 220)


class SimulationViewModel:
    """A placeholder view for simulation mode."""

    messages: list[str]
    width: int
    height: int
    _running: bool

    def __init__(self, messages: list[str] = None) -> None:
        """Create a SimulationViewModel holding <messages> to display."""
        self.messages = messages or []
        self._running = False
        self.width = 500
        self.height = 300

    def draw(self, screen: pygame.Surface) -> None:
        """Draw a placeholder simulation screen along with any messages."""
        screen.fill(BG_COLOR)
        font = pygame.font.SysFont(None, 28)
        text = font.render("Simulation mode coming soon...", True, TEXT_COLOR)
        screen.blit(text, text.get_rect(center=(self.width // 2, 40)))

        message_font = pygame.font.SysFont(None, 22)
        y = 90
        for message in self.messages:
            rendered = message_font.render(message, True, MESSAGE_COLOR)
            screen.blit(rendered, (20, y))
            y += rendered.get_height() + 4
