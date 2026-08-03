import pygame


WIDTH = 760
HEIGHT = 520
MARGIN = 40
LINE_HEIGHT = 26
BG_COLOR = (16, 18, 24)
TITLE_COLOR = (240, 210, 110)
PROMPT_COLOR = (150, 215, 235)
INPUT_COLOR = (255, 255, 255)
MESSAGE_COLOR = (206, 212, 224)


class GambleViewModel:
    """The gamble screen's state: the question currently being asked and a
    running block of feedback and result messages, drawn for the player."""

    prompt: str
    messages: list[str]
    width: int
    height: int

    def __init__(self) -> None:
        """Create an empty gamble view model."""
        self.prompt = ""
        self.messages = []
        self.width = WIDTH
        self.height = HEIGHT

    def set_prompt(self, prompt: str) -> None:
        """Set the question the View should display and read an answer for."""
        self.prompt = prompt

    def clear_messages(self) -> None:
        """Empty the running message block."""
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add <message> to the running message block."""
        self.messages.append(message)

    def draw(self, screen: pygame.Surface, typed: str) -> None:
        """Draw the title, message block, current question and <typed> answer."""
        screen.fill(BG_COLOR)
        title_font = pygame.font.SysFont("consolas", 34, bold=True)
        prompt_font = pygame.font.SysFont(None, 28)
        message_font = pygame.font.SysFont(None, 24)

        title = title_font.render("Waiting-Sim -- Gamble", True, TITLE_COLOR)
        screen.blit(title, (MARGIN, MARGIN))

        y = MARGIN + 60
        for message in self.messages[-10:]:
            rendered = message_font.render(message, True, MESSAGE_COLOR)
            screen.blit(rendered, (MARGIN, y))
            y += LINE_HEIGHT

        if self.prompt:
            question = prompt_font.render(self.prompt, True, PROMPT_COLOR)
            screen.blit(question, (MARGIN, self.height - MARGIN - LINE_HEIGHT * 2))
            answer = prompt_font.render(f"> {typed}_", True, INPUT_COLOR)
            screen.blit(answer, (MARGIN, self.height - MARGIN - LINE_HEIGHT))
