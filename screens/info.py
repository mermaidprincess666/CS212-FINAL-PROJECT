"""Plain information pages, built from a heading and a list of lines."""

import pygame

from screens.common import draw_button, draw_text_center
from settings import (
    BACKGROUND,
    HEIGHT,
    TITLE_COLOR,
    WIDTH,
)


class InfoScene:
    """A heading, a few centered lines, and a Back button.

    One class covers the Continue, Settings and About pages: each is built
    with its own text, and ``back_target`` says where Back leads.
    """

    def __init__(self, game, heading, lines, back_target="menu"):
        self.game = game
        self.heading = heading
        self.lines = lines
        self.back_target = back_target
        self.title_font = game.fonts["title"]
        self.body_font = game.fonts["button"]
        self.button_font = game.fonts["small"]
        self.back_button = pygame.Rect(40, HEIGHT - 60, 140, 40)

    def handle_event(self, event):
        """Send Back to this page's configured ``back_target``."""
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.back_button.collidepoint(event.pos)
        ):
            self.game.scene_manager.go_to(self.back_target)

    def update(self, delta_time):
        """Information pages are static and need no updates."""

    def draw(self, target, mouse_pos):
        """Draw the heading, centered information lines, and Back button."""
        target.fill(BACKGROUND)
        draw_text_center(
            target,
            self.heading,
            self.title_font,
            TITLE_COLOR,
            (WIDTH // 2, 100),
        )
        for line_index, line in enumerate(self.lines):
            draw_text_center(
                target,
                line,
                self.body_font,
                TITLE_COLOR,
                (WIDTH // 2, 200 + line_index * 40),
            )
        draw_button(target, self.back_button, "BACK", mouse_pos, self.button_font)