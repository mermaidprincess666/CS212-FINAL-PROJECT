
"""Shared in-game day and clock for SLICE gameplay scenes."""

import pygame

from settings import ASSETS_DIR, ui


OPEN_HOUR = 10
CLOSE_HOUR = 20
SECONDS_PER_GAME_HOUR = 30

CREAM = (247, 233, 209)
BROWN = (123, 86, 66)


class ShopClock:
    """One clock shared by the counter, kitchen and oven."""

    def __init__(self, game):
        self.day = 1
        self.started = False
        self.elapsed_seconds = 0.0

        self.day_font = self._load_font(
            ui(20), game.fonts.get("label")
        )
        self.time_font = self._load_font(
            ui(30), game.fonts.get("dialogue")
        )

    def _load_font(self, size, fallback):
        path = (
            ASSETS_DIR
            / "FONTS"
            / "Fredoka/static/Fredoka-SemiBold.ttf"
        )

        try:
            return pygame.font.Font(str(path), size)
        except (OSError, pygame.error):
            return fallback or pygame.font.Font(None, size)

    def start(self):
        """Start Day 1 after the welcome tutorial."""
        if not self.started:
            self.started = True
            self.elapsed_seconds = 0.0

    def update(self, delta_time):
        """Keep time progressing across gameplay screens."""
        if self.started:
            total_seconds = (
                (CLOSE_HOUR - OPEN_HOUR)
                * SECONDS_PER_GAME_HOUR
            )

            self.elapsed_seconds = min(
                total_seconds,
                self.elapsed_seconds + max(0.0, delta_time),
            )

    def time_text(self):
        """Convert elapsed real time into in-game time."""
        game_minutes = int(
            self.elapsed_seconds
            * 60
            / SECONDS_PER_GAME_HOUR
        )

        total_minutes = min(
            CLOSE_HOUR * 60,
            OPEN_HOUR * 60 + game_minutes,
        )

        hour_24, minutes = divmod(total_minutes, 60)
        hour_12 = hour_24 % 12 or 12
        am_pm = "AM" if hour_24 < 12 else "PM"

        return f"{hour_12}:{minutes:02d} {am_pm}"

    def draw(self, target, highlighted=False):
        """Draw the clock at the top-left corner."""
        panel = pygame.Rect(
            ui(24), ui(24), ui(190), ui(88)
        )

        # Highlight when the chef explains the clock
        if highlighted:
            pygame.draw.rect(
                target,
                (249, 207, 113),
                panel.inflate(ui(10), ui(10)),
                border_radius=ui(17),
            )

        pygame.draw.rect(
            target,
            (110, 74, 58),
            panel.move(0, ui(4)),
            border_radius=ui(14),
        )

        pygame.draw.rect(
            target,
            CREAM,
            panel,
            border_radius=ui(14),
        )

        pygame.draw.rect(
            target,
            BROWN,
            panel,
            ui(3),
            border_radius=ui(14),
        )

        day_image = self.day_font.render(
            f"Day {self.day}", True, BROWN
        )

        time_image = self.time_font.render(
            self.time_text(), True, BROWN
        )

        target.blit(
            day_image,
            (panel.x + ui(16), panel.y + ui(9)),
        )

        target.blit(
            time_image,
            (panel.x + ui(16), panel.y + ui(38)),
        )
