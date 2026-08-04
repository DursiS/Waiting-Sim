import pygame


WIDTH = 760
HEIGHT = 520
MARGIN = 40
LINE_HEIGHT = 26
PROB_BOX = pygame.Rect(WIDTH - 260, 70, 220, 92)

BG_COLOR = (16, 18, 24)
TITLE_COLOR = (240, 210, 110)
BALANCE_COLOR = (150, 235, 170)
PROMPT_COLOR = (150, 215, 235)
INPUT_BG_COLOR = (10, 12, 16)
INPUT_BORDER_COLOR = (70, 120, 170)
INPUT_COLOR = (255, 255, 255)
MESSAGE_COLOR = (206, 212, 224)
BOX_BG_COLOR = (28, 31, 40)
BOX_BORDER_COLOR = (58, 63, 78)
BOX_LABEL_COLOR = (150, 162, 178)
BOX_VALUE_COLOR = (250, 220, 130)


class GambleViewModel:
    """The gamble screen's betting state: the player's balance, the odds box
    for the bet being defined, the question currently being asked, and a
    running block of feedback messages. When betting ends the phase flips to
    'game' and the View renders the automatic game view model instead."""

    prompt: str
    messages: list[str]
    balance: float
    probability: str
    phase: str
    width: int
    height: int

    def __init__(self) -> None:
        """Create an empty gamble view model in the betting phase."""
        self.prompt = ""
        self.messages = []
        self.balance = 0.0
        self.probability = ""
        self.phase = "betting"
        self.width = WIDTH
        self.height = HEIGHT

    def set_prompt(self, prompt: str) -> None:
        """Set the question the View should display and read an answer for."""
        self.prompt = prompt

    def set_balance(self, balance: float) -> None:
        """Set the player's balance shown in the top-left corner."""
        self.balance = balance

    def set_probability(self, probability: str) -> None:
        """Set the text shown in the odds box, or '' to clear it."""
        self.probability = probability

    def set_phase(self, phase: str) -> None:
        """Set the screen phase: 'betting' or 'game'."""
        self.phase = phase

    def clear_messages(self) -> None:
        """Empty the running message block."""
        self.messages = []

    def add_message(self, message: str) -> None:
        """Add <message> to the running message block."""
        self.messages.append(message)

    def draw(self, screen: pygame.Surface, typed: str) -> None:
        """Draw the balance, odds box, message block, current question and the
        <typed> answer for the betting phase."""
        screen.fill(BG_COLOR)
        title_font = pygame.font.SysFont("consolas", 30, bold=True)
        balance_font = pygame.font.SysFont(None, 30)
        prompt_font = pygame.font.SysFont(None, 28)
        message_font = pygame.font.SysFont(None, 24)
        box_font = pygame.font.SysFont(None, 22)
        value_font = pygame.font.SysFont(None, 34, bold=True)

        balance = balance_font.render(f"Balance: {self.balance:.2f}", True, BALANCE_COLOR)
        screen.blit(balance, (MARGIN, 24))
        title = title_font.render("Gamble", True, TITLE_COLOR)
        screen.blit(title, title.get_rect(midtop=(self.width // 2, 22)))

        self._draw_probability_box(screen, box_font, value_font)

        y = 120
        for message in self.messages[-9:]:
            rendered = message_font.render(message, True, MESSAGE_COLOR)
            screen.blit(rendered, (MARGIN, y))
            y += LINE_HEIGHT

        if self.prompt:
            self._draw_prompt(screen, prompt_font, typed)

    def _draw_probability_box(
        self,
        screen: pygame.Surface,
        label_font: pygame.font.Font,
        value_font: pygame.font.Font,
    ) -> None:
        """Draw the odds box communicating the current bet's win probability."""
        pygame.draw.rect(screen, BOX_BG_COLOR, PROB_BOX, border_radius=8)
        pygame.draw.rect(screen, BOX_BORDER_COLOR, PROB_BOX, width=1, border_radius=8)
        label = label_font.render("Chance to win", True, BOX_LABEL_COLOR)
        screen.blit(label, label.get_rect(midtop=(PROB_BOX.centerx, PROB_BOX.top + 10)))
        value = value_font.render(self.probability or "--", True, BOX_VALUE_COLOR)
        screen.blit(value, value.get_rect(center=(PROB_BOX.centerx, PROB_BOX.centery + 12)))

    def _draw_prompt(
        self, screen: pygame.Surface, font: pygame.font.Font, typed: str
    ) -> None:
        """Draw the current question and an input box holding the typed answer."""
        question = font.render(self.prompt, True, PROMPT_COLOR)
        screen.blit(question, (MARGIN, self.height - MARGIN - LINE_HEIGHT * 2 - 8))
        box = pygame.Rect(MARGIN, self.height - MARGIN - LINE_HEIGHT - 6,
                          self.width - MARGIN * 2, LINE_HEIGHT + 8)
        pygame.draw.rect(screen, INPUT_BG_COLOR, box, border_radius=4)
        pygame.draw.rect(screen, INPUT_BORDER_COLOR, box, width=1, border_radius=4)
        answer = font.render(f"{typed}_", True, INPUT_COLOR)
        screen.blit(answer, answer.get_rect(midleft=(box.left + 10, box.centery)))
