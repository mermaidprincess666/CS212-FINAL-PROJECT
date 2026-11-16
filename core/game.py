"""Initialize Pygame and run the shared game loop."""

import pygame

from core.audio import MenuMusic
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
    WINDOWED_HEIGHT,
    WINDOWED_WIDTH,
)


class Game:
    """Own the window, shared assets, clock, and scene manager."""

    def __init__(self):
        pygame.init()
        self.fullscreen = False

        # Scenes always draw at the original game resolution.
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        self._set_display_mode()
        pygame.display.set_caption(GAME_TITLE)

        self.clock = pygame.time.Clock()
        self.running = True
        self.delta_time = 1 / FPS

        # Shared by the gate cover and story reveal.
        self.warm_surface = pygame.Surface((WIDTH, HEIGHT))
        self.warm_surface.fill(SCREEN_FADE_COLOR)
        self.fonts = {
            "title": pygame.font.SysFont(
                "comicsansms", TITLE_FONT_SIZE, bold=True
            ),
            "button": pygame.font.SysFont("trebuchetms", BUTTON_FONT_SIZE),
            "label": pygame.font.SysFont("trebuchetms", LABEL_FONT_SIZE),
            "small": pygame.font.SysFont("trebuchetms", SMALL_FONT_SIZE),
            "dialogue": pygame.font.SysFont("trebuchetms", DIALOGUE_FONT_SIZE),
            "name": pygame.font.SysFont("trebuchetms", NAME_FONT_SIZE, bold=True),
        }

        self.assets = AssetLoader()
        self.menu_music = MenuMusic()
        self.scene_manager = SceneManager(self)

    def toggle_fullscreen(self):
        """Switch display modes while keeping the game's logical canvas."""
        self.fullscreen = not self.fullscreen
        self._set_display_mode()

    def _set_display_mode(self):
        if self.fullscreen:
            self.display = pygame.display.set_mode(
                (WIDTH, HEIGHT), pygame.FULLSCREEN
            )
        else:
            self.display = pygame.display.set_mode(
                (WINDOWED_WIDTH, WINDOWED_HEIGHT)
            )

        display_width, display_height = self.display.get_size()

        # One scale factor fits both dimensions without stretching the game.
        scale = min(display_width / WIDTH, display_height / HEIGHT)
        viewport_width = max(1, round(WIDTH * scale))
        viewport_height = max(1, round(HEIGHT * scale))

        self._viewport = pygame.Rect(0, 0, viewport_width, viewport_height)
        self._viewport.center = self.display.get_rect().center

    def _to_logical_pos(self, position):
        """Convert a mouse position to coordinates on the game canvas."""
        if not self._viewport.collidepoint(position):
            return None

        x = position[0] - self._viewport.left
        y = position[1] - self._viewport.top
        return (
            x * WIDTH // self._viewport.width,
            y * HEIGHT // self._viewport.height,
        )

    def run(self):
        """Run events, updates, and drawing until the player exits."""
        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        continue

                    if event.type in (
                        pygame.MOUSEBUTTONDOWN,
                        pygame.MOUSEBUTTONUP,
                        pygame.MOUSEMOTION,
                    ):
                        logical_pos = self._to_logical_pos(event.pos)
                        if logical_pos is None:
                            if event.type != pygame.MOUSEMOTION:
                                continue
                            logical_pos = (-1, -1)

                        event = pygame.event.Event(
                            event.type, {**event.dict, "pos": logical_pos}
                        )

                    self.scene_manager.handle_event(event)

                mouse_pos = self._to_logical_pos(pygame.mouse.get_pos())
                if mouse_pos is None:
                    mouse_pos = (-1, -1)

                self.scene_manager.update(self.delta_time)
                self.scene_manager.draw(self.screen, mouse_pos)

                if self._viewport.size == self.screen.get_size():
                    frame = self.screen
                else:
                    frame = pygame.transform.smoothscale(
                        self.screen, self._viewport.size
                    )

                self.display.fill((0, 0, 0))
                self.display.blit(frame, self._viewport.topleft)
                pygame.display.flip()

                # Smooth delta time to reduce jumps after slow frames.
                raw_delta = min(self.clock.tick(FPS) / 1000, 0.05)
                self.delta_time = self.delta_time * 0.8 + raw_delta * 0.2
        finally:
            pygame.quit()