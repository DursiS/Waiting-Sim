import pygame

from App.ViewModelFacade import ViewModelFacade


MENU_WIDTH = 500
MENU_HEIGHT = 200
BG_COLOR = (24, 24, 28)
TEXT_COLOR = (255, 255, 255)


class ViewFacade:
    """Manage the main menu model and transition between feature
    view models."""

    view_model_facade: ViewModelFacade
    _busy: bool
    _running: bool
    _key_observers: dict

    def __init__(self, view_model_facade: ViewModelFacade) -> None:
        self.view_model_facade = view_model_facade
        self._busy = False
        self._running = True
        self._key_observers = {
            pygame.K_q: self.on_quit,
            pygame.K_g: self.on_game,
            pygame.K_s: self.on_simulation,
        }

        pygame.init()
        self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        pygame.display.set_caption("Waiting Sim")
        self.keydown_loop()
        pygame.quit()

    def keydown_loop(self) -> None:
        """Listen for keypresses, notify the bound observer, and redraw."""
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    observer = self._key_observers.get(event.key)
                    if observer is not None:
                        observer()

            self._draw()
            pygame.display.flip()

    def _draw(self) -> None:
        """Draw whichever mode is active, or the default menu."""
        game_view_model = self.view_model_facade.game_view_model
        simulation_view_model = self.view_model_facade.simulation_view_model

        if game_view_model._running:
            self._screen = pygame.display.set_mode(
                (game_view_model.width, game_view_model.height)
            )
            game_view_model.draw(self._screen)
        elif simulation_view_model._running:
            self._screen = pygame.display.set_mode(
                (simulation_view_model.width, simulation_view_model.height)
            )
            simulation_view_model.draw(self._screen)
        else:
            self._screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
            self._draw_menu()

    def _draw_menu(self) -> None:
        """Draw the default Game/Simulation/Quit menu."""
        self._screen.fill(BG_COLOR)
        font = pygame.font.SysFont(None, 28)
        text = font.render(
            "Press G for Game  |  Press S for Simulation  |  Press Q to Quit",
            True,
            TEXT_COLOR,
        )
        self._screen.blit(text, text.get_rect(center=self._screen.get_rect().center))

    def on_quit(self) -> None:
        """Action Listener to quit"""
        if self._busy:
            return
        self._busy = True
        try:
            self._running = False
        finally:
            self._busy = False

    def on_game(self) -> None:
        """Action Listener to start game mode"""
        if self._busy:
            return
        self._busy = True
        try:
            self.view_model_facade.start_game()
        finally:
            self._busy = False

    def on_simulation(self) -> None:
        """Action Listener to start simulation mode"""
        if self._busy:
            return
        self._busy = True
        try:
            self.view_model_facade.start_simulation()
        finally:
            self._busy = False
