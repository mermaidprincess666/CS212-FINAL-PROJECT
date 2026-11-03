"""Initialize Pygame and run the shared game loop."""

import pygame

from core.asset_loader import AssetLoader
from core.scene_manager import SceneManager
from settings import (
    BUTTON_FONT_SIZE,
    DIALOGUE_FONT_SIZE,
    FPS,
    GAME_TITLE,
    HEIGHT,
    LABEL_FONT_SIZE,
    NAME_FONT_SIZE,
    SCREEN_FADE_COLOR,
    SMALL_FONT_SIZE,
    TITLE_FONT_SIZE,
    WIDTH,
)


class Game:
    """Own the window, shared assets, clock, and scene manager."""

    def __init__(self):
        pygame.init()
        # SCALED keeps 1200x675 a logical size that stretches to the window,
        # so every layout constant in settings.py stays valid on any display.
        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT), pygame.SCALED, vsync=1
        )
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.delta_time = 1 / FPS

        # One shared full-screen haze, reused by the gate's cover and by the
        # story reveal. Whoever draws it sets the alpha for that frame.
        self.warm_surface = pygame.Surface((WIDTH, HEIGHT))
        self.warm_surface.fill(SCREEN_FADE_COLOR)
        # Built once here and looked up by role, so screens never build fonts.
        self.fonts = {
            "title": pygame.font.SysFont("georgia", TITLE_FONT_SIZE, bold=True),
            "button": pygame.font.SysFont("arial", BUTTON_FONT_SIZE),
            "label": pygame.font.SysFont("arial", LABEL_FONT_SIZE),
            "small": pygame.font.SysFont("arial", SMALL_FONT_SIZE),
            "dialogue": pygame.font.SysFont("arial", DIALOGUE_FONT_SIZE),
            "name": pygame.font.SysFont("arial", NAME_FONT_SIZE, bold=True),
        }
        self.assets = AssetLoader()
        self.scene_manager = SceneManager(self)

    def run(self):
        """Run events, updates, and drawing until the player exits."""
        try:
            while self.running:
                mouse_pos = pygame.mouse.get_pos()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    else:
                        self.scene_manager.handle_event(event)

                self.scene_manager.update(self.delta_time)
                self.scene_manager.draw(self.screen, mouse_pos)
                pygame.display.flip()

                # Blend frame times so one slow frame does not jerk the gate animation.
                raw_delta = min(self.clock.tick(FPS) / 1000, 0.05)
                self.delta_time = self.delta_time * 0.8 + raw_delta * 0.2
        finally:
            pygame.quit()