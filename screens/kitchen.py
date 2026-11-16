
"""Kitchen gameplay scene for SLICE."""

import pygame

from settings import ASSETS_DIR, WIDTH, HEIGHT, ui


CREAM = (247, 233, 209)
PAPER = (255, 247, 232)
BROWN = (123, 86, 66)
DARK = (63, 43, 35)


class KitchenScene:
    """Display the kitchen where players prepare pizzas."""

    def __init__(self, game):
        self.game = game
        self.background = None

        self.guide_font = self._load_font()

        self._load_background()

    def _load_font(self):
        """Load the font used for the keyboard guide."""
        try:
            return pygame.font.Font(
                str(
                    ASSETS_DIR
                    / "FONTS"
                    / "Fredoka"
                    / "static"
                    / "Fredoka-SemiBold.ttf"
                ),
                ui(16),
            )
        except (OSError, pygame.error):
            return self.game.fonts["small"]

    def _load_background(self):
        """Load the kitchen background."""
        try:
            path = ASSETS_DIR / "KITCHEN" / "kitchen.png"

            image = pygame.image.load(
                str(path)
            ).convert()

            # Scale without stretching the image.
            scale = max(
                WIDTH / image.get_width(),
                HEIGHT / image.get_height()
            )

            new_width = round(image.get_width() * scale)
            new_height = round(image.get_height() * scale)

            self.background = pygame.transform.smoothscale(
                image,
                (new_width, new_height)
            )

        except (OSError, pygame.error) as error:
            print(f"Kitchen background unavailable: {error}")

    def _go_to_scene(self, scene_name):
        """Switch to another registered scene."""
        scenes = self.game.scene_manager.scenes

        if scene_name not in scenes:
            print(
                f"Scene '{scene_name}' is not implemented "
                "or registered yet."
            )
            return

        self.game.scene_manager.go_to(scene_name)

    def handle_event(self, event):
        """Handle keyboard navigation."""
        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_a:
                self._go_to_scene("oven")

            elif event.key == pygame.K_d:
                self._go_to_scene("welcome")

    def update(self, delta_time):
        """Update kitchen gameplay."""
        pass

    def draw(self, target, mouse_pos):
        """Draw the kitchen and keyboard guide."""
        target.fill(CREAM)

        # Kitchen background
        if self.background is not None:
            x = (WIDTH - self.background.get_width()) // 2
            y = (HEIGHT - self.background.get_height()) // 2

            target.blit(self.background, (x, y))

        # Bottom-right keyboard controls
        self._draw_controls(target)

    def _draw_controls(self, target):
        """Draw navigation guide at bottom-right."""

        y = HEIGHT - ui(47)
        right = WIDTH - ui(30)

        items = [
            ("A", "Oven"),
            ("D", "Cashier"),
        ]

        total_width = ui(270)
        x = right - total_width

        for index, (key, label) in enumerate(items):
            key_rect = pygame.Rect(
                x,
                y,
                ui(34),
                ui(28),
            )

            # Key background
            pygame.draw.rect(
                target,
                PAPER,
                key_rect,
                border_radius=ui(6),
            )

            # Key border
            pygame.draw.rect(
                target,
                BROWN,
                key_rect,
                ui(2),
                border_radius=ui(6),
            )

            # Key letter
            key_image = self.guide_font.render(
                key,
                True,
                BROWN,
            )

            target.blit(
                key_image,
                key_image.get_rect(
                    center=key_rect.center
                ),
            )

            # Destination label
            label_image = self.guide_font.render(
                label,
                True,
                PAPER,
            )

            target.blit(
                label_image,
                (
                    key_rect.right + ui(8),
                    key_rect.centery
                    - label_image.get_height() // 2,
                ),
            )

            x += ui(130)

            # Separator
            if index == 0:
                separator_x = x - ui(12)

                pygame.draw.line(
                    target,
                    BROWN,
                    (separator_x, y),
                    (separator_x, y + ui(28)),
                    ui(2),
                )
